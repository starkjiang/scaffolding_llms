"""Lab 2 solution, office example — the same chain, applied to expense claims.

Identical structure to lab2_solution.py. Only the subject matter changes:
    extract  ->  is the category covered by a documented policy?
             ->  draft a reply from that policy  ->  communication-policy gate
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("WORKSHOP_DOMAIN", "office")

from scaffold import get_llm, trace  # noqa: E402
from scaffold.domains import data_dir  # noqa: E402
from scaffold.evals import judge  # noqa: E402
from scaffold.prompts import REPLY_CLAIM, TRIAGE_CLAIM  # noqa: E402
from scaffold.structured import Claim, structured_call  # noqa: E402
from scaffold.workflow import Escalate, Outcome, chain  # noqa: E402

llm = get_llm()
POLICIES = json.loads((data_dir() / "known_issues.json").read_text())
# never tell someone their claim is approved, and never promise a payment date
FORBIDDEN = re.compile(r"approved|i approve|reimbursed tomorrow|will be paid|lands tomorrow"
                       r"|payment date|in your account", re.I)


def extract(ticket: dict) -> dict:
    rec = structured_call(llm, TRIAGE_CLAIM, ticket["text"], Claim)
    return {"ticket": ticket, "triage": rec}


def gate_documented_policy(state: dict) -> dict:
    t: Claim = state["triage"]
    if t.needs_human:
        raise Escalate("claim flagged needs_human (over limit, missing info, or an "
                       "instruction aimed at the assistant)", {"triage": t.model_dump()})
    if t.risk >= 3:
        raise Escalate("possible policy violation", {"triage": t.model_dump()})
    if not t.category:
        raise Escalate("no category; route to a person", {"triage": t.model_dump()})
    policy = POLICIES.get(t.category)
    if policy is None:
        raise Escalate(f"no documented policy for category {t.category}", {"triage": t.model_dump()})
    state["issue"] = policy
    return state


def draft_reply(state: dict) -> dict:
    issue, t = state["issue"], state["triage"]
    article = f"{issue['title']} ({issue['doc']} §{issue['section']}): {issue['article']}"
    state["article"] = article
    state["reply"] = llm.complete(
        REPLY_CLAIM.render_user(state["ticket"]["text"], triage=t.model_dump_json(), article=article),
        system=REPLY_CLAIM.render_system(), tier="large")
    return state


def gate_policy(state: dict) -> Outcome:
    reply = state["reply"]
    if FORBIDDEN.search(reply):
        raise Escalate("communication policy: reply approves a claim or promises a payment date",
                       {"draft": reply})
    verdict = judge(llm, reply, state["article"], state["ticket"]["text"])
    if verdict.get("safe", 2) < 2:
        raise Escalate(f"judge flagged reply: {verdict.get('notes')}", {"draft": reply, "judge": verdict})
    return Outcome("reply", text=reply, data={"judge": verdict, "article": state["article"]})


handle = chain(extract, gate_documented_policy, draft_reply, gate_policy, name="expense_chain")


def handle_with_trace(ticket: dict):
    """Return (outcome, triage, article) so the eval runner can check fields."""
    trace.reset()
    state: dict = {}
    triage = article = None
    try:
        state = extract(ticket)
        triage = state["triage"]
        state = gate_documented_policy(state)
        state = draft_reply(state)
        article = state["article"]
        out = gate_policy(state)
    except Escalate as e:
        out = Outcome("escalate", reason=e.reason, data=e.data)
        out.text = f"Sent to a person on the expense desk: {e.reason}"
        if triage is not None and triage.risk >= 4:
            out.text = ("POLICY: this looks like one purchase split across several claims, "
                        "which Finance reviews regardless of intent.\n") + out.text
        article = state.get("article")
    return out, triage, article


if __name__ == "__main__":
    from labs._common import load_jsonl

    for t in load_jsonl("office/tickets.jsonl"):
        out = handle(t)
        print(f"\n--- {t['id']} ---\n{out}")
