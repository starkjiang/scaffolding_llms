"""Lab 5 — Build the eval set and change one thing (25 min).

Goal: run the eval on your Lab 2 chain, record the baseline, change ONE
component, re-run, and explain the delta.

Run:  python labs/lab5_evals.py [name]

Not a programmer? worksheets/lab5.md does the same lab, and
`python run.py score` / `run.py compare` do the scoring for you.
"""
import sys

from _common import banner, get_llm

from scaffold.evals import print_summary, run_eval

# TODO 1: point this at YOUR chain from Lab 2 (or the solution).
from solutions.lab2_solution import handle_with_trace   # noqa: E402

# TODO 2: add at least two cases of your own to data/eval_cases.jsonl
#         (and matching tickets to data/tickets.jsonl).
# TODO 3: set USE_JUDGE=True and compare the failures the judge adds.
# TODO 4: change ONE thing (prompt wording, model tier, a gate) and re-run under a new name.
USE_JUDGE = False


def system_fn(ticket: dict):
    """Adapter: (triage_dict_or_None, output_text, article_or_None)."""
    out, triage, article = handle_with_trace(ticket)
    return (triage.model_dump() if triage else None), out.text, article


def main() -> None:
    name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    llm = get_llm()
    banner(f"Lab 5 — evals  (provider: {llm.provider})  run={name} judge={USE_JUDGE}")
    s = run_eval(system_fn, llm=llm, use_judge=USE_JUDGE, name=name)
    print_summary(s)
    print(f"\nFull report: reports/{name}.json")


if __name__ == "__main__":
    main()
