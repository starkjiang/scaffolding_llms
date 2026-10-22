"""Lab 3 solution — compare chunkers and search modes side by side."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scaffold.rag import build_index, chunk_by_section, chunk_fixed, retrieval_eval  # noqa: E402

if __name__ == "__main__":
    for chunker in (chunk_fixed, chunk_by_section):
        index = build_index(chunker)
        for mode in ("keyword", "dense", "hybrid"):
            r = retrieval_eval(index, k=5, mode=mode)
            print(f"{chunker.__name__:<18} {mode:<8} recall@5={r['recall@k']:.2f} mrr={r['mrr']:.2f} misses={r['misses']}")
