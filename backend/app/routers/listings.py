"""Public catalogue: browse and view approved listings; buyer shortlist."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.deps import get_current_user
from app.models import ApprovalStatus, Listing, ListingStatus, PropertyType, Role, Shortlist, User
from app.routers.common import to_card, to_detail
from app.schemas import Facets, ListingCard, ListingDetail, ListingPage

router = APIRouter(prefix="/api", tags=["listings"])

_VISIBLE = (Listing.approval_status == ApprovalStatus.approved,)


@router.get("/listings", response_model=ListingPage)
def browse(
    q: str | None = Query(default=None, max_length=100),
    locality: list[str] = Query(default=[]),
    property_type: PropertyType | None = None,
    bedrooms: int | None = Query(default=None, ge=0, le=10),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    has_parking: bool | None = None,
    near_metro: bool | None = None,
    near_school: bool | None = None,
    include_sold: bool = False,
    sort: Literal["newest", "price_asc", "price_desc"] = "newest",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=48),
    db: Session = Depends(get_db),
) -> ListingPage:
    conds = list(_VISIBLE)
    if not include_sold:
        conds.append(Listing.status == ListingStatus.available)
    if q:
        like = f"%{q.strip()}%"
        conds.append(
            Listing.title.ilike(like) | Listing.locality.ilike(like) | Listing.ref_code.ilike(like)
        )
    if locality:
        conds.append(Listing.locality.in_(locality))
    if property_type:
        conds.append(Listing.property_type == property_type)
    if bedrooms is not None:
        conds.append(Listing.bedrooms >= bedrooms if bedrooms >= 4 else Listing.bedrooms == bedrooms)
    if price_min is not None:
        conds.append(Listing.price_inr >= price_min)
    if price_max is not None:
        conds.append(Listing.price_inr <= price_max)
    for flag, col in ((has_parking, Listing.has_parking), (near_metro, Listing.near_metro),
                      (near_school, Listing.near_school)):
        if flag:
            conds.append(col.is_(True))

    order = {
        "newest": Listing.created_at.desc(),
        "price_asc": Listing.price_inr.asc(),
        "price_desc": Listing.price_inr.desc(),
    }[sort]
    total = db.scalar(select(func.count()).select_from(Listing).where(*conds)) or 0
    rows = db.scalars(
        select(Listing)
        .where(*conds)
        .options(selectinload(Listing.images))
        .order_by(order, Listing.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return ListingPage(items=[to_card(r) for r in rows], total=total, page=page, page_size=page_size)


@router.get("/listings/facets", response_model=Facets)
def facets(db: Session = Depends(get_db)) -> Facets:
    locs = db.scalars(select(Listing.locality).where(*_VISIBLE).distinct().order_by(Listing.locality))
    lo, hi = db.execute(select(func.min(Listing.price_inr), func.max(Listing.price_inr)).where(*_VISIBLE)).one()
    return Facets(
        localities=list(locs),
        property_types=[p.value for p in PropertyType],
        price_min=lo or 0,
        price_max=hi or 0,
    )


@router.get("/listings/{listing_id}", response_model=ListingDetail)
def detail(listing_id: int, db: Session = Depends(get_db)) -> ListingDetail:
    listing = db.scalar(
        select(Listing)
        .where(Listing.id == listing_id, *_VISIBLE)
        .options(selectinload(Listing.images), selectinload(Listing.owner))
    )
    if listing is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return to_detail(listing)


# --------------------------------------------------------------------------- shortlist
@router.get("/me/shortlist", response_model=list[ListingCard])
def my_shortlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ListingCard]:
    rows = db.scalars(
        select(Listing)
        .join(Shortlist, Shortlist.listing_id == Listing.id)
        .where(Shortlist.user_id == user.id)
        .options(selectinload(Listing.images))
        .order_by(Shortlist.created_at.desc())
    ).all()
    return [to_card(r) for r in rows]


@router.put("/me/shortlist/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def add_to_shortlist(listing_id: int, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)) -> None:
    if user.role != Role.buyer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only buyers can shortlist properties")
    if db.scalar(select(Listing.id).where(Listing.id == listing_id, *_VISIBLE)) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    if db.get(Shortlist, (user.id, listing_id)) is None:
        db.add(Shortlist(user_id=user.id, listing_id=listing_id))
        db.commit()


@router.delete("/me/shortlist/{listing_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
def remove_from_shortlist(listing_id: int, user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> None:
    row = db.get(Shortlist, (user.id, listing_id))
    if row is not None:
        db.delete(row)
        db.commit()
