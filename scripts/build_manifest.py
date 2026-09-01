#!/usr/bin/env python3
from __future__ import annotations

import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {"__pycache__", ".pytest_cache", ".git", "*.egg-info"}
EXCLUDED_FILES = {"MANIFEST_SHA256.txt"}


def include(path: Path) -> bool:
    if path.name in EXCLUDED_FILES:
        return False
    for part in path.relative_to(ROOT).parts:
        if part in {"__pycache__", ".pytest_cache", ".git"} or part.endswith(".egg-info"):
            return False
    return path.is_file() and path.suffix != ".pyc"


rows = []
for path in sorted(ROOT.rglob("*")):
    if not include(path):
        continue
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rows.append(f"{digest}  {path.relative_to(ROOT).as_posix()}")
(ROOT / "MANIFEST_SHA256.txt").write_text("\n".join(rows) + "\n", encoding="utf-8")
print(f"wrote {len(rows)} hashes")
