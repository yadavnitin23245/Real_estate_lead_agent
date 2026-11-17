"""Request / response models for the HTTP API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models import (
    ApprovalStatus,
    AreaUnit,
    Furnishing,
    LeadScore,
    LeadStatus,
    ListingStatus,
    PropertyType,
    Role,
    VisitStatus,
)


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------- auth / users
class UserOut(ORM):
    id: int
    name: str
    email: str
    phone: str | None
    role: Role
    is_active: bool
    created_at: datetime


class SignupIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    # Staff accounts (sales agents, admins) are created by an admin, not by sign-up.
    role: Literal["buyer", "seller"] = "buyer"

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut


class StaffCreateIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.sales_agent


class UserPatch(BaseModel):
    is_active: bool | None = None
    role: Role | None = None


# --------------------------------------------------------------------------- listings
class ImageOut(ORM):
    id: int
    url: str
    thumb_url: str


class ListingCard(ORM):
    id: int
    ref_code: str
    title: str
    city: str
    locality: str
    property_type: PropertyType
    bedrooms: int | None
    bathrooms: int | None
    area_value: float | None
    area_unit: AreaUnit
    price_inr: int
    furnishing: Furnishing | None
    has_parking: bool
    near_school: bool
    near_metro: bool
    status: ListingStatus
    approval_status: ApprovalStatus
    thumb_url: str | None = None
    created_at: datetime


class ListingDetail(ListingCard):
    description: str
    images: list[ImageOut]
    owner_name: str | None = None


class ListingPage(BaseModel):
    items: list[ListingCard]
    total: int
    page: int
    page_size: int


class ListingIn(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    city: str = Field(default="Pune", max_length=80)
    locality: str = Field(min_length=2, max_length=80)
    property_type: PropertyType
    bedrooms: int | None = Field(default=None, ge=0, le=20)
    bathrooms: int | None = Field(default=None, ge=0, le=20)
    area_value: float | None = Field(default=None, gt=0)
    area_unit: AreaUnit = AreaUnit.sqft
    price_inr: int = Field(gt=0)
    furnishing: Furnishing | None = None
    has_parking: bool = False
    near_school: bool = False
    near_metro: bool = False
    description: str = Field(default="", max_length=5000)


class Facets(BaseModel):
    localities: list[str]
    property_types: list[str]
    price_min: int
    price_max: int


# --------------------------------------------------------------------------- leads
class AgentRef(ORM):
    id: int
    name: str


class LeadRow(ORM):
    id: int
    name: str | None
    phone: str | None
    email: str | None
    budget_min: int | None
    budget_max: int | None
    preferred_localities: list[str]
    property_type: PropertyType | None
    bedrooms: int | None
    timeline_months: int | None
    loan_preapproved: bool | None
    score: LeadScore
    status: LeadStatus
    assigned_agent: AgentRef | None
    handed_off_at: datetime | None
    created_at: datetime
    updated_at: datetime


class MessageOut(ORM):
    id: int
    role: str
    content: str
    created_at: datetime


class MatchOut(BaseModel):
    rank: int
    reason: str
    matched_filters: dict[str, Any] | None
    listing: ListingCard


class VisitOut(BaseModel):
    id: int
    preferred_time: str
    status: VisitStatus
    created_at: datetime
    listing: ListingCard


class LeadDetail(LeadRow):
    must_haves: dict[str, bool]
    soft_preferences: str | None
    summary: str | None
    notes: str | None
    city: str | None
    messages: list[MessageOut] = []
    matches: list[MatchOut] = []
    visits: list[VisitOut] = []


class LeadPatch(BaseModel):
    status: LeadStatus | None = None
    notes: str | None = Field(default=None, max_length=5000)
    assigned_agent_id: int | None = None


class VisitPatch(BaseModel):
    status: VisitStatus


class RejectIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)
