"""Minimal structured runtime logging."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from eral.engine.paths import RuntimePaths


@dataclass(slots=True)
class RuntimeLogger:
    """Append newline-delimited JSON entries for key runtime actions."""

    paths: RuntimePaths

    def log_path(self) -> Path:
        return self.paths.logs / "runtime.jsonl"

    def append(self, **payload: Any) -> None:
        path = self.log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
