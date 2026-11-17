"""Seller workspace: own listings, create / edit (goes to the approval queue), photos."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import get_settings
from app.db import get_db
from app.deps import require_roles
from app.images import ImageValidationError, process_image
from app.models import ApprovalStatus, Listing, ListingImage, ListingStatus, PropertyType, Role, User
from app.routers.common import to_card, to_detail
from app.schemas import ListingCard, ListingDetail, ListingIn
from app.storage import get_storage

router = APIRouter(prefix="/api/seller", tags=["seller"])
seller_only = require_roles(Role.seller, Role.admin)


def _own(db: Session, user: User, listing_id: int) -> Listing:
    listing = db.scalar(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(selectinload(Listing.images), selectinload(Listing.owner))
    )
    if listing is None or (listing.owner_id != user.id and user.role != Role.admin):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Listing not found")
    return listing


def _apply(listing: Listing, body: ListingIn) -> None:
    data = body.model_dump()
    if body.property_type == PropertyType.plot_land:
        if body.area_value is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Plot area is required")
        data["bedrooms"] = data["bathrooms"] = None
        data["furnishing"] = None
    for k, v in data.items():
        setattr(listing, k, v)


@router.get("/listings", response_model=list[ListingCard])
def my_listings(user: User = Depends(seller_only), db: Session = Depends(get_db)) -> list[ListingCard]:
    rows = db.scalars(
        select(Listing)
        .where(Listing.owner_id == user.id)
        .options(selectinload(Listing.images))
        .order_by(Listing.created_at.desc())
    ).all()
    return [to_card(r) for r in rows]


@router.get("/listings/{listing_id}", response_model=ListingDetail)
def get_listing(listing_id: int, user: User = Depends(seller_only), db: Session = Depends(get_db)) -> ListingDetail:
    return to_detail(_own(db, user, listing_id))


@router.post("/listings", response_model=ListingDetail, status_code=status.HTTP_201_CREATED)
def create_listing(body: ListingIn, user: User = Depends(seller_only), db: Session = Depends(get_db)) -> ListingDetail:
    listing = Listing(owner_id=user.id, ref_code=f"TMP-{uuid.uuid4().hex[:12]}",
                      approval_status=ApprovalStatus.pending, status=ListingStatus.available)
    _apply(listing, body)
    db.add(listing)
    db.flush()
    listing.ref_code = f"GK-S{listing.id:05d}"
    db.commit()
    return to_detail(_own(db, user, listing.id))


@router.put("/listings/{listing_id}", response_model=ListingDetail)
def update_listing(listing_id: int, body: ListingIn, user: User = Depends(seller_only),
                   db: Session = Depends(get_db)) -> ListingDetail:
    listing = _own(db, user, listing_id)
    _apply(listing, body)
    # Any edit goes back through review; the embedding is rebuilt on approval.
    listing.approval_status = ApprovalStatus.pending
    listing.embedding = None
    db.commit()
    return to_detail(_own(db, user, listing_id))


@router.post("/listings/{listing_id}/sold", response_model=ListingDetail)
def mark_sold(listing_id: int, user: User = Depends(seller_only), db: Session = Depends(get_db)) -> ListingDetail:
    listing = _own(db, user, listing_id)
    listing.status = ListingStatus.sold
    db.commit()
    return to_detail(_own(db, user, listing_id))


@router.post("/listings/{listing_id}/images", response_model=ListingDetail)
async def upload_image(listing_id: int, file: UploadFile = File(...), user: User = Depends(seller_only),
                       db: Session = Depends(get_db)) -> ListingDetail:
    listing = _own(db, user, listing_id)
    s = get_settings()
    if len(listing.images) >= s.max_images_per_listing:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"At most {s.max_images_per_listing} photos per listing")
    data = await file.read(s.max_image_bytes + 1)
    try:
        img = process_image(data)
    except ImageValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    storage = get_storage()
    key = f"listings/{listing.id}/{uuid.uuid4().hex[:12]}"
    url = storage.save(f"{key}_web.{img.extension}", img.web, img.content_type)
    thumb = storage.save(f"{key}_thumb.{img.extension}", img.thumb, img.content_type)
    db.add(ListingImage(listing_id=listing.id, url=url, thumb_url=thumb, storage_key=key,
                        sort_order=len(listing.images)))
    db.commit()
    db.expire_all()
    return to_detail(_own(db, user, listing_id))


@router.delete("/listings/{listing_id}/images/{image_id}", response_model=ListingDetail)
def delete_image(listing_id: int, image_id: int, user: User = Depends(seller_only),
                 db: Session = Depends(get_db)) -> ListingDetail:
    listing = _own(db, user, listing_id)
    image = next((i for i in listing.images if i.id == image_id), None)
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Photo not found")
    get_storage().delete_prefix(image.storage_key)
    db.delete(image)
    db.commit()
    db.expire_all()
    return to_detail(_own(db, user, listing_id))
