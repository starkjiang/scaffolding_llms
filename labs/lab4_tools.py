"""Lab 4 — Give the assistant a tool (25 min).

Goal: register a label-rate lookup and a calculator, let the model decide when
to call them, and add an approval gate for a write action.

Run:  python labs/lab4_tools.py

Not a programmer? worksheets/lab4.md does the same lab, and
`python run.py tools "..."` shows tool use without any editing.
"""
from _common import banner, get_llm, trace

from scaffold.agent import run_agent
from scaffold.tools import Registry

llm = get_llm()
reg = Registry()          # start from an EMPTY registry — you register the tools


# ---------------------------------------------------------------------------
# TODO 1: implement and register lookup_label_rate. The docstring is the part
#         the model reads — say when to use it and what the args mean.
#         data/labels.json has the data (see scaffold/tools.py for a reference).
# ---------------------------------------------------------------------------
@reg.tool()
def lookup_label_rate(product: str, crop: str) -> dict:
    """TODO: write a description the model can act on.

    Args:
        product: TODO
        crop: TODO
    """
    raise NotImplementedError


# TODO 2: register a calculate(expression: str) tool (copy the safe evaluator
#         from scaffold/tools.py or import it).

# TODO 3: register create_work_order(machine, issue, priority) with write=True
#         and observe that the agent's call is queued, not executed.

QUESTIONS = [
    "What is the labeled rate of Product X on soybeans, and what is the PHI?",
    "How many 2.5-gallon jugs of Product X do I need for 137 acres of corn?",
    "Is Product Y labeled for wheat?",
    # TODO 3b: "The manual says E212 needs a dealer pump inspection. Create a work order for HX-900."
]


def main() -> None:
    banner(f"Lab 4 — tools  (provider: {llm.provider})  tools={list(reg.tools)}")
    for q in QUESTIONS:
        trace.reset()
        res = run_agent(llm, reg, q, max_steps=6)
        print(f"\nQ: {q}\nA: {res.text}\n   steps={res.steps} stopped={res.stopped_reason} "
              f"pending_approvals={res.pending_approvals}")
        trace.print_last()


if __name__ == "__main__":
    main()
