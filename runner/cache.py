"""Simple JSON cache for model responses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ResponseCache:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self._data: dict[str, Any] = {}
        if path and path.exists():
            self._data = json.loads(path.read_text(encoding="utf-8"))

    def key(self, *, model: str, case_id: str, prompt: str) -> str:
        digest = hashlib.sha256()
        digest.update(model.encode("utf-8"))
        digest.update(b"\0")
        digest.update(case_id.encode("utf-8"))
        digest.update(b"\0")
        digest.update(prompt.encode("utf-8"))
        return digest.hexdigest()

    def get(self, key: str) -> str | None:
        value = self._data.get(key)
        return str(value) if value is not None else None

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self._data, indent=2, sort_keys=True),
                encoding="utf-8",
            )
