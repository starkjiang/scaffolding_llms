"""Tool registry (Part 4): schemas from type hints + docstrings, approval gates."""
from __future__ import annotations

import ast
import inspect
import json
import operator
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, get_type_hints

from .tracing import trace

from .domains import ROOT, data_dir  # noqa: E402

_PY2JSON = {str: "string", int: "integer", float: "number", bool: "boolean", dict: "object", list: "array"}


class ApprovalRequired(Exception):
    """Raised by write tools when a human must approve before execution."""

    def __init__(self, proposal: dict):
        super().__init__("approval required")
        self.proposal = proposal


@dataclass
class Tool:
    name: str
    fn: Callable
    description: str
    parameters: dict
    write: bool = False            # side effects → needs approval unless auto_approve

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description, "parameters": self.parameters}


@dataclass
class Registry:
    tools: dict[str, Tool] = field(default_factory=dict)
    auto_approve: bool = False
    approvals: list[dict] = field(default_factory=list)   # queue of proposed writes

    def tool(self, write: bool = False):
        """Decorator: register a function. Docstring → description; hints → schema."""

        def deco(fn: Callable) -> Callable:
            hints = get_type_hints(fn)
            sig = inspect.signature(fn)
            doc = inspect.getdoc(fn) or ""
            arg_docs = dict(re.findall(r"^\s*(\w+):\s*(.+)$", doc.split("Args:")[-1], re.M)) if "Args:" in doc else {}
            props = {}
            for p in sig.parameters.values():
                t = hints.get(p.name, str)
                props[p.name] = {"type": _PY2JSON.get(t, "string"), "description": arg_docs.get(p.name, "")}
            required = [p.name for p in sig.parameters.values() if p.default is inspect._empty]
            self.tools[fn.__name__] = Tool(fn.__name__, fn, doc.split("Args:")[0].strip(),
                                           {"type": "object", "properties": props, "required": required}, write)
            return fn
        return deco

    def schemas(self, names: list[str] | None = None) -> list[dict]:
        return [t.schema() for n, t in self.tools.items() if names is None or n in names]

    def call(self, name: str, args: dict) -> Any:
        t = self.tools[name]
        with trace.span("tool", tool=name, write=t.write) as sp:
            sp.log(args=args)
            if t.write and not self.auto_approve:
                proposal = {"tool": name, "args": args}
                self.approvals.append(proposal)
                sp.log(queued_for_approval=True)
                return {"status": "pending_approval", "proposal": proposal,
                        "message": "This action requires human approval and has been queued."}
            try:
                result = t.fn(**args)
            except Exception as e:  # tool errors go back to the model as data
                result = {"error": f"{type(e).__name__}: {e}"}
            sp.log(result=str(result)[:200])
            return result


# --- built-in tools used by the labs ---------------------------------------
registry = Registry()

_ALLOWED_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("unsupported expression")


@registry.tool()
def calculate(expression: str) -> dict:
    """Evaluate an arithmetic expression exactly. Use this for any rate, quantity, or unit
    conversion arithmetic instead of estimating. Supports + - * / ** and parentheses only.

    Args:
        expression: arithmetic expression, e.g. "137 * 2.5 / 320"
    """
    value = _safe_eval(ast.parse(expression, mode="eval").body)
    return {"expression": expression, "value": value}


@registry.tool()
def lookup_label_rate(product: str, crop: str) -> dict:
    """Return the labeled application rate and intervals for a crop-protection product on a crop.
    Use this whenever a user asks for a rate, dose, PHI, or REI. Do NOT estimate rates yourself.

    Args:
        product: product name as printed on the label, e.g. "Product X"
        crop: crop name in lowercase, e.g. "corn", "soybean", "wheat"
    """
    labels = json.loads((ROOT / "data" / "labels.json").read_text())
    prod = labels.get(product.title()) or labels.get(product)
    if not prod:
        raise KeyError(f"no label on file for product '{product}'")
    entry = prod.get(crop.lower())
    if not entry:
        raise KeyError(f"'{product}' is not labeled for crop '{crop}'; labeled crops: {list(prod)}")
    return entry


@registry.tool()
def search_manual(query: str) -> dict:
    """Search the equipment manuals, labels, and policies and return the top matching passages.
    Use this before answering any question about diagnostic codes, procedures, or parts.

    Args:
        query: short search query, e.g. "E212 hydraulic pressure"
    """
    from .rag import build_index  # lazy to avoid import cycle at module load

    global _INDEX
    try:
        _INDEX
    except NameError:
        _INDEX = build_index()
    chunks = _INDEX.search(query, k=3)
    return {"passages": [{"id": c.id, "text": c.text[:500]} for c in chunks]}


@registry.tool(write=True)
def create_work_order(machine: str, issue: str, priority: str = "normal") -> dict:
    """Create a service work order in the dealer system. This is a WRITE action: it will be
    queued for human approval. Only propose it when a documented procedure did not resolve the
    issue or the manual says to contact dealer service.

    Args:
        machine: machine model and/or serial, e.g. "HX-900"
        issue: short description including the diagnostic code
        priority: one of "low", "normal", "high"
    """
    return {"status": "created", "work_order_id": "WO-DEMO-0001", "machine": machine,
            "issue": issue, "priority": priority}


# --- the office example's tools --------------------------------------------
@registry.tool()
def lookup_expense_limit(category: str, city_tier: str = "tier2") -> dict:
    """Return the company spending limit for an expense category. Use this whenever
    someone asks what they are allowed to spend, or whether an amount is within policy.
    Do NOT quote a limit from memory.

    Args:
        category: one of "meals", "lodging", "home_office", "mileage", "phone_stipend"
        city_tier: "tier1" (New York, San Francisco, London), "tier2" (Chicago, Boston,
            Austin, Toronto) or "tier3" (everywhere else). Ignored for categories that
            do not vary by city.
    """
    limits = json.loads((ROOT / "data" / "office" / "limits.json").read_text())
    entry = limits.get(category.lower())
    if entry is None:
        raise KeyError(f"no documented limit for '{category}'; known: {list(limits)}")
    if city_tier.lower() in entry:
        return entry[city_tier.lower()]
    if any(k.startswith("tier") for k in entry):
        raise KeyError(f"'{category}' varies by city tier; pass tier1, tier2 or tier3")
    return entry


@registry.tool(write=True)
def request_expense_exception(claim_id: str, amount_usd: float, reason: str) -> dict:
    """Ask for a policy exception on an expense claim that is over a documented limit.
    This is a WRITE action: it will be queued for human approval. Only propose it when the
    claim is genuinely over a limit and the employee has given a reason. You may never
    approve an exception yourself.

    Args:
        claim_id: the claim reference, e.g. "C-003"
        amount_usd: the amount claimed, as a number
        reason: the employee's stated reason, in one short sentence
    """
    return {"status": "created", "exception_id": "EX-DEMO-0001", "claim_id": claim_id,
            "amount_usd": amount_usd, "reason": reason}


# which tools belong to which worked example
DOMAIN_TOOLS = {
    "ag": ["calculate", "lookup_label_rate", "search_manual", "create_work_order"],
    "office": ["calculate", "lookup_expense_limit", "search_manual", "request_expense_exception"],
}


def tools_for(domain: str | None = None) -> list[str]:
    """Tool names appropriate to one worked example."""
    from .domains import current

    return DOMAIN_TOOLS.get(domain or current(), DOMAIN_TOOLS["ag"])
