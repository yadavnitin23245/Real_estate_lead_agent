"""Sales workspace: lead inbox, lead detail, status / notes / assignment, site visits.

Sales agents see the leads assigned to them; admins see every lead.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import require_roles
from app.models import (
    Lead,
    LeadMatch,
    LeadScore,
    LeadStatus,
    Listing,
    Message,
    Role,
    User,
    VisitRequest,
)
from app.routers.common import to_card
from app.schemas import LeadDetail, LeadPatch, LeadRow, MatchOut, MessageOut, VisitOut, VisitPatch

router = APIRouter(prefix="/api/leads", tags=["leads"])
staff = require_roles(Role.sales_agent, Role.admin)


def _scope(user: User):
    return [] if user.role == Role.admin else [Lead.assigned_agent_id == user.id]


def _get(db: Session, user: User, lead_id: int) -> Lead:
    lead = db.scalar(
        select(Lead).where(Lead.id == lead_id, *_scope(user)).options(selectinload(Lead.assigned_agent))
    )
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Lead not found")
    return lead


@router.get("", response_model=list[LeadRow])
def inbox(
    score: LeadScore | None = None,
    lead_status: LeadStatus | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, max_length=100),
    unassigned: bool = False,
    user: User = Depends(staff),
    db: Session = Depends(get_db),
) -> list[Lead]:
    conds = _scope(user)
    if score:
        conds.append(Lead.score == score)
    if lead_status:
        conds.append(Lead.status == lead_status)
    if unassigned:
        conds.append(Lead.assigned_agent_id.is_(None))
    if q:
        like = f"%{q.strip()}%"
        conds.append(or_(Lead.name.ilike(like), Lead.email.ilike(like), Lead.phone.ilike(like)))
    score_rank = case((Lead.score == LeadScore.hot, 0), (Lead.score == LeadScore.warm, 1), else_=2)
    return list(
        db.scalars(
            select(Lead)
            .where(*conds)
            .options(selectinload(Lead.assigned_agent))
            .order_by(score_rank, Lead.updated_at.desc())
            .limit(500)
        )
    )


@router.get("/agents", response_model=list[dict])
def agents(user: User = Depends(staff), db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(User).where(User.role == Role.sales_agent, User.is_active.is_(True)).order_by(User.name)
    )
    return [{"id": u.id, "name": u.name} for u in rows]


@router.get("/{lead_id}", response_model=LeadDetail)
def lead_detail(lead_id: int, user: User = Depends(staff), db: Session = Depends(get_db)) -> LeadDetail:
    lead = _get(db, user, lead_id)
    out = LeadDetail(
        **LeadRow.model_validate(lead).model_dump(),
        must_haves=lead.must_haves or {},
        soft_preferences=lead.soft_preferences,
        summary=lead.summary,
        notes=lead.notes,
        city=lead.city,
    )
    out.messages = [
        MessageOut(id=m.id, role=m.role.value, content=m.content, created_at=m.created_at)
        for m in db.scalars(select(Message).where(Message.lead_id == lead.id).order_by(Message.created_at, Message.id))
    ]
    matches = db.scalars(
        select(LeadMatch)
        .where(LeadMatch.lead_id == lead.id)
        .options(selectinload(LeadMatch.listing).selectinload(Listing.images))
        .order_by(LeadMatch.rank)
    )
    out.matches = [
        MatchOut(rank=m.rank, reason=m.reason, matched_filters=m.matched_filters, listing=to_card(m.listing))
        for m in matches
    ]
    visits = db.scalars(
        select(VisitRequest)
        .where(VisitRequest.lead_id == lead.id)
        .options(selectinload(VisitRequest.listing).selectinload(Listing.images))
        .order_by(VisitRequest.created_at.desc())
    )
    out.visits = [
        VisitOut(id=v.id, preferred_time=v.preferred_time, status=v.status, created_at=v.created_at,
                 listing=to_card(v.listing))
        for v in visits
    ]
    return out


@router.patch("/{lead_id}", response_model=LeadDetail)
def update_lead(lead_id: int, body: LeadPatch, user: User = Depends(staff),
                db: Session = Depends(get_db)) -> LeadDetail:
    lead = _get(db, user, lead_id)
    fields = body.model_fields_set
    if "status" in fields and body.status is not None:
        lead.status = body.status
        if body.status == LeadStatus.handed_off and lead.handed_off_at is None:
            lead.handed_off_at = datetime.now(timezone.utc)
    if "notes" in fields:
        lead.notes = body.notes
    if "assigned_agent_id" in fields:
        if user.role != Role.admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Only admins can reassign leads")
        if body.assigned_agent_id is not None:
            agent = db.get(User, body.assigned_agent_id)
            if agent is None or agent.role != Role.sales_agent:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, "Not a sales agent")
        lead.assigned_agent_id = body.assigned_agent_id
    db.commit()
    db.expire_all()
    return lead_detail(lead_id, user, db)


@router.patch("/{lead_id}/visits/{visit_id}", response_model=LeadDetail)
def update_visit(lead_id: int, visit_id: int, body: VisitPatch, user: User = Depends(staff),
                 db: Session = Depends(get_db)) -> LeadDetail:
    _get(db, user, lead_id)
    visit = db.get(VisitRequest, visit_id)
    if visit is None or visit.lead_id != lead_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Visit not found")
    visit.status = body.status
    if visit.assigned_agent_id is None and user.role == Role.sales_agent:
        visit.assigned_agent_id = user.id
    db.commit()
    db.expire_all()
    return lead_detail(lead_id, user, db)
