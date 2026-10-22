"""Session memory (Part 3): typed facts + rolling summary + recent turns."""
from __future__ import annotations

from dataclasses import dataclass, field

from .llm import LLM
from .prompts import SUMMARIZE


def token_len(text: str) -> int:
    """Rough token estimate (≈ 4 chars/token). Good enough for budgeting."""
    return max(1, len(text) // 4)


@dataclass
class Turn:
    role: str
    content: str


@dataclass
class Session:
    llm: LLM
    facts: dict = field(default_factory=dict)        # app-owned typed state
    summary: str = ""                                 # model-written, bounded
    recent: list[Turn] = field(default_factory=list)  # verbatim tail
    budget_tokens: int = 1500
    keep_recent: int = 4

    def add(self, role: str, content: str) -> None:
        self.recent.append(Turn(role, content))
        if token_len(self.render_recent()) > self.budget_tokens:
            self.compact()

    def compact(self) -> None:
        old, self.recent = self.recent[:-self.keep_recent], self.recent[-self.keep_recent:]
        turns = "\n".join(f"{t.role}: {t.content}" for t in old)
        self.summary = self.llm.complete(SUMMARIZE.render_user(turns, prev=self.summary or "(none)"),
                                         system=SUMMARIZE.render_system())

    def render_recent(self) -> str:
        return "\n".join(f"{t.role}: {t.content}" for t in self.recent)

    def context(self) -> str:
        parts = []
        if self.facts:
            parts.append("Known facts: " + ", ".join(f"{k}={v}" for k, v in self.facts.items()))
        if self.summary:
            parts.append("Earlier in the conversation: " + self.summary)
        parts.append(self.render_recent())
        return "\n".join(parts)
