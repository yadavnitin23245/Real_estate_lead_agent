"""Database management (code-first).

Point backend/.env (DB_HOST / DB_PORT / POSTGRES_* or DATABASE_URL) at any
Postgres server with the pgvector extension available, then:

    python manage.py setup            # create DB if missing + migrate + seed  (one command)
    python manage.py setup --no-seed  # create DB + tables only
    python manage.py migrate          # apply Alembic migrations
    python manage.py seed [--reset]   # idempotent demo data (--reset wipes listings/leads first)
    python manage.py check            # show connection target and migration status
"""

from __future__ import annotations

import argparse
import logging
import sys

import psycopg
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from psycopg import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.config import BACKEND_DIR, get_settings

log = logging.getLogger("manage")


def _url():
    return make_url(get_settings().database_url)


def _target() -> str:
    u = _url()
    return f"{u.host}:{u.port or 5432}/{u.database} (user {u.username})"


def _libpq(dbname: str) -> str:
    u = _url()
    return make_url(u).set(drivername="postgresql", database=dbname).render_as_string(hide_password=False)


def create_database() -> None:
    """Create the target database on the server if it doesn't exist yet."""
    name = _url().database
    try:
        with psycopg.connect(_libpq(name), connect_timeout=5):
            log.info("Database %s exists", name)
            return
    except psycopg.OperationalError as exc:
        if f'database "{name}" does not exist' not in str(exc):
            sys.exit(f"Cannot connect to Postgres at {_target()}:\n  {exc}")

    log.info("Database %s not found - creating it", name)
    try:
        with psycopg.connect(_libpq("postgres"), autocommit=True, connect_timeout=5) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    except psycopg.Error as exc:
        sys.exit(f"Could not create database {name!r} (does the user have CREATEDB?):\n  {exc}")


def ensure_pgvector() -> None:
    with psycopg.connect(_libpq(_url().database), autocommit=True, connect_timeout=5) as conn:
        available = conn.execute(
            "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"
        ).fetchone()
        if not available:
            sys.exit(
                "The pgvector extension is not installed on this Postgres server.\n"
                "Use the pgvector/pgvector:pg16 image, a managed Postgres with pgvector "
                "(Supabase, Neon, RDS...), or install it: https://github.com/pgvector/pgvector"
            )
        try:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except psycopg.Error as exc:
            sys.exit(f"pgvector is available but could not be enabled (needs owner/superuser):\n  {exc}")


def _alembic_cfg() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def migrate() -> None:
    log.info("Applying migrations on %s", _target())
    command.upgrade(_alembic_cfg(), "head")


def seed(reset: bool = False) -> None:
    from seed.__main__ import run

    run(reset)


def check() -> None:
    print("Target:", _target())
    head = ScriptDirectory.from_config(_alembic_cfg()).get_current_head()
    engine = create_engine(get_settings().database_url)
    try:
        with engine.connect() as conn:
            current = MigrationContext.configure(conn).get_current_revision()
    except Exception as exc:  # noqa: BLE001 - report any connection problem
        sys.exit(f"Cannot connect: {exc}")
    print(f"Migration: current={current} head={head} -> {'up to date' if current == head else 'NEEDS migrate'}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_setup = sub.add_parser("setup", help="create DB if missing, migrate, seed")
    p_setup.add_argument("--no-seed", action="store_true")
    p_setup.add_argument("--reset", action="store_true", help="wipe listings/leads before seeding")
    sub.add_parser("migrate", help="apply migrations")
    p_seed = sub.add_parser("seed", help="seed demo data (idempotent)")
    p_seed.add_argument("--reset", action="store_true")
    sub.add_parser("check", help="show target and migration status")
    args = parser.parse_args()

    if args.cmd == "setup":
        create_database()
        ensure_pgvector()
        migrate()
        if not args.no_seed:
            seed(args.reset)
    elif args.cmd == "migrate":
        ensure_pgvector()
        migrate()
    elif args.cmd == "seed":
        seed(args.reset)
    else:
        check()


if __name__ == "__main__":
    main()
