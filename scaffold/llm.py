"""Provider-agnostic LLM client.

One small abstraction so every lab works the same way against Anthropic, an
OpenAI-compatible endpoint, or an offline *mock* that needs no key.

    from scaffold.llm import get_llm
    llm = get_llm()
    text = llm.complete("Say hi", system="You are terse.")
    resp = llm.chat(messages, tools=[...])   # tool-calling form

The mock is deliberately simple: it uses keyword heuristics so the labs run
end-to-end without network access. It is NOT a stand-in for a real model —
switch providers to see real behaviour.
"""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any

from dotenv import load_dotenv

from .tracing import trace

load_dotenv()

Tier = str  # "small" | "large"


def _send_temperature(provider: str = "ANTHROPIC") -> bool:
    """Current models reject or restrict `temperature`. Opt in for pinned older models."""
    return os.getenv(f"{provider}_SEND_TEMPERATURE", "").strip().lower() in ("1", "true", "yes")


_warned: set[str] = set()


def _warn_once(message: str) -> None:
    if message not in _warned:
        _warned.add(message)
        print(f"  note: {message}", file=sys.stderr)


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class Response:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
    input_tokens: int = 0
    output_tokens: int = 0


class LLM:
    """Base interface. Subclasses implement `_chat`."""

    provider = "base"

    def __init__(self) -> None:
        self.models = {
            "small": os.getenv("LLM_MODEL_SMALL", "claude-haiku-5-5"),
            "large": os.getenv("LLM_MODEL_LARGE", "claude-sonnet-5-5"),
        }

    # -- public API ---------------------------------------------------------
    def complete(self, prompt: str, system: str = "", tier: Tier = "small",
                 temperature: float = 0.0, max_tokens: int = 1024) -> str:
        resp = self.chat([{"role": "user", "content": prompt}], system=system,
                         tier=tier, temperature=temperature, max_tokens=max_tokens)
        return resp.text

    def chat(self, messages: list[dict], system: str = "", tools: list[dict] | None = None,
             tier: Tier = "small", temperature: float = 0.0, max_tokens: int = 1024) -> Response:
        with trace.span("llm.chat", provider=self.provider, model=self.models[tier], tier=tier) as sp:
            resp = self._chat(messages, system, tools or [], self.models[tier], temperature, max_tokens)
            sp.log(input_tokens=resp.input_tokens, output_tokens=resp.output_tokens,
                   tool_calls=[t.name for t in resp.tool_calls], text=resp.text[:200])
            return resp

    def _chat(self, messages, system, tools, model, temperature, max_tokens) -> Response:  # pragma: no cover
        raise NotImplementedError


# --------------------------------------------------------------------------
# Anthropic
# --------------------------------------------------------------------------
class AnthropicLLM(LLM):
    provider = "anthropic"

    def __init__(self) -> None:
        super().__init__()
        import anthropic  # lazy import so the mock works without the SDK

        self.client = anthropic.Anthropic()

    def _chat(self, messages, system, tools, model, temperature, max_tokens) -> Response:
        kwargs: dict[str, Any] = dict(model=model, max_tokens=max_tokens, messages=messages)
        # temperature / top_p / top_k are DEPRECATED on Claude 4.7 and later. Sending a
        # non-default value returns a 400, and the Python SDK v1.0+ removed the argument
        # entirely, so passing it raises TypeError. We omit it and steer behaviour through
        # the prompt and the output schema instead — which is the subject of Part 1.
        # Set ANTHROPIC_SEND_TEMPERATURE=1 only if you have pinned a pre-4.7 model.
        if _send_temperature():
            kwargs["temperature"] = temperature
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [{"name": t["name"], "description": t["description"],
                                "input_schema": t["parameters"]} for t in tools]
        try:
            msg = self.client.messages.create(**kwargs)
        except TypeError as e:          # SDK v1.0+ removed the parameter
            if "temperature" not in str(e):
                raise
            kwargs.pop("temperature", None)
            msg = self.client.messages.create(**kwargs)
        text = "".join(b.text for b in msg.content if b.type == "text")
        calls = [ToolCall(b.id, b.name, b.input) for b in msg.content if b.type == "tool_use"]
        return Response(text, calls, raw=msg, input_tokens=msg.usage.input_tokens,
                        output_tokens=msg.usage.output_tokens)

    @staticmethod
    def tool_result_message(call: ToolCall, result: Any) -> dict:
        return {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id,
                                             "content": json.dumps(result, default=str)}]}

    @staticmethod
    def assistant_message(resp: Response) -> dict:
        return {"role": "assistant", "content": resp.raw.content}


