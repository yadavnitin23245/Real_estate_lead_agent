"""Helpers shared by routers."""

from __future__ import annotations

from app.models import Listing
from app.schemas import ListingCard, ListingDetail


def to_card(listing: Listing) -> ListingCard:
    card = ListingCard.model_validate(listing)
    card.thumb_url = listing.images[0].thumb_url if listing.images else None
    return card


def to_detail(listing: Listing) -> ListingDetail:
    detail = ListingDetail.model_validate(listing)
    detail.thumb_url = listing.images[0].thumb_url if listing.images else None
    detail.owner_name = listing.owner.name if listing.owner else None
    return detail
