"""Orchestration patterns (Part 2): chain, route, parallel, evaluator-optimizer.

Everything here is plain Python. The model is called inside steps; the
control flow is deterministic and testable.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable

from .tracing import trace

Step = Callable[[Any], Any]


@dataclass
class Outcome:
    """A first-class result: either a reply to send or an escalation."""

    status: str                       # "reply" | "escalate"
    text: str = ""
    reason: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        head = f"[{self.status.upper()}]" + (f" {self.reason}" if self.reason else "")
        return f"{head}\n{self.text}".strip()


class Escalate(Exception):
    """Raise anywhere in a chain to stop and hand off to a human."""

    def __init__(self, reason: str, data: dict | None = None):
        super().__init__(reason)
        self.reason, self.data = reason, data or {}


def chain(*steps: Step, name: str = "chain") -> Callable[[Any], Outcome]:
    """Run steps in sequence. A step may return an Outcome to end early or raise Escalate."""

    def run(x: Any) -> Outcome:
        with trace.span(name):
            try:
                for s in steps:
                    with trace.span(getattr(s, "__name__", "step")):
                        x = s(x)
                    if isinstance(x, Outcome):
                        return x
                return x if isinstance(x, Outcome) else Outcome("reply", text=str(x))
            except Escalate as e:
                return Outcome("escalate", reason=e.reason, data=e.data)
    return run


def route(classify: Callable[[Any], str], branches: dict[str, Step],
          default: str = "OTHER") -> Callable[[Any], Any]:
    """Pick a branch by label. Always include a default/escalation branch."""

    def run(x: Any) -> Any:
        with trace.span("route") as sp:
            label = classify(x)
            sp.log(label=label)
            handler = branches.get(label) or branches[default]
            return handler(x)
    return run


def parallel_map(fn: Step, items: Iterable[Any], workers: int = 4) -> list[Any]:
    """Sectioning: apply fn to each item concurrently."""
    with trace.span("parallel_map", workers=workers):
        with ThreadPoolExecutor(max_workers=workers) as ex:
            return list(ex.map(fn, items))


def vote(fn: Callable[[Any], bool], x: Any, n: int = 3) -> bool:
    """Voting: run a boolean check n times and take the majority."""
    with trace.span("vote", n=n) as sp:
        votes = parallel_map(lambda _: fn(x), range(n))
        sp.log(votes=votes)
        return sum(votes) > n / 2


def evaluator_optimizer(generate: Callable[[Any, str | None], str],
                        evaluate: Callable[[str], tuple[bool, str]],
                        x: Any, max_rounds: int = 2) -> tuple[str, bool]:
    """Generate → evaluate → revise, bounded by max_rounds."""
    with trace.span("evaluator_optimizer", max_rounds=max_rounds) as sp:
        feedback: str | None = None
        draft = ""
        for r in range(max_rounds + 1):
            draft = generate(x, feedback)
            ok, feedback = evaluate(draft)
            sp.log(**{f"round_{r}_ok": ok})
            if ok:
                return draft, True
        return draft, False
