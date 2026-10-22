"""Lab 4 solution — the built-in registry already has all four tools."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scaffold import get_llm, trace  # noqa: E402
from scaffold.agent import run_agent  # noqa: E402
from scaffold.tools import registry  # noqa: E402

QUESTIONS = [
    "What is the labeled rate of Product X on soybeans, and what is the PHI?",
    "How many 2.5-gallon jugs of Product X do I need for 137 acres of corn?",
    "The manual says E212 needs a dealer pump inspection. Create a work order for HX-900.",
]

if __name__ == "__main__":
    llm = get_llm()
    for q in QUESTIONS:
        trace.reset()
        res = run_agent(llm, registry, q, tool_names=["lookup_label_rate", "calculate", "search_manual", "create_work_order"])
        print(f"\nQ: {q}\nA: {res.text}\n   stopped={res.stopped_reason} pending={res.pending_approvals}")
        trace.print_last()
    if registry.approvals:
        print("\nPending approvals (a human must review these):")
        for p in registry.approvals:
            print("  ", p)
