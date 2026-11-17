"""Test configuration.

Settings need DB credentials; defaults here let pure unit tests run without a
.env. DB-backed tests (from step 2 on) use the docker-compose database.
"""

import os

os.environ.setdefault("POSTGRES_USER", "homematch")
os.environ.setdefault("POSTGRES_PASSWORD", "test-only")
os.environ.setdefault("POSTGRES_DB", "homematch")
os.environ.setdefault("EMBED_BACKEND", "hash")
