"""Retrieval (Part 3): load docs, chunk, index, hybrid search, retrieval eval.

Offline-friendly: keyword search uses BM25; the "dense" side uses a cheap
hashed bag-of-words embedding so the hybrid path runs without a provider.
Swap `embed()` for a real embedding model in production.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from .tracing import trace

from .domains import data_dir  # noqa: E402


@dataclass
class Doc:
    id: str
    meta: dict
    text: str


@dataclass
class Chunk:
    id: str          # "<doc>#<n>"
    doc: str
    section: str
    text: str
    meta: dict = field(default_factory=dict)


# --- loading --------------------------------------------------------------
def load_docs(folder: Path | None = None) -> list[Doc]:
    folder = folder or data_dir() / "docs"
    docs = []
    for p in sorted(folder.glob("*.md")):
        raw = p.read_text(encoding="utf-8")
        meta: dict = {}
        if raw.startswith("---"):
            head, _, raw = raw[3:].partition("\n---\n")
            for line in head.strip().splitlines():
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip()
        docs.append(Doc(meta.get("doc", p.stem), meta, raw.strip()))
    return docs


# --- chunking ---------------------------------------------------------------
def chunk_fixed(doc: Doc, size: int = 400, overlap: int = 60) -> list[Chunk]:
    """Character-based fixed-size chunks with overlap. Simple; breaks tables."""
    out, i, n = [], 0, 0
    while i < len(doc.text):
        out.append(Chunk(f"{doc.id}#{n}", doc.id, "", doc.text[i:i + size], doc.meta))
        i += size - overlap
        n += 1
    return out


def chunk_by_section(doc: Doc, max_chars: int = 900) -> list[Chunk]:
    """Split on markdown headings; keep each section intact; prefix with its title."""
    out, n = [], 0
    parts = re.split(r"\n(?=#{1,3} )", doc.text)
    for part in parts:
        title_m = re.match(r"#{1,3} (.*)", part)
        title = title_m.group(1).strip() if title_m else ""
        body = part.strip()
        # enrich: put doc + section title in the chunk text so both search and model see it
        text = f"[{doc.id} · {title}]\n{body}" if title else body
        for j in range(0, len(text), max_chars):
            out.append(Chunk(f"{doc.id}#{n}", doc.id, title, text[j:j + max_chars], doc.meta))
            n += 1
    return out


# --- embeddings (offline stand-in) ----------------------------------------------
_DIM = 512


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9\-\.]*", text.lower())


def embed(text: str) -> np.ndarray:
    """Hashed bag-of-words with bigrams — replace with a real embedding model."""
    v = np.zeros(_DIM)
    toks = tokenize(text)
    for t in toks + [a + "_" + b for a, b in zip(toks, toks[1:])]:
        h = int(hashlib.md5(t.encode()).hexdigest(), 16)
        v[h % _DIM] += 1.0 if "_" not in t else 0.5
    n = np.linalg.norm(v)
    return v / n if n else v


# --- index --------------------------------------------------------------
class Index:
    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        self.bm25 = BM25Okapi([tokenize(c.text) for c in chunks])
        self.vecs = np.stack([embed(c.text) for c in chunks]) if chunks else np.zeros((0, _DIM))

    def keyword(self, q: str, k: int) -> list[tuple[int, float]]:
        scores = self.bm25.get_scores(tokenize(q))
        idx = np.argsort(-scores)[:k]
        return [(int(i), float(scores[i])) for i in idx if scores[i] > 0]

    def dense(self, q: str, k: int) -> list[tuple[int, float]]:
        sims = self.vecs @ embed(q)
        idx = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in idx if sims[i] > 0]

    def search(self, q: str, k: int = 5, mode: str = "hybrid", filters: dict | None = None,
               candidates: int = 20) -> list[Chunk]:
        """mode: 'keyword' | 'dense' | 'hybrid' (reciprocal-rank fusion)."""
        with trace.span("retrieve", mode=mode, k=k) as sp:
            allowed = {i for i, c in enumerate(self.chunks)
                       if not filters or all(c.meta.get(f) == v for f, v in filters.items())}
            ranked: dict[int, float] = {}
            lists = []
            if mode in ("keyword", "hybrid"):
                lists.append(self.keyword(q, candidates))
            if mode in ("dense", "hybrid"):
                lists.append(self.dense(q, candidates))
            for lst in lists:
                for rank, (i, _) in enumerate(lst):
                    if i in allowed:
                        ranked[i] = ranked.get(i, 0.0) + 1.0 / (60 + rank)   # RRF
            top = sorted(ranked.items(), key=lambda t: -t[1])[:k]
            sp.log(hits=[self.chunks[i].id for i, _ in top])
            return [self.chunks[i] for i, _ in top]


def build_index(chunker=chunk_by_section, docs: list[Doc] | None = None, **kw) -> Index:
    docs = docs or load_docs()
    chunks = [c for d in docs for c in chunker(d, **kw)]
    return Index(chunks)


def render_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[{c.id}]\n{c.text}" for c in chunks)


# --- retrieval eval ----------------------------------------------------------
def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def retrieval_eval(index: Index, cases: list[dict] | None = None, k: int = 5, **search_kw) -> dict:
    cases = cases or load_jsonl(data_dir() / "eval_retrieval.jsonl")
    hits, rr, misses = 0, 0.0, []
    for case in cases:
        chunks = index.search(case["q"], k=k, **search_kw)
        docs = [c.doc for c in chunks]
        if case["expected_doc"] in docs:
            hits += 1
            rr += 1.0 / (docs.index(case["expected_doc"]) + 1)
        else:
            misses.append(case["q"])
    n = len(cases)
    return {"recall@k": round(hits / n, 3), "mrr": round(rr / n, 3), "k": k, "n": n, "misses": misses}
