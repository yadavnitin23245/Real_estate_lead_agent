"""Seed the database with demo data.  Safe to re-run.

    python -m seed            # create whatever is missing
    python -m seed --reset    # wipe listings/leads/etc. (keeps users) and re-seed

Idempotency: users are keyed by email, listings by ref_code, sample leads by
email. Images and embeddings are only created where missing.
"""

from __future__ import annotations

import argparse
import logging
import random
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.bootstrap import ensure_admin
from app.config import get_settings
from app.db import SessionLocal
from app.embeddings import embed_many, listing_embedding_text
from app.images import ProcessedImage, process_image
from app.lead_summary import build_summary
from app.models import (
    ApprovalStatus,
    AreaUnit,
    Conversation,
    Event,
    Furnishing,
    Lead,
    LeadMatch,
    LeadStatus,
    Listing,
    ListingImage,
    ListingStatus,
    Message,
    MessageRole,
    PropertyType,
    Role,
    User,
    VisitRequest,
    VisitStatus,
)
from app.scoring import score_lead
from app.security import hash_password
from app.storage import get_storage
from seed.catalog import ListingSpec, generate_catalog, generate_pending
from seed.leads import LEADS, LeadSeed, generic_chat

log = logging.getLogger("seed")
ASSETS = Path(__file__).parent / "assets"
NOW = datetime.now(timezone.utc)

DEMO_USERS: list[tuple[str, str, str, Role]] = [
    # (name, email, phone, role) - password comes from DEMO_PASSWORD
    ("Demo Buyer", "demo.buyer@greenkey.example", "+91 90000 00001", Role.buyer),
    ("Demo Seller", "demo.seller@greenkey.example", "+91 90000 00002", Role.seller),
    ("Priya Kulkarni", "demo.agent@greenkey.example", "+91 90000 00003", Role.sales_agent),
    ("Rohan Deshmukh", "rohan.deshmukh@greenkey.example", "+91 90000 00004", Role.sales_agent),
    ("Ananya Joshi", "ananya.joshi@greenkey.example", "+91 90000 00005", Role.sales_agent),
    ("Vikram Patil", "vikram.patil@greenkey.example", "+91 90000 00006", Role.sales_agent),
]
# A few approved catalog listings belong to the demo seller so "My listings" has variety.
SELLER_OWNED = {"GK-BAN-002", "GK-WAK-005", "GK-KOT-004"}


# --------------------------------------------------------------------------- users
def seed_users(db: Session) -> dict[str, User]:
    password = get_settings().demo_password
    if not password:
        sys.exit("DEMO_PASSWORD is not set; add it to .env (see .env.example).")
    users: dict[str, User] = {}
    for name, email, phone, role in DEMO_USERS:
        user = db.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(name=name, email=email, phone=phone, role=role,
                        password_hash=hash_password(password), is_active=True)
            db.add(user)
            db.flush()
        users[email] = user
    return users


# --------------------------------------------------------------------------- listings
def _listing_from_spec(spec: ListingSpec, owner: User, approval: ApprovalStatus) -> Listing:
    created = NOW - timedelta(days=spec.days_ago, hours=random.Random(spec.ref_code).randint(0, 23))
    return Listing(
        ref_code=spec.ref_code,
        owner_id=owner.id,
        title=spec.title,
        city=spec.city,
        locality=spec.locality,
        property_type=PropertyType(spec.property_type),
        bedrooms=spec.bedrooms,
        bathrooms=spec.bathrooms,
        area_value=spec.area_value,
        area_unit=AreaUnit(spec.area_unit),
        price_inr=spec.price_inr,
        furnishing=Furnishing(spec.furnishing) if spec.furnishing else None,
        has_parking=spec.has_parking,
        near_school=spec.near_school,
        near_metro=spec.near_metro,
        status=ListingStatus(spec.status),
        approval_status=approval,
        description=spec.description,
        created_at=created,
        updated_at=created,
    )


def seed_listings(db: Session, admin: User, seller: User) -> tuple[int, dict[str, ListingSpec]]:
    existing = set(db.scalars(select(Listing.ref_code)))
    specs: dict[str, ListingSpec] = {}
    created = 0
    for spec in generate_catalog():
        specs[spec.ref_code] = spec
        if spec.ref_code in existing:
            continue
        owner = seller if spec.ref_code in SELLER_OWNED else admin
        db.add(_listing_from_spec(spec, owner, ApprovalStatus.approved))
        created += 1
    for spec in generate_pending():
        specs[spec.ref_code] = spec
        if spec.ref_code in existing:
            continue
        db.add(_listing_from_spec(spec, seller, ApprovalStatus.pending))
        created += 1
    db.flush()
    return created, specs