# --------------------------------------------------------------------------
# OpenAI-compatible
# --------------------------------------------------------------------------
class OpenAILLM(LLM):
    provider = "openai"

    def __init__(self) -> None:
        super().__init__()
        from openai import OpenAI

        self.client = OpenAI()
        self.models = {"small": os.getenv("LLM_MODEL_SMALL", "gpt-6-luna"),
                       "large": os.getenv("LLM_MODEL_LARGE", "gpt-6.1-sol")}

    def _chat(self, messages, system, tools, model, temperature, max_tokens) -> Response:
        # Current OpenAI models require the RESPONSES API for tool calling — chat
        # completions returns a 400 for them. So anything with tools goes down the
        # responses path, and plain text calls stay on chat completions.
        if tools:
            return self._respond(messages, system, tools, model, temperature, max_tokens)

        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        # max_tokens is deprecated in favour of max_completion_tokens. temperature is
        # restricted on reasoning models, and reasoning_effort is only valid on some.
        # Rather than hard-coding a table of which model takes what — it changes every
        # few months — we send a sensible set and drop what the API objects to.
        kwargs: dict[str, Any] = dict(model=model, messages=msgs,
                                      max_completion_tokens=max_tokens)
        if _send_temperature("OPENAI"):
            kwargs["temperature"] = temperature
        effort = os.getenv("OPENAI_REASONING_EFFORT", "").strip().lower()
        if effort:
            kwargs["reasoning_effort"] = effort

        out = self._call(self.client.chat.completions.create, kwargs,
                         self._CHAT_OPTIONAL, {"max_completion_tokens": ("max_tokens", max_tokens)})
        m = out.choices[0].message
        calls = [ToolCall(tc.id, tc.function.name, json.loads(tc.function.arguments or "{}"))
                 for tc in (m.tool_calls or [])]
        return Response(m.content or "", calls, raw=m,
                        input_tokens=out.usage.prompt_tokens, output_tokens=out.usage.completion_tokens)

    def _respond(self, messages, system, tools, model, temperature, max_tokens) -> Response:
        """The Responses API path: tools are flat, instructions carry the system prompt."""
        kwargs: dict[str, Any] = dict(
            model=model, input=list(messages), max_output_tokens=max_tokens,
            tools=[{"type": "function", "name": t["name"], "description": t["description"],
                    "parameters": t["parameters"]} for t in tools])
        if system:
            kwargs["instructions"] = system
        if _send_temperature("OPENAI"):
            kwargs["temperature"] = temperature
        effort = os.getenv("OPENAI_REASONING_EFFORT", "").strip().lower()
        if effort:
            kwargs["reasoning"] = {"effort": effort}

        out = self._call(self.client.responses.create, kwargs, self._RESP_OPTIONAL)
        items = list(getattr(out, "output", []) or [])
        calls = [ToolCall(it.call_id, it.name, json.loads(it.arguments or "{}"))
                 for it in items if getattr(it, "type", "") == "function_call"]
        usage = getattr(out, "usage", None)
        # Reasoning items must be handed back with the tool results, so keep every item.
        return Response(getattr(out, "output_text", "") or "", calls, raw=items,
                        input_tokens=getattr(usage, "input_tokens", 0) or 0,
                        output_tokens=getattr(usage, "output_tokens", 0) or 0)

    # Parameters OpenAI may reject depending on the model generation. Order matters:
    # the first one named in an error message is the one we drop.
    _CHAT_OPTIONAL = ("reasoning_effort", "temperature", "top_p", "max_completion_tokens")
    _RESP_OPTIONAL = ("reasoning", "temperature", "top_p", "max_output_tokens")

    def _call(self, create, kwargs: dict, optional: tuple, rename: dict | None = None):
        """Send the request, dropping any parameter this model will not accept.

        Model families differ on which sampling and length parameters they take, and
        the answer changes between generations. Rather than guessing, we let the API
        tell us: a 400 naming a parameter means drop it and try again.
        """
        last: Exception | None = None
        for _ in range(len(optional) + 1):
            try:
                return create(**kwargs)
            except TypeError as e:                       # SDK removed the argument
                last, dropped = e, self._drop(kwargs, str(e), optional)
            except Exception as e:                       # 400 naming a parameter
                last = e
                if getattr(e, "status_code", None) not in (400, 422):
                    raise
                dropped = self._drop(kwargs, str(e), optional)
            if not dropped:
                raise self._explain(last, kwargs) from last
            if rename and dropped in rename:             # older endpoints want the old name
                key, value = rename[dropped]
                kwargs[key] = value
        raise self._explain(last, kwargs) from last

    @staticmethod
    def _explain(error: Exception, kwargs: dict) -> Exception:
        """Turn a bare 400 into something a person can act on in a workshop."""
        sent = ", ".join(sorted(k for k in kwargs if k != "messages"))
        return RuntimeError(
            f"\n  The provider rejected this request and it is not a parameter this repo "
            f"knows how to drop.\n"
            f"    Model:      {kwargs.get('model')}\n"
            f"    Sent:       {sent}\n"
            f"    Provider:   {type(error).__name__}: {error}\n\n"
            f"  Most likely one of:\n"
            f"    - the model ID does not exist or is retired "
            f"(https://developers.openai.com/api/docs/models)\n"
            f"    - your key has no access to this model\n"
            f"    - this model wants a different endpoint than the one used here\n"
            f"      (tool calls go through the Responses API, plain text through chat\n"
            f"       completions — see scaffold/llm.py)\n\n"
            f"  Try a different model in .env, for example:\n"
            f"    LLM_MODEL_SMALL=gpt-6-luna      LLM_MODEL_LARGE=gpt-6.1-sol\n\n"
            f"  Or keep going offline — every lab works without a key:\n"
            f"    LLM_PROVIDER=mock python run.py demo\n"
            f"    (on Windows:  set LLM_PROVIDER=mock)\n")

    def _drop(self, kwargs: dict, message: str, optional: tuple) -> str | None:
        low = message.lower()
        for name in optional:
            if name in kwargs and name in low:
                kwargs.pop(name)
                _warn_once(f"this model does not accept '{name}' — dropping it and retrying. "
                           f"Set it in .env only if your model supports it.")
                return name
        return None

    # Tools go through the Responses API, so the turn-taking items are its shapes:
    # a function_call_output carries call_id, and the whole previous output (reasoning
    # items included) is handed back unchanged.
    @staticmethod
    def tool_result_message(call: ToolCall, result: Any) -> dict:
        return {"type": "function_call_output", "call_id": call.id,
                "output": json.dumps(result, default=str)}

    @staticmethod
    def assistant_message(resp: Response) -> list:
        return [it.model_dump(exclude_none=True) if hasattr(it, "model_dump") else it
                for it in (resp.raw or [])]


