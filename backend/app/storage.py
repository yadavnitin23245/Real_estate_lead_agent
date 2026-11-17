"""File storage abstraction.

``LocalFileStorage`` writes to ``UPLOAD_DIR`` (a Docker volume in dev) and the API
serves it under ``/uploads``. S3 / Supabase are stubs to fill in for production.
"""

from __future__ import annotations

import abc
import shutil
from pathlib import Path

from app.config import get_settings


class FileStorage(abc.ABC):
    @abc.abstractmethod
    def save(self, key: str, data: bytes, content_type: str) -> str:
        """Store ``data`` under ``key`` and return its public URL."""

    @abc.abstractmethod
    def delete_prefix(self, prefix: str) -> None:
        """Delete every object whose key starts with ``prefix``."""

    @abc.abstractmethod
    def exists(self, key: str) -> bool: ...


class LocalFileStorage(FileStorage):
    def __init__(self, root: str, url_prefix: str) -> None:
        self.root = Path(root).resolve()
        self.url_prefix = url_prefix.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("invalid storage key")
        return path

    def save(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"{self.url_prefix}/{key}"

    def delete_prefix(self, prefix: str) -> None:
        base = self._path(prefix)
        if base.is_dir():
            shutil.rmtree(base, ignore_errors=True)
        for p in base.parent.glob(base.name + "*"):
            if p.is_file():
                p.unlink(missing_ok=True)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


class S3FileStorage(FileStorage):  # pragma: no cover - production stub
    """TODO: implement with boto3 (put_object / delete_objects / head_object)
    and return a CloudFront or bucket URL."""

    def save(self, key: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError("S3 storage is not configured yet")

    def delete_prefix(self, prefix: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError


class SupabaseFileStorage(FileStorage):  # pragma: no cover - production stub
    """TODO: implement with supabase-py storage.from_(bucket).upload/remove."""

    def save(self, key: str, data: bytes, content_type: str) -> str:
        raise NotImplementedError("Supabase storage is not configured yet")

    def delete_prefix(self, prefix: str) -> None:
        raise NotImplementedError

    def exists(self, key: str) -> bool:
        raise NotImplementedError


_storage: FileStorage | None = None


def get_storage() -> FileStorage:
    global _storage
    if _storage is None:
        s = get_settings()
        if s.storage_backend == "s3":
            _storage = S3FileStorage()
        elif s.storage_backend == "supabase":
            _storage = SupabaseFileStorage()
        else:
            _storage = LocalFileStorage(s.upload_dir, s.uploads_url_prefix)
    return _storage
