"""Shared helpers for the labs."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scaffold import get_llm, trace  # noqa: E402

DATA = ROOT / "data"


def load_jsonl(name: str) -> list[dict]:
    return [json.loads(l) for l in (DATA / name).read_text(encoding="utf-8").splitlines() if l.strip()]


def banner(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


__all__ = ["get_llm", "trace", "load_jsonl", "banner", "DATA", "ROOT"]
