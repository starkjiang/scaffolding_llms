"""Which worked example are we using?

The workshop ships two parallel example domains so the ideas land whatever
industry you are from:

    ag      a dealer / agronomy support desk   (equipment codes, product labels)
    office  an expense and travel claims desk  (policy limits, approvals)

Both exercise exactly the same scaffolding. Only the subject matter changes.
Pick one with the WORKSHOP_DOMAIN environment variable, or `run.py --domain`.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DOMAINS = {
    "ag": {
        "data": ROOT / "data",
        "label": "Dealer / agronomy support desk",
        "unit": "ticket",
        "blurb": "Equipment fault codes, product labels, and field questions.",
    },
    "office": {
        "data": ROOT / "data" / "office",
        "label": "Expense and travel claims desk",
        "unit": "claim",
        "blurb": "Spending limits, travel policy, and what needs a manager's approval.",
    },
}

DEFAULT = "ag"


def current() -> str:
    d = os.getenv("WORKSHOP_DOMAIN", DEFAULT).strip().lower()
    return d if d in DOMAINS else DEFAULT


def data_dir() -> Path:
    """Where this domain's documents and sample data live."""
    return DOMAINS[current()]["data"]


def info() -> dict:
    return DOMAINS[current()]
