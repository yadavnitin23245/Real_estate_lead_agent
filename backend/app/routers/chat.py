"""Buyer chat with the HomeMatch assistant.

Visitors don't need an account: the browser sends a random ``X-Guest-Id``.
When a signed-in buyer chats, their guest conversation (if any) is attached to them.
"""

from __future__ import annotations

import re
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.agent import AgentUnavailable, run_turn
from app.config import get_settings
from app.db import get_db
from app.deps import get_optional_user
from app.models import Conversation, Lead, LeadStatus, Listing, Message, MessageRole, Role, User
from app.routers.common import to_card
from app.schemas import ListingCard

router = APIRouter(prefix="/api/chat", tags=["chat"])
GUEST_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")
_hits: dict[str, deque[float]] = defaultdict(deque)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    listings: list[ListingCard] = []


class ChatOut(BaseModel):
    lead_id: int | None
    messages: list[ChatMessageOut]
    handed_off_to: str | None = None


def _guest(x_guest_id: str | None) -> str | None:
    return x_guest_id if x_guest_id and GUEST_RE.match(x_guest_id) else None


def _find_lead(db: Session, user: User | None, guest_id: str | None, create: bool) -> Lead | None:
    open_ = Lead.status != LeadStatus.closed
    buyer = user if user and user.role == Role.buyer else None
    lead = None
    if buyer:
        lead = db.scalar(select(Lead).where(Lead.user_id == buyer.id, open_).order_by(Lead.created_at.desc()))
    if lead is None and guest_id:
        lead = db.scalar(select(Lead).where(Lead.guest_id == guest_id, open_).order_by(Lead.created_at.desc()))
        if lead is not None and buyer and lead.user_id is None:
            lead.user_id = buyer.id
            lead.name = lead.name or buyer.name
            lead.email = lead.email or buyer.email
            lead.phone = lead.phone or buyer.phone
    if lead is None and create:
        lead = Lead(
            user_id=buyer.id if buyer else None,
            guest_id=guest_id,
            name=buyer.name if buyer else None,
            email=buyer.email if buyer else None,
            phone=buyer.phone if buyer else None,
            city=get_settings().city_default,
            status=LeadStatus.new,
        )
        db.add(lead)
        db.flush()
        db.add(Conversation(lead_id=lead.id, thread_id=uuid.uuid4().hex))
        db.flush()
    return lead


def _rate_limit(key: str) -> None:
    limit = get_settings().chat_rate_per_minute
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "You're sending messages too fast. Please wait a moment.")
    q.append(now)


def _history(db: Session, lead: Lead | None) -> ChatOut:
    if lead is None:
        return ChatOut(lead_id=None, messages=[])
    msgs = list(db.scalars(select(Message).where(Message.lead_id == lead.id).order_by(Message.created_at, Message.id)))
    ids = {i for m in msgs for i in (m.meta or {}).get("listing_ids", [])}
    cards = {
        listing.id: to_card(listing)
        for listing in db.scalars(select(Listing).where(Listing.id.in_(ids)).options(selectinload(Listing.images)))
    } if ids else {}
    agent = lead.assigned_agent.name if lead.status == LeadStatus.handed_off and lead.assigned_agent else None
    return ChatOut(
        lead_id=lead.id,
        handed_off_to=agent,
        messages=[
            ChatMessageOut(
                id=m.id, role=m.role.value, content=m.content, created_at=m.created_at,
                listings=[cards[i] for i in (m.meta or {}).get("listing_ids", []) if i in cards],
            )
            for m in msgs
        ],
    )


@router.get("", response_model=ChatOut)
def history(
    x_guest_id: str | None = Header(default=None),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    lead = _find_lead(db, user, _guest(x_guest_id), create=False)
    out = _history(db, lead)
    db.commit()  # persists a guest -> account attach
    return out


@router.post("", response_model=ChatOut)
def send(
    body: ChatIn,
    x_guest_id: str | None = Header(default=None),
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ChatOut:
    guest_id = _guest(x_guest_id)
    if user is None and guest_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Missing X-Guest-Id header")
    _rate_limit(f"u{user.id}" if user else f"g{guest_id}")

    lead = _find_lead(db, user, guest_id, create=True)
    assert lead is not None
    conv = db.scalar(select(Conversation).where(Conversation.lead_id == lead.id).order_by(Conversation.id))
    if conv is None:
        conv = Conversation(lead_id=lead.id, thread_id=uuid.uuid4().hex)
        db.add(conv)
        db.flush()
    text = body.message.strip()

    try:
        turn = run_turn(db, lead, text)
    except AgentUnavailable:
        db.rollback()
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "The assistant is unavailable right now. Please try again in a minute.") from None

    if lead.status == LeadStatus.new:
        lead.status = LeadStatus.qualifying
    db.add(Message(conversation_id=conv.id, lead_id=lead.id, role=MessageRole.user, content=text))
    db.flush()
    db.add(Message(conversation_id=conv.id, lead_id=lead.id, role=MessageRole.assistant, content=turn.reply,
                   meta={"listing_ids": turn.listing_ids} if turn.listing_ids else None))
    lead.updated_at = datetime.now().astimezone()
    db.commit()
    db.refresh(lead)
    return _history(db, lead)
