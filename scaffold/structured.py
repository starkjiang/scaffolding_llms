"""Schema-validated model calls with feedback-on-retry (Part 1)."""
from __future__ import annotations

import json
import re
from typing import TypeVar

from pydantic import BaseModel, Field, ValidationError

from .llm import LLM
from .prompts import Prompt
from .tracing import trace

T = TypeVar("T", bound=BaseModel)


class Triage(BaseModel):
    """The ag example: a dealer support ticket."""

    machine_model: str | None = None
    error_code: str | None = None
    summary: str = Field(max_length=240)
    urgency: int = Field(ge=1, le=4)
    needs_human: bool


class Claim(BaseModel):
    """The office example: an expense claim. Same shape, different subject."""

    category: str | None = None          # MEALS | LODGING | TRAVEL | EQUIP | OTHER
    amount_usd: float | None = None
    summary: str = Field(max_length=240)
    risk: int = Field(ge=1, le=4)        # 1 routine … 4 possible policy violation
    needs_human: bool


def extract_json(text: str) -> str:
    """Pull the first {...} block out of a model reply (handles ``` fences)."""
    text = re.sub(r"```(?:json)?", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object found in model output")
    return m.group(0)


def structured_call(llm: LLM, prompt: Prompt, user_input: str, schema: type[T],
                    retries: int = 2, tier: str = "small", **kw) -> T:
    """Call the model, validate against `schema`, retry with the error as feedback."""
    user = prompt.render_user(user_input, **kw)
    with trace.span("structured_call", prompt=f"{prompt.name}@{prompt.version}", schema=schema.__name__) as sp:
        for attempt in range(retries + 1):
            raw = llm.complete(user, system=prompt.render_system(), tier=tier)
            try:
                obj = schema.model_validate_json(extract_json(raw))
                sp.log(attempts=attempt + 1)
                return obj
            except (ValidationError, ValueError) as e:
                sp.log(**{f"error_{attempt}": str(e)[:200]})
                user += (f"\n\nYour previous output was invalid:\n{e}\n"
                         f"Return corrected JSON only, matching the schema exactly.")
        raise RuntimeError(f"{prompt.name}: output failed validation after {retries + 1} attempts")


def json_call(llm: LLM, prompt: Prompt, user_input: str, tier: str = "small", **kw) -> dict:
    """Loosely typed variant: returns a dict, raises if no JSON."""
    raw = llm.complete(prompt.render_user(user_input, **kw), system=prompt.render_system(), tier=tier)
    return json.loads(extract_json(raw))
