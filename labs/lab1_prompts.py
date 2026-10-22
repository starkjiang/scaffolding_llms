"""Lab 1 — Write a prompt contract (25 min).

Goal: turn a vague triage prompt into a layered prompt with a JSON output
schema, then validate it against the tickets in data/tickets.jsonl.

Run:  python labs/lab1_prompts.py

Not a programmer? worksheets/lab1.md does the same lab with no code,
and `python run.py triage` runs your instruction from my_instruction.txt.
"""
from _common import banner, get_llm, load_jsonl, trace

from scaffold.prompts import Prompt
from scaffold.structured import Triage, structured_call

# ---------------------------------------------------------------------------
# TODO 1: fill in the three sections. Keep the system prompt stable; put the
#         procedure in `task`; describe the exact JSON in `output`.
#         Look at scaffold/prompts.py::TRIAGE only if you get stuck.
# ---------------------------------------------------------------------------
MY_TRIAGE = Prompt(
    name="my_triage", version="v1",
    system="You are a triage assistant for an equipment dealer support desk.",   # TODO: add refusal rules
    task="Extract a triage record from the support ticket.",                    # TODO: define urgency scale + needs_human rules
    output='Return ONLY JSON: {"machine_model": ..., "error_code": ..., "summary": ..., "urgency": ..., "needs_human": ...}',
    input_tag="ticket",
)

# TODO 2 (stretch): add two few-shot examples to MY_TRIAGE.examples and re-run.
#   MY_TRIAGE.examples = [("<ticket>...</ticket>", '{"machine_model": ...}'), ...]


def main() -> None:
    llm = get_llm()
    banner(f"Lab 1 — prompt contract  (provider: {llm.provider})")
    tickets = load_jsonl("tickets.jsonl")
    passed = 0
    for t in tickets:
        trace.reset()
        try:
            rec = structured_call(llm, MY_TRIAGE, t["text"], Triage)
            passed += 1
            print(f"✓ {t['id']}: code={rec.error_code} urgency={rec.urgency} human={rec.needs_human}")
        except Exception as e:
            print(f"✗ {t['id']}: {e}")
    print(f"\n{passed}/{len(tickets)} tickets produced a valid Triage record.")
    print("\nNow inspect T-003 (safety), T-007 (injection) and T-008 (unknown code):")
    print("  did urgency and needs_human come out the way the policy requires?")


if __name__ == "__main__":
    main()
