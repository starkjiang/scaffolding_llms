"""scaffold — minimal, readable building blocks for LLM scaffolding.

Modules map onto the workshop's pillars:
    prompts     — layered prompt templates          (Part 1)
    structured  — schema-validated outputs + retry  (Part 1)
    workflow    — chain / route / parallel / refine (Part 2)
    memory      — session state and summarization  (Part 3)
    rag         — chunking, indexing, hybrid search (Part 3)
    tools       — tool registry, schemas, approval  (Part 4)
    agent       — bounded agent loop                (Part 4)
    evals       — eval runner, checks, judge        (Part 5)
    tracing     — spans and cost/latency logging    (Part 5)
    llm         — provider-agnostic client + mock
"""
from .llm import get_llm  # noqa: F401
from .tracing import trace  # noqa: F401
