"""Lab 3 — Ground the assistant with retrieval (30 min).

Usage:
  python labs/lab3_rag.py index            # inspect chunks
  python labs/lab3_rag.py eval             # recall@5 for the current settings
  python labs/lab3_rag.py ask "question"   # answer with citations

Not a programmer? worksheets/lab3.md does the same lab, and
`python run.py ask` / `run.py find` show retrieval without any editing.
"""
import sys

from _common import banner, get_llm, trace

from scaffold.prompts import ANSWER_WITH_SOURCES
from scaffold.rag import build_index, chunk_by_section, chunk_fixed, render_context, retrieval_eval

# ---------------------------------------------------------------------------
# TODO 1: start with chunk_fixed + mode="keyword"; run `eval`; write down recall@5.
# TODO 2: switch CHUNKER to chunk_by_section; re-run. Did recall move? Why?
# TODO 3: switch MODE to "hybrid"; re-run. Which misses disappeared?
# TODO 4: try FILTERS={"type": "label"} for a label question — what changes?
# ---------------------------------------------------------------------------
CHUNKER = chunk_fixed          # or chunk_by_section
MODE = "keyword"               # "keyword" | "dense" | "hybrid"
K = 5
FILTERS = None                 # e.g. {"type": "label"}


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "eval"
    index = build_index(CHUNKER)
    banner(f"Lab 3 — retrieval  chunker={CHUNKER.__name__} mode={MODE} k={K}")
    if cmd == "index":
        for c in index.chunks[:12]:
            print(f"\n[{c.id}] section='{c.section}' len={len(c.text)}\n{c.text[:160]}…")
        print(f"\n{len(index.chunks)} chunks total")
    elif cmd == "eval":
        r = retrieval_eval(index, k=K, mode=MODE, filters=FILTERS)
        print(r)
    elif cmd == "ask":
        q = " ".join(sys.argv[2:]) or "What is the re-entry interval for Product X?"
        llm = get_llm()
        trace.reset()
        chunks = index.search(q, k=K, mode=MODE, filters=FILTERS)
        ans = llm.complete(ANSWER_WITH_SOURCES.render_user(q, context=render_context(chunks)),
                           system=ANSWER_WITH_SOURCES.render_system(), tier="large")
        print(ans)
        trace.print_last()


if __name__ == "__main__":
    main()
