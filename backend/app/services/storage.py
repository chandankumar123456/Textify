#backend/app/services/storage.py
import logging
from pathlib import Path
from ..config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.data_dir = Path(settings.DATA_DIR)
        self._ensure_dirs()

    def _ensure_dirs(self):
        for subdir in ("uploads", "pages", "results"):
            (self.data_dir / subdir).mkdir(parents=True, exist_ok=True)

    def upload_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream"):
        path = self.data_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.debug("Stored %d bytes at %s", len(data), path)

    def download_bytes(self, key: str) -> bytes:
        path = self.data_dir / key
        if not path.exists():
            raise FileNotFoundError(f"File not found: {key}")
        return path.read_bytes()

    def list_objects(self, prefix: str) -> list:
        """Return all file keys that start with *prefix* (relative to data_dir)."""
        base = self.data_dir / prefix
        if base.is_dir():
            return [str(p.relative_to(self.data_dir)).replace("\\", "/")
                    for p in base.rglob("*") if p.is_file()]
        parent = base.parent
        name_prefix = base.name
        if parent.is_dir():
            return [str(p.relative_to(self.data_dir)).replace("\\", "/")
                    for p in parent.iterdir()
                    if p.is_file() and p.name.startswith(name_prefix)]
        return []

    def delete_object(self, key: str):
        path = self.data_dir / key
        if path.exists():
            path.unlink()
            logger.debug("Deleted %s", path)
