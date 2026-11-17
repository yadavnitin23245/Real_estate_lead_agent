"""Startup tasks: make sure the admin account from env exists."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Role, User
from app.security import hash_password

log = logging.getLogger(__name__)


def ensure_admin(db: Session) -> User | None:
    """Create the admin from ADMIN_EMAIL / ADMIN_PASSWORD if it doesn't exist yet.

    An existing admin's password is never overwritten, so changing it in the UI
    sticks across restarts.
    """
    s = get_settings()
    if not s.admin_email or not s.admin_password:
        log.warning("ADMIN_EMAIL / ADMIN_PASSWORD not set - no admin account seeded")
        return None
    email = s.admin_email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            name="GreenKey Admin",
            email=email,
            password_hash=hash_password(s.admin_password),
            role=Role.admin,
            is_active=True,
        )
        db.add(user)
        db.flush()
        log.info("Seeded admin account %s", email)
    elif user.role != Role.admin or not user.is_active:
        user.role = Role.admin
        user.is_active = True
    return user