# --------------------------------------------------------------------------
# Offline mock — keyword heuristics so labs run without a key
# --------------------------------------------------------------------------
class MockLLM(LLM):
    provider = "mock"
    _counter = 0

    def __init__(self) -> None:
        super().__init__()
        self.models = {"small": "mock-small", "large": "mock-large"}

    def _chat(self, messages, system, tools, model, temperature, max_tokens) -> Response:
        last = messages[-1]
        content = last["content"] if isinstance(last["content"], str) else json.dumps(last["content"])
        blob = (system + "\n" + content)
        low = blob.lower()

        # --- tool calling: pick a tool by keyword, once ------------------
        if tools and last["role"] == "user" and isinstance(last["content"], str):
            call = self._pick_tool(content, tools)
            if call:
                return Response("", [call], raw={"mock": True})
        if last["role"] in ("user", "tool") and not isinstance(last.get("content"), str):
            return Response(self._summarize_tool_result(content), [], raw={"mock": True})

        # --- judge rubric -------------------------------------------------
        if "faithful" in low and "return json" in low:
            reply_m = re.search(r"<reply>\n?(.*?)\n?</reply>", blob, re.S)
            reply = reply_m.group(1).lower() if reply_m else ""
            # unsafe in either example: promising coverage/approval, quoting price, or a payment date
            safe = 0 if re.search(r"warrant|covered under|\bprice\b|\bapproved\b"
                                  r"|lands tomorrow|in your account|will be paid", reply) else 2
            return Response(json.dumps({"faithful": 2, "complete": 2 if "step" in reply or "check" in reply else 1,
                                        "safe": safe, "tone": 2, "notes": "mock judge"}), [], raw={"mock": True})

        # --- reply drafting from an article ------------------------------
        article = re.search(r"<article>\n?(.*?)\n?</article>", blob, re.S)
        if article and "reply" in low:
            body = article.group(1).strip()
            title = body.split("(")[0].strip() if "(" in body else "manual article"
            steps = body.split(":", 1)[-1].strip() if ":" in body else body
            pre = "Stop operation first. " if re.search(r"stop operation", body, re.I) else ""
            return Response(f"{pre}Per the documented procedure: {steps[:350]}\nReference: {title}", [],
                            raw={"mock": True})

        # --- structured triage JSON -------------------------------------
        if "needs_human" in low and ("<claim>" in blob or "amount_usd" in low):
            return Response(self._claim_json(content), [], raw={"mock": True})
        if "needs_human" in low:
            return Response(self._triage_json(content), [], raw={"mock": True})

        # --- classification / routing -----------------------------------
        if "label:" in low and "agronomy" in low:
            return Response(self._classify(content), [], raw={"mock": True})

        # --- summarization ---------------------------------------------
        if "summar" in low:
            return Response("Summary (mock): " + re.sub(r"\s+", " ", content)[:240], [], raw={"mock": True})

        # --- default: grounded-ish answer using any <context> provided ---
        ctx = re.search(r"<context>(.*?)</context>", blob, re.S)
        if ctx:
            first = [ln for ln in ctx.group(1).splitlines() if ln.strip()][:6]
            return Response("Based on the provided sources: " + " ".join(l.strip() for l in first)[:600]
                            + " [source: see retrieved chunks]", [], raw={"mock": True})
        return Response("(mock model) I do not have enough information to answer reliably; "
                        "please provide documents or escalate to a human.", [], raw={"mock": True})

    # -- helpers --------------------------------------------------------------
    def _triage_json(self, content: str) -> str:
        ticket_m = re.search(r".*<ticket>\s*(.*?)\s*</ticket>", content, re.S)
        t = (ticket_m.group(1) if ticket_m else content)
        code_m = re.search(r"\bE\d{3}\b", t)
        code = code_m.group(0) if code_m else None
        model_m = re.search(r"HX-?\d{3}", t, re.I)
        low = t.lower()
        urgency = 1
        if code in ("E212", "E305"):
            urgency = 2
        if code == "E410" or "smok" in low or "fire" in low:
            urgency = 4
        needs_human = bool(re.search(r"warrant|price|cost|override|admin|E999", t, re.I)) or code is None and "?" in t and "joke" not in low
        if code and code not in ("E212", "E305", "E410"):
            needs_human = True
        summary = re.sub(r"\s+", " ", t.strip())[:120]
        return json.dumps({"machine_model": model_m.group(0).upper().replace("HX", "HX-").replace("--", "-") if model_m else None,
                           "error_code": code, "summary": summary, "urgency": urgency,
                           "needs_human": needs_human})

    def _claim_json(self, content: str) -> str:
        m = re.search(r".*<claim>\s*(.*?)\s*</claim>", content, re.S)
        t = m.group(1) if m else content
        low = t.lower()
        amounts = [float(x) for x in re.findall(r"\$\s?(\d+(?:\.\d{1,2})?)", t)]
        amount = max(amounts) if amounts else None
        category = None
        if re.search(r"\b(dinner|lunch|meal|meals|breakfast|beer|coffee)\b", low):
            category = "MEALS"
        elif re.search(r"\b(laptop|desk|monitor|chair|footrest|handset|equipment)\b", low):
            category = "EQUIP"
        elif re.search(r"\b(hotel|lodging|per night|a night|nightly)\b", low):
            category = "LODGING"
        elif re.search(r"\b(mile|miles|mileage|taxi|rideshare|flight|train)\b", low):
            category = "TRAVEL"
        risk = 1
        if re.search(r"submitted separately|split", low):
            risk = 4
        elif amount and category == "LODGING" and amount > 320:
            risk = 3
        elif re.search(r"didn\u2019t ask|didn't ask|no receipt|not the names|lost the receipt", low):
            risk = 3
        elif amount:
            risk = 2
        needs_human = bool(
            risk >= 3
            or re.search(r"approve|override|admin mode|when will|arrive|not the names|split", low)
        )
        if re.search(r"coffee machine|floor 3", low):
            category, risk, needs_human = None, 1, False
        summary = re.sub(r"\s+", " ", t.strip())[:120]
        return json.dumps({"category": category, "amount_usd": amount, "summary": summary,
                           "risk": risk, "needs_human": needs_human})

    def _classify(self, content: str) -> str:
        q = content.lower().split("request:")[-1]
        if "joke" in q:
            return "OTHER"
        if re.search(r"\be\d{3}\b|code|alarm|feeder|hydraulic", q) and "troubleshoot" in content.lower():
            return "TROUBLESHOOT"
        if re.search(r"part number|filter|price|cost|order", q):
            return "PARTS"
        if re.search(r"interval|label|rate|harvest|re-entry|phi", q):
            return "REGULATORY"
        if re.search(r"rate|stage|aphid|spray|nitrogen|tank mix|v\d", q):
            return "AGRONOMY"
        return "OTHER"

    def _pick_tool(self, content: str, tools: list[dict]) -> ToolCall | None:
        MockLLM._counter += 1
        names = {t["name"] for t in tools}
        low = content.lower()
        if "request_expense_exception" in names and re.search(r"exception|over the limit|over limit|approve", low):
            return ToolCall(f"mock-{MockLLM._counter}", "request_expense_exception",
                            {"claim_id": "C-003", "amount_usd": 410.0,
                             "reason": "cheaper compliant options were sold out"})
        if "create_work_order" in names and re.search(r"work order|schedule|create", low):
            code = re.search(r"\bE\d{3}\b", content)
            return ToolCall(f"mock-{MockLLM._counter}", "create_work_order",
                            {"machine": "HX-900", "issue": code.group(0) if code else "unspecified",
                             "priority": "normal"})
        if "lookup_expense_limit" in names and re.search(r"limit|cap|allowed|spend|claim|expense|per mile|mileage|stipend", low):
            cat = ("meals" if re.search(r"dinner|lunch|meal|breakfast", low) else
                   "lodging" if re.search(r"hotel|night|lodging", low) else
                   "mileage" if re.search(r"mile", low) else
                   "home_office" if re.search(r"desk|chair|home office|monitor", low) else
                   "phone_stipend" if re.search(r"phone|stipend", low) else None)
            if cat:
                tier = ("tier1" if re.search(r"new york|san francisco|london", low) else
                        "tier3" if re.search(r"tier 3|elsewhere", low) else "tier2")
                return ToolCall(f"mock-{MockLLM._counter}", "lookup_expense_limit",
                                {"category": cat, "city_tier": tier})
        if "lookup_label_rate" in names and re.search(r"rate|harvest|interval|phi", low):
            prod = re.search(r"product [xy]", low)
            crop = re.search(r"corn|soybean|wheat", low)
            if prod and crop:
                return ToolCall(f"mock-{MockLLM._counter}", "lookup_label_rate",
                                {"product": prod.group(0).title(), "crop": crop.group(0)})
        if "calculate" in names and re.search(r"how many|jug|total|acres", low):
            nums = re.findall(r"\d+(?:\.\d+)?", low)
            if len(nums) >= 2:
                return ToolCall(f"mock-{MockLLM._counter}", "calculate",
                                {"expression": f"{nums[0]} * {nums[1]}"})
        if "search_manual" in names and re.search(r"\bE\d{3}\b|code|manual", content):
            return ToolCall(f"mock-{MockLLM._counter}", "search_manual", {"query": content[:80]})
        return None

    def _summarize_tool_result(self, content: str) -> str:
        try:
            blocks = json.loads(content)
            inner = json.loads(blocks[0]["content"])
        except Exception:
            return "Tool result received (mock): " + content[:300]
        if "error" in inner:
            return f"The tool reported an error: {inner['error']}. I cannot answer this reliably; please escalate."
        if "status" in inner and inner.get("status") == "pending_approval":
            what = inner["proposal"]["tool"].replace("_", " ")
            return (f"I have proposed to {what}; it is queued for human approval and has NOT "
                    f"been carried out: {inner['proposal']['args']}")
        if "passages" in inner:
            ids = ", ".join(p["id"] for p in inner["passages"])
            return f"According to the manual passages [{ids}], follow the documented procedure. (mock answer)"
        if "value" in inner:
            return f"Calculation: {inner['expression']} = {inner['value']} (via calculator tool)"
        pairs = ", ".join(f"{k}: {v}" for k, v in inner.items())
        return f"From the lookup — {pairs}"


