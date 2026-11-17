"""FastAPI application entry point."""

import mimetypes
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text

from app.config import get_settings
from app.db import SessionLocal
from app.models import ApprovalStatus, Lead, Listing, ListingStatus, User
from app.routers import admin, auth, chat, leads, listings, seller

settings = get_settings()
mimetypes.add_type("image/webp", ".webp")  # slim images lack it; StaticFiles would send text/plain

app = FastAPI(title="HomeMatch API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
for r in (auth.router, listings.router, seller.router, leads.router, admin.router, chat.router):
    app.include_router(r)

app.mount(settings.uploads_url_prefix, StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/api/health")
def health() -> dict[str, object]:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
        visible = db.scalar(
            select(func.count())
            .select_from(Listing)
            .where(
                Listing.approval_status == ApprovalStatus.approved,
                Listing.status == ListingStatus.available,
            )
        )
        return {
            "status": "ok",
            "users": db.scalar(select(func.count()).select_from(User)),
            "listings": db.scalar(select(func.count()).select_from(Listing)),
            "visible_listings": visible,
            "leads": db.scalar(select(func.count()).select_from(Lead)),
        }