def seed_images(db: Session, specs: dict[str, ListingSpec]) -> int:
    storage = get_storage()
    cache: dict[str, ProcessedImage] = {}
    have_images = set(db.scalars(select(ListingImage.listing_id).distinct()))
    count = 0
    for listing in db.scalars(select(Listing).order_by(Listing.id)):
        spec = specs.get(listing.ref_code)
        if spec is None or listing.id in have_images:
            continue
        for order, asset in enumerate(spec.images):
            path = ASSETS / f"{asset}.jpg"
            if not path.exists():
                log.warning("missing asset %s", path.name)
                continue
            if asset not in cache:
                cache[asset] = process_image(path.read_bytes())
            img = cache[asset]
            key = f"listings/{listing.id}/{uuid.uuid4().hex[:12]}"
            url = storage.save(f"{key}_web.{img.extension}", img.web, img.content_type)
            thumb = storage.save(f"{key}_thumb.{img.extension}", img.thumb, img.content_type)
            db.add(ListingImage(listing_id=listing.id, url=url, thumb_url=thumb,
                                storage_key=key, sort_order=order))
            count += 1
    db.flush()
    return count


def seed_embeddings(db: Session) -> int:
    rows = list(db.scalars(select(Listing).where(Listing.embedding.is_(None)).order_by(Listing.id)))
    if not rows:
        return 0
    log.info("Embedding %d listing descriptions with %s (%s) ...",
             len(rows), get_settings().embed_model, get_settings().embed_backend)
    t0 = time.perf_counter()
    vectors = embed_many([listing_embedding_text(r.title, r.locality, r.description) for r in rows])
    for row, vec in zip(rows, vectors):
        row.embedding = vec
    db.flush()
    log.info("Embedded in %.1fs", time.perf_counter() - t0)
    return len(rows)


# --------------------------------------------------------------------------- leads
def _seed_matches(db: Session, lead: Lead) -> list[Listing]:
    """Simple filter + price-closeness match for demo leads (the real hybrid search
    arrives in step 4; this only populates sample data)."""
    if lead.budget_max is None and lead.budget_min is None:
        return []
    budget_max = lead.budget_max or int((lead.budget_min or 0) * 1.3)
    target = ((lead.budget_min or budget_max) + budget_max) / 2

    def query(with_localities: bool) -> list[Listing]:
        q = select(Listing).where(
            Listing.approval_status == ApprovalStatus.approved,
            Listing.status == ListingStatus.available,
            Listing.price_inr <= int(budget_max * 1.1),
        )
        if lead.city:
            q = q.where(Listing.city == lead.city)
        if lead.property_type:
            q = q.where(Listing.property_type == lead.property_type)
        if lead.bedrooms and lead.property_type in (PropertyType.apartment, PropertyType.house, PropertyType.villa):
            q = q.where(Listing.bedrooms == lead.bedrooms)
        for key, wanted in (lead.must_haves or {}).items():
            if wanted and hasattr(Listing, key):
                q = q.where(getattr(Listing, key).is_(True))
        if with_localities and lead.preferred_localities:
            q = q.where(Listing.locality.in_(lead.preferred_localities))
        return list(db.scalars(q.order_by(func.abs(Listing.price_inr - target)).limit(3)))

    found = query(True)
    if len(found) < 3:
        found += [x for x in query(False) if x not in found][: 3 - len(found)]

    for rank, listing in enumerate(found, start=1):
        over = listing.price_inr > budget_max
        reason_bits = [f"{listing.locality}", "slightly over budget" if over else "within budget"]
        if listing.near_school:
            reason_bits.append("near a school")
        if listing.near_metro:
            reason_bits.append("near metro")
        if listing.has_parking and listing.property_type != PropertyType.plot_land:
            reason_bits.append("has car parking")
        db.add(LeadMatch(
            lead_id=lead.id, listing_id=listing.id, rank=rank,
            reason=f"{listing.title}: " + ", ".join(reason_bits) + ".",
            matched_filters={
                "city": listing.city,
                "locality": listing.locality,
                "property_type": listing.property_type.value,
                "bedrooms": listing.bedrooms,
                "price": "slightly_over" if over else "within",
                **{k: True for k, v in (lead.must_haves or {}).items() if v},
            },
        ))
    return found


