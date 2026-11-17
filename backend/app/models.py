"""Database models.

Enums are stored as VARCHAR + CHECK constraint (``native_enum=False``) so adding
a value later is a simple migration instead of an ``ALTER TYPE``.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import get_settings
from app.db import Base

EMBED_DIM = get_settings().embed_dim


# --------------------------------------------------------------------------- enums
class Role(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    sales_agent = "sales_agent"
    admin = "admin"


class PropertyType(str, enum.Enum):
    apartment = "apartment"
    house = "house"
    villa = "villa"
    plot_land = "plot_land"
    commercial = "commercial"


class ListingStatus(str, enum.Enum):
    available = "available"
    sold = "sold"


class ApprovalStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Furnishing(str, enum.Enum):
    unfurnished = "unfurnished"
    semi_furnished = "semi_furnished"
    fully_furnished = "fully_furnished"


class AreaUnit(str, enum.Enum):
    sqft = "sqft"
    sqm = "sqm"
    sqyd = "sqyd"
    guntha = "guntha"
    acre = "acre"


class LeadScore(str, enum.Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"


class LeadStatus(str, enum.Enum):
    new = "new"
    qualifying = "qualifying"
    handed_off = "handed_off"
    nurture = "nurture"
    closed = "closed"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class VisitStatus(str, enum.Enum):
    requested = "requested"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


def _enum(e: type[enum.Enum], name: str) -> Enum:
    return Enum(
        e,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def _updated() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


# --------------------------------------------------------------------------- users
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)  # stored lower-cased
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(_enum(Role, "user_role"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = _created()

    listings: Mapped[list[Listing]] = relationship(back_populates="owner")


# --------------------------------------------------------------------------- listings
class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (
        CheckConstraint("price_inr > 0", name="price_positive"),
        CheckConstraint("area_value IS NULL OR area_value > 0", name="area_positive"),
        CheckConstraint(
            "property_type <> 'plot_land' OR "
            "(bedrooms IS NULL AND bathrooms IS NULL AND area_value IS NOT NULL)",
            name="plot_shape",
        ),
        Index("ix_listings_visible", "approval_status", "status", "city", "property_type"),
        Index(
            "ix_listings_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Human-readable stable code, e.g. GK-BAN-007 (also lets evals reference listings).
    ref_code: Mapped[str] = mapped_column(String(20), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    city: Mapped[str] = mapped_column(String(80))
    locality: Mapped[str] = mapped_column(String(80), index=True)
    property_type: Mapped[PropertyType] = mapped_column(_enum(PropertyType, "property_type"))
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    bathrooms: Mapped[int | None] = mapped_column(Integer)
    area_value: Mapped[float | None] = mapped_column(Float)
    area_unit: Mapped[AreaUnit] = mapped_column(
        _enum(AreaUnit, "area_unit"), server_default=AreaUnit.sqft.value, default=AreaUnit.sqft
    )
    price_inr: Mapped[int] = mapped_column(BigInteger, index=True)
    furnishing: Mapped[Furnishing | None] = mapped_column(_enum(Furnishing, "furnishing"))
    has_parking: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    near_school: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    near_metro: Mapped[bool] = mapped_column(Boolean, server_default=text("false"), default=False)
    status: Mapped[ListingStatus] = mapped_column(
        _enum(ListingStatus, "listing_status"),
        server_default=ListingStatus.available.value,
        default=ListingStatus.available,
    )
    approval_status: Mapped[ApprovalStatus] = mapped_column(
        _enum(ApprovalStatus, "approval_status"),
        server_default=ApprovalStatus.pending.value,
        default=ApprovalStatus.pending,
    )
    description: Mapped[str] = mapped_column(Text, server_default="", default="")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    owner: Mapped[User] = relationship(back_populates="listings")
    images: Mapped[list[ListingImage]] = relationship(
        back_populates="listing",
        order_by="ListingImage.sort_order",
        cascade="all, delete-orphan",
    )


class ListingImage(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(500))
    thumb_url: Mapped[str] = mapped_column(String(500))
    # key prefix inside the FileStorage, so files can be deleted with the row
    storage_key: Mapped[str] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    created_at: Mapped[datetime] = _created()

    listing: Mapped[Listing] = relationship(back_populates="images")


# --------------------------------------------------------------------------- leads
class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (Index("ix_leads_score_status", "score", "status"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    # Anonymous visitor id (cookie) for guest chats; cleared/kept when attached to a user.
    guest_id: Mapped[str | None] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20))
    email: Mapped[str | None] = mapped_column(String(254))
    budget_min: Mapped[int | None] = mapped_column(BigInteger)
    budget_max: Mapped[int | None] = mapped_column(BigInteger)
    city: Mapped[str | None] = mapped_column(String(80))
    preferred_localities: Mapped[list[str]] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb"), default=list
    )
    property_type: Mapped[PropertyType | None] = mapped_column(
        _enum(PropertyType, "lead_property_type")
    )
    bedrooms: Mapped[int | None] = mapped_column(Integer)
    timeline_months: Mapped[int | None] = mapped_column(Integer)
    loan_preapproved: Mapped[bool | None] = mapped_column(Boolean)
    # Hard boolean filters the buyer asked for, e.g. {"has_parking": true, "near_metro": true}
    must_haves: Mapped[dict[str, bool]] = mapped_column(
        JSONB, server_default=text("'{}'::jsonb"), default=dict
    )
    soft_preferences: Mapped[str | None] = mapped_column(Text)
    score: Mapped[LeadScore] = mapped_column(
        _enum(LeadScore, "lead_score"), server_default=LeadScore.cold.value, default=LeadScore.cold
    )
    status: Mapped[LeadStatus] = mapped_column(
        _enum(LeadStatus, "lead_status"), server_default=LeadStatus.new.value, default=LeadStatus.new
    )
    summary: Mapped[str | None] = mapped_column(Text)
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    handed_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    user: Mapped[User | None] = relationship(foreign_keys=[user_id])
    assigned_agent: Mapped[User | None] = relationship(foreign_keys=[assigned_agent_id])
    matches: Mapped[list[LeadMatch]] = relationship(
        back_populates="lead", order_by="LeadMatch.rank", cascade="all, delete-orphan"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    # LangGraph checkpointer thread id
    thread_id: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (Index("ix_messages_lead_created", "lead_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    role: Mapped[MessageRole] = mapped_column(_enum(MessageRole, "message_role"))
    content: Mapped[str] = mapped_column(Text)
    # Extra render data: agent steps, listing ids shown, action chips
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()


class LeadMatch(Base):
    __tablename__ = "lead_matches"
    __table_args__ = (UniqueConstraint("lead_id", "listing_id", name="uq_lead_matches_lead_listing"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    rank: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text)
    # For the "Why this?" expand: which hard filters matched / were relaxed
    matched_filters: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _created()

    lead: Mapped[Lead] = relationship(back_populates="matches")
    listing: Mapped[Listing] = relationship()


class Shortlist(Base):
    __tablename__ = "shortlists"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    listing_id: Mapped[int] = mapped_column(
        ForeignKey("listings.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = _created()


class VisitRequest(Base):
    __tablename__ = "visit_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"))
    preferred_time: Mapped[str] = mapped_column(String(120))  # free text, e.g. "Sat morning"
    status: Mapped[VisitStatus] = mapped_column(
        _enum(VisitStatus, "visit_status"),
        server_default=VisitStatus.requested.value,
        default=VisitStatus.requested,
    )
    assigned_agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = _created()
    updated_at: Mapped[datetime] = _updated()

    lead: Mapped[Lead] = relationship()
    listing: Mapped[Listing] = relationship()


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL"), index=True
    )
    type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    tokens: Mapped[int] = mapped_column(Integer, server_default=text("0"), default=0)
    cost: Mapped[float] = mapped_column(Float, server_default=text("0"), default=0.0)  # USD
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
