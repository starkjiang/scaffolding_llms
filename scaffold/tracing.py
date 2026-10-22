"""Tiny tracing: nested spans with timing, printed as an indented tree.

    with trace.span("extract", ticket_id="T-001") as sp:
        ...
        sp.log(fields=5)
    trace.print_last()
"""
from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Span:
    name: str
    attrs: dict[str, Any]
    start: float = field(default_factory=time.perf_counter)
    end: float | None = None
    children: list["Span"] = field(default_factory=list)
    logs: dict[str, Any] = field(default_factory=dict)

    def log(self, **kw: Any) -> None:
        self.logs.update(kw)

    @property
    def ms(self) -> float:
        return ((self.end or time.perf_counter()) - self.start) * 1000

    def to_dict(self) -> dict:
        return {"name": self.name, "ms": round(self.ms, 1), "attrs": self.attrs,
                "logs": self.logs, "children": [c.to_dict() for c in self.children]}


class Tracer:
    def __init__(self) -> None:
        self._stack: list[Span] = []
        self.roots: list[Span] = []

    @contextmanager
    def span(self, name: str, **attrs: Any):
        sp = Span(name, attrs)
        if self._stack:
            self._stack[-1].children.append(sp)
        else:
            self.roots.append(sp)
        self._stack.append(sp)
        try:
            yield sp
        finally:
            sp.end = time.perf_counter()
            if self._stack and self._stack[-1] is sp:
                self._stack.pop()

    def reset(self) -> None:
        self.roots.clear()
        self._stack.clear()

    def token_totals(self) -> tuple[int, int]:
        def walk(s: Span):
            i = s.logs.get("input_tokens", 0) or 0
            o = s.logs.get("output_tokens", 0) or 0
            for c in s.children:
                ci, co = walk(c)
                i, o = i + ci, o + co
            return i, o
        ti = to = 0
        for r in self.roots:
            i, o = walk(r)
            ti, to = ti + i, to + o
        return ti, to

    def print_last(self) -> None:
        if self.roots:
            self._print(self.roots[-1], 0)

    def _print(self, s: Span, depth: int) -> None:
        pad = "  " * depth
        attrs = " ".join(f"{k}={v}" for k, v in s.attrs.items())
        print(f"{pad}├─ {s.name} ({s.ms:.0f} ms) {attrs}")
        for k, v in s.logs.items():
            vs = json.dumps(v, default=str)
            print(f"{pad}│    {k}: {vs[:140]}")
        for c in s.children:
            self._print(c, depth + 1)


trace = Tracer()
