"""JSON 文件原子读写存储."""

import json
import os
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path


class JsonFileStore:
    """线程安全的 JSON 文件存储."""

    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._lock = threading.RLock()
        self._ensure_file()

    def _ensure_file(self) -> None:
        if not self._file_path.exists():
            self._file_path.parent.mkdir(parents=True, exist_ok=True)
            self._write_atomic(self._empty_store())

    def _empty_store(self) -> dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return {
            "schema_version": 1,
            "meta": {"created_at": now, "updated_at": now},
            "users": [],
            "templates": [],
            "contracts": [],
            "approval_records": [],
            "messages": [],
            "audit_logs": [],
            "sessions": [],
        }

    def read(self) -> dict:
        with self._lock:
            with open(self._file_path, "r", encoding="utf-8") as f:
                return json.load(f)

    def transaction(self, mutator):
        """在锁内执行 mutator(data) → result，然后原子写入."""
        with self._lock:
            data = self._read_unlocked()
            result = mutator(data)
            self._write_atomic_unlocked(data)
            return result

    def _read_unlocked(self) -> dict:
        with open(self._file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_atomic(self, data: dict) -> None:
        data["meta"]["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self._file_path.parent, delete=False, suffix=".tmp"
        )
        try:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self._file_path)
        except Exception:
            tmp.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise

    def _write_atomic_unlocked(self, data: dict) -> None:
        data["meta"]["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=self._file_path.parent, delete=False, suffix=".tmp"
        )
        try:
            json.dump(data, tmp, ensure_ascii=False, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, self._file_path)
        except Exception:
            tmp.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise

    def new_id(self) -> str:
        return str(uuid.uuid4())

    def utcnow(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
