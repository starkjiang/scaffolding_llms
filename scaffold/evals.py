"""Evaluation runner (Part 5): deterministic checks + model-as-judge, per-type scores."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .llm import LLM
from .prompts import JUDGE
from .structured import extract_json
from .tracing import trace

from .domains import data_dir  # noqa: E402
REPORTS = Path(__file__).resolve().parent.parent / "reports"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


@dataclass
class CaseResult:
    id: str
    type: str
    passed: bool
    checks: dict[str, bool] = field(default_factory=dict)
    output: str = ""
    judge: dict | None = None


def deterministic_checks(case: dict, triage: dict | None, output_text: str) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    exp = case.get("expected", {})
    if triage is not None:
        for k, v in exp.items():
            checks[f"field:{k}"] = (triage.get(k) == v)
    low = output_text.lower()
    for pat in case.get("forbidden", []):
        checks[f"forbidden:{pat}"] = re.search(pat, low) is None
    for s in case.get("must_contain", []):
        checks[f"contains:{s}"] = s.lower() in low
    return checks


def judge(llm: LLM, reply: str, article: str, ticket: str = "") -> dict:
    raw = llm.complete(JUDGE.render_user(ticket, reply=reply, article=article),
                       system=JUDGE.render_system(), tier="large")
    try:
        return json.loads(extract_json(raw))
    except Exception:
        return {"error": "judge output unparsable", "raw": raw[:200]}


def run_eval(system_fn: Callable[[dict], tuple[dict | None, str, str | None]],
             cases: list[dict] | None = None, tickets: list[dict] | None = None,
             llm: LLM | None = None, use_judge: bool = False, name: str = "eval") -> dict:
    """system_fn(ticket) -> (triage_dict_or_None, output_text, article_or_None)."""
    cases = cases or load_jsonl(data_dir() / "eval_cases.jsonl")
    tickets = {t["id"]: t for t in (tickets or load_jsonl(data_dir() / "tickets.jsonl"))}
    results: list[CaseResult] = []
    if True:
        for case in cases:
            ticket = tickets[case["id"]]
            try:
                triage, out, article = system_fn(ticket)
            except Exception as e:
                results.append(CaseResult(case["id"], case["type"], False, {"exception": False}, str(e)))
                continue
            checks = deterministic_checks(case, triage, out)
            j = None
            if use_judge and llm is not None and article:
                j = judge(llm, out, article, ticket["text"])
                if "safe" in j:
                    checks["judge:safe"] = j["safe"] >= 2
                    checks["judge:faithful"] = j["faithful"] >= 1
            results.append(CaseResult(case["id"], case["type"], all(checks.values()) if checks else True,
                                      checks, out, j))
    by_type: dict[str, list[bool]] = defaultdict(list)
    for r in results:
        by_type[r.type].append(r.passed)
    summary = {
        "name": name,
        "pass_rate": round(sum(r.passed for r in results) / len(results), 3),
        "by_type": {t: f"{sum(v)}/{len(v)}" for t, v in sorted(by_type.items())},
        "failures": [{"id": r.id, "failed": [k for k, v in r.checks.items() if not v]} for r in results if not r.passed],
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / f"{name}.json").write_text(json.dumps({"summary": summary,
                                                      "results": [r.__dict__ for r in results]}, indent=2))
    return summary


def print_summary(s: dict) -> None:
    print(f"\n== {s['name']} ==  pass rate {s['pass_rate']:.0%}")
    for t, v in s["by_type"].items():
        print(f"   {t:<14} {v}")
    for f in s["failures"]:
        print(f"   ✗ {f['id']}: {', '.join(f['failed'])}")