# --------------------------------------------------------------------------
_KEY_FOR = {"anthropic": "ANTHROPIC_API_KEY", "openai": "OPENAI_API_KEY"}
_SDK_FOR = {"anthropic": "anthropic", "openai": "openai"}


def _bail(provider: str, problem: str, fix: str) -> None:
    """Fail with something a workshop participant can act on, not a traceback."""
    raise SystemExit(
        f"\n  Could not start the '{provider}' provider.\n"
        f"    Problem: {problem}\n"
        f"    Fix:     {fix}\n\n"
        f"  Or work offline for now — practice mode needs no key:\n"
        f"    LLM_PROVIDER=mock python run.py check\n"
        f"  (on Windows:  set LLM_PROVIDER=mock)\n"
    )


def get_llm() -> LLM:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if not provider:
        provider = "anthropic" if os.getenv("ANTHROPIC_API_KEY") else \
                   "openai" if os.getenv("OPENAI_API_KEY") else "mock"
    if provider == "mock":
        return MockLLM()
    if provider not in _KEY_FOR:
        _bail(provider, f"'{provider}' is not a provider this repo knows about.",
              "Set LLM_PROVIDER to anthropic, openai, or mock in your .env file.")

    key = os.getenv(_KEY_FOR[provider], "").strip()
    if not key:
        _bail(provider, f"{_KEY_FOR[provider]} is not set (or is empty).",
              f"Copy .env.example to .env and put your key on the {_KEY_FOR[provider]} line. "
              f"No quotes, no spaces around the '='.")
    try:
        __import__(_SDK_FOR[provider])
    except ImportError:
        _bail(provider, f"the '{_SDK_FOR[provider]}' package is not installed.",
              "Activate your virtual environment, then run:  pip install -r requirements.txt")

    try:
        return AnthropicLLM() if provider == "anthropic" else OpenAILLM()
    except Exception as e:  # bad key format, proxy problems, SDK version mismatch
        _bail(provider, f"{type(e).__name__}: {e}",
              f"Check that {_KEY_FOR[provider]} is the full key and has not expired.")


def tool_result_message(llm: LLM, call: ToolCall, result: Any) -> dict:
    if isinstance(llm, MockLLM):
        return {"role": "user", "content": [{"type": "tool_result", "tool_use_id": call.id,
                                             "content": json.dumps(result, default=str)}]}
    return type(llm).tool_result_message(call, result)


def assistant_message(llm: LLM, resp: Response) -> dict:
    if isinstance(llm, MockLLM):
        return {"role": "assistant", "content": [{"type": "tool_use", "id": c.id, "name": c.name,
                                                  "input": c.input} for c in resp.tool_calls]
                or resp.text}
    return type(llm).assistant_message(resp)
