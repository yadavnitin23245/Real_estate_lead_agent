"""Admin console: KPIs, listing approvals, user management."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_roles
from app.embeddings import embed, listing_embedding_text
from app.models import (
    ApprovalStatus,
    Event,
    Lead,
    Listing,
    ListingStatus,
    Role,
    User,
    VisitRequest,
    VisitStatus,
)
from app.routers.common import to_detail
from app.schemas import ListingDetail, RejectIn, StaffCreateIn, UserOut, UserPatch
from app.security import hash_password

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = require_roles(Role.admin)


def _counts(db: Session, col, *where) -> dict[str, int]:
    rows = db.execute(select(col, func.count()).where(*where).group_by(col)).all()
    return {(k.value if hasattr(k, "value") else str(k)): n for k, n in rows}


@router.get("/stats")
def stats(_: User = Depends(admin_only), db: Session = Depends(get_db)) -> dict:
    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0)
    day = func.date_trunc("day", Lead.created_at)
    per_day = {d.date().isoformat(): n for d, n in db.execute(
        select(day, func.count()).where(Lead.created_at >= since).group_by(day)
    ).all()}
    series = [
        {"date": (since + timedelta(days=i)).date().isoformat(),
         "leads": per_day.get((since + timedelta(days=i)).date().isoformat(), 0)}
        for i in range(14)
    ]
    cost, tokens = db.execute(select(func.coalesce(func.sum(Event.cost), 0.0),
                                     func.coalesce(func.sum(Event.tokens), 0))).one()
    agent_load = db.execute(
        select(User.id, User.name, func.count(Lead.id))
        .outerjoin(Lead, Lead.assigned_agent_id == User.id)
        .where(User.role == Role.sales_agent)
        .group_by(User.id, User.name)
        .order_by(User.name)
    ).all()
    return {
        "users_by_role": _counts(db, User.role),
        "listings_by_approval": _counts(db, Listing.approval_status),
        "listings_live": db.scalar(select(func.count()).select_from(Listing).where(
            Listing.approval_status == ApprovalStatus.approved, Listing.status == ListingStatus.available)) or 0,
        "listings_sold": db.scalar(select(func.count()).select_from(Listing).where(
            Listing.status == ListingStatus.sold)) or 0,
        "leads_by_score": _counts(db, Lead.score),
        "leads_by_status": _counts(db, Lead.status),
        "leads_total": db.scalar(select(func.count()).select_from(Lead)) or 0,
        "leads_unassigned": db.scalar(select(func.count()).select_from(Lead).where(
            Lead.assigned_agent_id.is_(None))) or 0,
        "visits_open": db.scalar(select(func.count()).select_from(VisitRequest).where(
            VisitRequest.status.in_([VisitStatus.requested, VisitStatus.confirmed]))) or 0,
        "llm_cost_usd": round(float(cost), 4),
        "llm_tokens": int(tokens),
        "leads_per_day": series,
        "agent_load": [{"id": i, "name": n, "leads": c} for i, n, c in agent_load],
    }


# --------------------------------------------------------------------------- approvals
@router.get("/listings", response_model=list[ListingDetail])
def review_queue(
    approval: ApprovalStatus = ApprovalStatus.pending,
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[ListingDetail]:
    rows = db.scalars(
        select(Listing)
        .where(Listing.approval_status == approval)
        .options(selectinload(Listing.images), selectinload(Listing.owner))
        .order_by(Listing.updated_at.desc())
        .limit(200)
    ).all()
    return [to_detail(r) for r in rows]


def _listing(db: Session, listing_id: int) -> Listing:
    listing = db.scalar(select(Listing).where(Listing.id == listing_id)
                        .options(selectinload(Listing.images), selectinload(Listing.owner)))
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return listing


@router.post("/listings/{listing_id}/approve", response_model=ListingDetail)
def approve(listing_id: int, admin: User = Depends(admin_only), db: Session = Depends(get_db)) -> ListingDetail:
    listing = _listing(db, listing_id)
    if listing.embedding is None:
        try:
            listing.embedding = embed(listing_embedding_text(listing.title, listing.locality, listing.description))
        except Exception:  # noqa: BLE001 - approval must not fail because the model is unavailable
            log.exception("Could not embed listing %s; it will be searchable after re-seed", listing.ref_code)
    listing.approval_status = ApprovalStatus.approved
    db.add(Event(type="listing_approved", payload={"listing_id": listing.id, "by": admin.id}))
    db.commit()
    return to_detail(_listing(db, listing_id))


@router.post("/listings/{listing_id}/reject", response_model=ListingDetail)
def reject(listing_id: int, body: RejectIn, admin: User = Depends(admin_only),
           db: Session = Depends(get_db)) -> ListingDetail:
    listing = _listing(db, listing_id)
    listing.approval_status = ApprovalStatus.rejected
    db.add(Event(type="listing_rejected",
                 payload={"listing_id": listing.id, "by": admin.id, "reason": body.reason}))
    db.commit()
    return to_detail(_listing(db, listing_id))


# --------------------------------------------------------------------------- users
@router.get("/users", response_model=list[UserOut])
def users(
    role: Role | None = None,
    q: str | None = Query(default=None, max_length=100),
    _: User = Depends(admin_only),
    db: Session = Depends(get_db),
) -> list[User]:
    conds = []
    if role:
        conds.append(User.role == role)
    if q:
        like = f"%{q.strip()}%"
        conds.append(User.name.ilike(like) | User.email.ilike(like))
    return list(db.scalars(select(User).where(*conds).order_by(User.created_at.desc()).limit(500)))


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: StaffCreateIn, _: User = Depends(admin_only), db: Session = Depends(get_db)) -> User:
    email = body.email.strip().lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(name=body.name.strip(), email=email, phone=(body.phone or "").strip() or None,
                password_hash=hash_password(body.password), role=body.role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserPatch, admin: User = Depends(admin_only),
                db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if user.id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You can't change your own account here")
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.role is not None:
        user.role = body.role
    db.commit()
    db.refresh(user)
    return user
