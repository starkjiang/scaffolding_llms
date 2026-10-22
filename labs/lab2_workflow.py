"""Lab 2 — Build a chain with gates (30 min).

Goal: extract → known-issue gate → draft reply → policy gate, with escalation
as a first-class outcome.

Run:  python labs/lab2_workflow.py

Not a programmer? worksheets/lab2.md does the same lab on paper.
"""
import json
import re

from _common import DATA, banner, get_llm, load_jsonl, trace

from scaffold.prompts import REPLY, TRIAGE
from scaffold.structured import Triage, structured_call
from scaffold.workflow import Escalate, Outcome, chain

llm = get_llm()
KNOWN = json.loads((DATA / "known_issues.json").read_text())
FORBIDDEN = re.compile(r"warrant|\$|price|cost|deliver|lead time", re.I)


def extract(ticket: dict) -> dict:
    rec = structured_call(llm, TRIAGE, ticket["text"], Triage)
    return {"ticket": ticket, "triage": rec}


def gate_known_issue(state: dict) -> dict:
    """TODO 1: escalate when needs_human, urgency>=4, or the code is not in KNOWN.
    Attach KNOWN[code] to state["issue"] otherwise."""
    t: Triage = state["triage"]
    # ---- your code here ----
    raise NotImplementedError("gate_known_issue")


def draft_reply(state: dict) -> dict:
    """TODO 2: call the model with REPLY, passing triage + article, and store state["reply"]."""
    # hint: REPLY.render_user(ticket_text, triage=..., article=...)
    raise NotImplementedError("draft_reply")


def gate_policy(state: dict) -> Outcome:
    """TODO 3: reject replies matching FORBIDDEN (escalate with the draft attached);
    otherwise return Outcome('reply', text=...). Stretch: add a model judge (scaffold.evals.judge)."""
    raise NotImplementedError("gate_policy")


handle = chain(extract, gate_known_issue, draft_reply, gate_policy, name="support_chain")


def main() -> None:
    banner(f"Lab 2 — chain with gates  (provider: {llm.provider})")
    for t in load_jsonl("tickets.jsonl"):
        trace.reset()
        out = handle(t)
        print(f"\n--- {t['id']} ---\n{out}")
        trace.print_last()


if __name__ == "__main__":
    main()
