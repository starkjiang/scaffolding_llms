"""Capstone — the full assistant: route → chain / RAG / tools → evals.

    python capstone.py            # run the ten tickets through the routed assistant
    python capstone.py eval       # run the eval set against it
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from labs._common import banner, load_jsonl  # noqa: E402
from scaffold import get_llm, trace  # noqa: E402
from scaffold.agent import run_agent  # noqa: E402
from scaffold.evals import print_summary, run_eval  # noqa: E402
from scaffold.prompts import ANSWER_WITH_SOURCES, CLASSIFY  # noqa: E402
from scaffold.rag import build_index, render_context  # noqa: E402
from scaffold.tools import registry  # noqa: E402
from scaffold.workflow import Outcome, route  # noqa: E402
from solutions.lab2_solution import handle_with_trace  # noqa: E402

llm = get_llm()
INDEX = build_index()


def classify(ticket: dict) -> str:
    raw = llm.complete(CLASSIFY.render_user(f'Request: "{ticket["text"]}"'), system=CLASSIFY.render_system())
    label = raw.strip().split(":")[-1].strip().upper()
    return label if label in BRANCHES else "OTHER"


def troubleshoot(ticket: dict) -> Outcome:
    out, _, _ = handle_with_trace(ticket)
    return out


def rag_answer(ticket: dict) -> Outcome:
    chunks = INDEX.search(ticket["text"], k=5, mode="hybrid")
    ans = llm.complete(ANSWER_WITH_SOURCES.render_user(ticket["text"], context=render_context(chunks)),
                       system=ANSWER_WITH_SOURCES.render_system(), tier="large")
    return Outcome("reply", text=ans, data={"sources": [c.id for c in chunks]})


def regulatory(ticket: dict) -> Outcome:
    res = run_agent(llm, registry, ticket["text"], tool_names=["lookup_label_rate", "calculate"], max_steps=5)
    return Outcome("reply", text=res.text, data={"stopped": res.stopped_reason})


def parts(ticket: dict) -> Outcome:
    return Outcome("escalate", reason="parts & pricing are handled by the parts desk (policy #2)")


def other(ticket: dict) -> Outcome:
    return Outcome("escalate", reason="out of scope for the assistant")


BRANCHES = {"TROUBLESHOOT": troubleshoot, "AGRONOMY": rag_answer, "REGULATORY": regulatory,
            "PARTS": parts, "OTHER": other}
assistant = route(classify, BRANCHES, default="OTHER")


def system_fn(ticket: dict):
    trace.reset()
    out = assistant(ticket)
    triage = out.data.get("triage") if isinstance(out.data, dict) else None
    return triage, out.text, out.data.get("article") if isinstance(out.data, dict) else None


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "eval":
        banner("Capstone eval")
        print_summary(run_eval(system_fn, name="capstone"))
    else:
        banner(f"Capstone assistant  (provider: {llm.provider})")
        for t in load_jsonl("tickets.jsonl"):
            trace.reset()
            out = assistant(t)
            print(f"\n--- {t['id']}: {t['text'][:70]}…\n{out}")
            trace.print_last()
