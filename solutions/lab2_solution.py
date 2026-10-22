"""Lab 2 solution — support chain with deterministic and model gates."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scaffold import get_llm, trace  # noqa: E402
from scaffold.evals import judge  # noqa: E402
from scaffold.prompts import REPLY, TRIAGE  # noqa: E402
from scaffold.structured import Triage, structured_call  # noqa: E402
from scaffold.workflow import Escalate, Outcome, chain  # noqa: E402

llm = get_llm()
KNOWN = json.loads((ROOT / "data" / "known_issues.json").read_text())
FORBIDDEN = re.compile(r"warrant|\$|price|cost|deliver|lead time", re.I)


def extract(ticket: dict) -> dict:
    rec = structured_call(llm, TRIAGE, ticket["text"], Triage)
    return {"ticket": ticket, "triage": rec}


def gate_known_issue(state: dict) -> dict:
    t: Triage = state["triage"]
    if t.needs_human:
        raise Escalate("ticket flagged needs_human (warranty/pricing/injection/unknown)", {"triage": t.model_dump()})
    if t.urgency >= 4:
        raise Escalate("safety-level urgency", {"triage": t.model_dump()})
    if not t.error_code:
        raise Escalate("no diagnostic code; route to agronomy/other branch", {"triage": t.model_dump()})
    issue = KNOWN.get(t.error_code)
    if issue is None:
        raise Escalate(f"unknown error code {t.error_code}", {"triage": t.model_dump()})
    state["issue"] = issue
    return state


def draft_reply(state: dict) -> dict:
    issue, t = state["issue"], state["triage"]
    article = f"{issue['title']} ({issue['doc']} §{issue['section']}): {issue['article']}"
    state["article"] = article
    state["reply"] = llm.complete(REPLY.render_user(state["ticket"]["text"], triage=t.model_dump_json(), article=article),
                                  system=REPLY.render_system(), tier="large")
    return state


def gate_policy(state: dict) -> Outcome:
    reply = state["reply"]
    if FORBIDDEN.search(reply):
        raise Escalate("policy: forbidden phrase in draft", {"draft": reply})
    if state["issue"].get("safety") and "stop" not in reply.lower():
        raise Escalate("policy: safety code reply must instruct operator to stop", {"draft": reply})
    verdict = judge(llm, reply, state["article"], state["ticket"]["text"])
    if verdict.get("safe", 2) < 2:
        raise Escalate(f"judge flagged reply: {verdict.get('notes')}", {"draft": reply, "judge": verdict})
    return Outcome("reply", text=reply, data={"judge": verdict, "article": state["article"]})


handle = chain(extract, gate_known_issue, draft_reply, gate_policy, name="support_chain")


def handle_with_trace(ticket: dict):
    """Return (outcome, triage, article) so evals can check fields."""
    trace.reset()
    state: dict = {}
    triage = article = None
    try:
        state = extract(ticket)
        triage = state["triage"]
        state = gate_known_issue(state)
        state = draft_reply(state)
        article = state["article"]
        out = gate_policy(state)
    except Escalate as e:
        out = Outcome("escalate", reason=e.reason, data=e.data)
        out.text = f"Escalated to a human technician: {e.reason}"
        if triage is not None and triage.urgency >= 4:
            # deterministic safety message — never depends on the model
            out.text = "SAFETY: stop operation immediately and do not restart until a technician has inspected the machine.\n" + out.text
        article = state.get("article")
    return out, triage, article


if __name__ == "__main__":
    from labs._common import load_jsonl

    for t in load_jsonl("tickets.jsonl"):
        out = handle(t)
        print(f"\n--- {t['id']} ---\n{out}")
        trace.print_last()
