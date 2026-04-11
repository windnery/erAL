"""Project paths derived from the repository root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class RuntimePaths:
    """Canonical path set for the erAL repository."""

    root: Path
    src: Path
    docs: Path
    data: Path
    mods: Path
    assets: Path
    tests: Path
    runtime: Path
    saves: Path
    cache: Path
    logs: Path

    @classmethod
    def from_root(cls, root: Path) -> "RuntimePaths":
        runtime = root / "runtime"
        return cls(
            root=root,
            src=root / "src",
            docs=root / "docs",
            data=root / "data",
            mods=root / "mods",
            assets=root / "assets",
            tests=root / "tests",
            runtime=runtime,
            saves=runtime / "saves",
            cache=runtime / "cache",
            logs=runtime / "logs",
        )

    def ensure_runtime_dirs(self) -> None:
        for path in (self.runtime, self.saves, self.cache, self.logs):
            path.mkdir(parents=True, exist_ok=True)

