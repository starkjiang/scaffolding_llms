"""Lab 5 solution — baseline vs. one change (judge on), printed side by side."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scaffold import get_llm  # noqa: E402
from scaffold.evals import print_summary, run_eval  # noqa: E402
from solutions.lab2_solution import handle_with_trace  # noqa: E402


def system_fn(ticket):
    out, triage, article = handle_with_trace(ticket)
    return (triage.model_dump() if triage else None), out.text, article


if __name__ == "__main__":
    llm = get_llm()
    print_summary(run_eval(system_fn, name="baseline"))
    print_summary(run_eval(system_fn, llm=llm, use_judge=True, name="with_judge"))