def _add_chat(db: Session, lead: Lead, ls: LeadSeed, agent: User | None, n_matches: int,
              start: datetime, rng: random.Random) -> None:
    conv = Conversation(lead_id=lead.id, thread_id=f"seed-{uuid.uuid4().hex}", created_at=start)
    db.add(conv)
    db.flush()
    chat = ls.chat or generic_chat(ls, agent.name if agent else None, n_matches)
    t = start
    for role, content in chat:
        t += timedelta(seconds=rng.randint(15, 90))
        db.add(Message(conversation_id=conv.id, lead_id=lead.id, role=MessageRole(role),
                       content=content, created_at=t))
        if role == "assistant":
            tokens = rng.randint(900, 2600)
            db.add(Event(lead_id=lead.id, type="llm_call", tokens=tokens,
                         cost=round(tokens * rng.uniform(0.4, 0.9) / 1_000_000, 6),
                         latency_ms=rng.randint(600, 2800), payload={"node": "respond", "seed": True},
                         created_at=t))
    conv.updated_at = t


def seed_leads(db: Session, agents: list[User]) -> int:
    existing = set(db.scalars(select(Lead.email).where(Lead.email.is_not(None))))
    rng = random.Random(2024)
    # round-robin continues from however many leads were already assigned
    rr = db.scalar(select(func.count()).select_from(Lead).where(Lead.assigned_agent_id.is_not(None))) or 0
    created = 0
    for ls in LEADS:
        if ls.email in existing:
            continue
        start = NOW - timedelta(days=ls.days_ago, hours=rng.randint(0, 6), minutes=rng.randint(0, 59))
        lead = Lead(
            name=ls.name, email=ls.email, phone=ls.phone, city=ls.city,
            preferred_localities=ls.localities,
            property_type=PropertyType(ls.property_type) if ls.property_type else None,
            bedrooms=ls.bedrooms, budget_min=ls.budget_min, budget_max=ls.budget_max,
            timeline_months=ls.timeline_months, loan_preapproved=ls.loan_preapproved,
            must_haves=ls.must_haves, soft_preferences=ls.soft_preferences,
            score=score_lead(ls.budget_min, ls.budget_max, ls.timeline_months, ls.loan_preapproved),
            status=LeadStatus(ls.status), notes=ls.notes, created_at=start, updated_at=start,
        )
        db.add(lead)
        db.flush()

        agent: User | None = None
        if lead.status in (LeadStatus.handed_off, LeadStatus.closed):
            agent = agents[rr % len(agents)]
            rr += 1
            lead.assigned_agent_id = agent.id
            lead.handed_off_at = start + timedelta(minutes=8)

        matches = _seed_matches(db, lead)
        _add_chat(db, lead, ls, agent, len(matches), start, rng)

        if lead.status in (LeadStatus.handed_off, LeadStatus.closed, LeadStatus.nurture):
            lead.summary = build_summary(lead, matches)
            db.add(Event(lead_id=lead.id, type="lead_scored", payload={"score": lead.score.value},
                         created_at=start + timedelta(minutes=7)))
        if agent:
            db.add(Event(lead_id=lead.id, type="handoff",
                         payload={"agent_id": agent.id, "score": lead.score.value},
                         created_at=lead.handed_off_at))
        if ls.visit and matches:
            db.add(VisitRequest(lead_id=lead.id, listing_id=matches[0].id, preferred_time=ls.visit[0],
                                status=VisitStatus(ls.visit[1]), assigned_agent_id=lead.assigned_agent_id,
                                created_at=start + timedelta(minutes=10)))
        created += 1
    db.flush()
    return created


# --------------------------------------------------------------------------- main
def reset(db: Session) -> None:
    log.warning("Resetting listings, leads and related data (users are kept)")
    db.execute(text(
        "TRUNCATE events, visit_requests, shortlists, lead_matches, messages, conversations, "
        "leads, listing_images, listings RESTART IDENTITY CASCADE"
    ))
    get_storage().delete_prefix("listings")
    db.commit()


def run(do_reset: bool = False) -> None:
    with SessionLocal() as db:
        if do_reset:
            reset(db)
        admin = ensure_admin(db)
        if admin is None:
            sys.exit("ADMIN_EMAIL / ADMIN_PASSWORD are not set; add them to .env (see .env.example).")
        users = seed_users(db)
        seller = users["demo.seller@greenkey.example"]
        agents = [u for u in users.values() if u.role == Role.sales_agent]
        db.commit()

        n_listings, specs = seed_listings(db, admin, seller)
        n_images = seed_images(db, specs)
        db.commit()
        n_emb = seed_embeddings(db)
        db.commit()
        n_leads = seed_leads(db, agents)
        db.commit()

        total = db.scalar(select(func.count()).select_from(Listing))
        visible = db.scalar(select(func.count()).select_from(Listing).where(
            Listing.approval_status == ApprovalStatus.approved, Listing.status == ListingStatus.available))
        log.info(
            "Seed done: +%d listings (%d total, %d visible to buyers), +%d images, +%d embeddings, "
            "+%d leads", n_listings, total, visible, n_images, n_emb, n_leads,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="wipe listings/leads before seeding")
    run(parser.parse_args().reset)


if __name__ == "__main__":
    main()
