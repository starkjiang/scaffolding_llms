"""Smoke tests — run in mock mode so CI needs no key: LLM_PROVIDER=mock pytest -q"""
import os
import sys
from pathlib import Path

os.environ["LLM_PROVIDER"] = "mock"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scaffold import get_llm  # noqa: E402
from scaffold.prompts import TRIAGE  # noqa: E402
from scaffold.rag import build_index, chunk_by_section, retrieval_eval  # noqa: E402
from scaffold.structured import Triage, structured_call  # noqa: E402
from scaffold.tools import Registry, calculate, lookup_label_rate, registry  # noqa: E402
from scaffold.agent import run_agent  # noqa: E402
from scaffold.workflow import Escalate, Outcome, chain, evaluator_optimizer, vote  # noqa: E402


def test_structured_triage_mock():
    llm = get_llm()
    rec = structured_call(llm, TRIAGE, "HX-900 throwing E212, fluid low", Triage)
    assert rec.error_code == "E212" and 1 <= rec.urgency <= 4


def test_chain_escalates():
    def a(x):
        return x + 1

    def b(x):
        raise Escalate("nope")

    out = chain(a, b)(1)
    assert isinstance(out, Outcome) and out.status == "escalate"


def test_vote_and_refine():
    assert vote(lambda x: x > 0, 1, n=3) is True
    draft, ok = evaluator_optimizer(lambda x, fb: "ok" if fb else "bad", lambda d: (d == "ok", "fix"), None)
    assert ok and draft == "ok"


def test_tools():
    assert calculate("137 * 2.5 / 320")["value"] > 1.07
    assert lookup_label_rate("Product X", "soybean")["phi_days"] == 60
    reg = Registry()
    reg.tools = registry.tools
    res = reg.call("create_work_order", {"machine": "HX-900", "issue": "E212"})
    assert res["status"] == "pending_approval" and reg.approvals


def test_retrieval_recall():
    """The eval set is deliberately split: questions worded like the document, and
    questions worded like a person. The easy half should be near-perfect; the hard half
    is the one `run.py sweep` makes move, so it only has to clear a much lower bar."""
    from scaffold.evals import load_jsonl
    from scaffold.domains import data_dir

    idx = build_index(chunk_by_section)
    cases = load_jsonl(data_dir() / "eval_retrieval.jsonl")
    easy = [c for c in cases if not c.get("hard")]
    hard = [c for c in cases if c.get("hard")]
    assert easy and hard, "the sweep lab needs both halves present"
    assert retrieval_eval(idx, easy, k=5, mode="hybrid")["recall@k"] >= 0.85
    assert retrieval_eval(idx, hard, k=5, mode="hybrid")["recall@k"] >= 0.3
    assert retrieval_eval(idx, cases, k=10, mode="hybrid")["recall@k"] >= 0.8


def test_agent_bounded():
    res = run_agent(get_llm(), registry, "What is the rate of Product X on corn?",
                    tool_names=["lookup_label_rate"], max_steps=3)
    assert res.steps <= 3


# --- no-code track -----------------------------------------------------------
def test_run_cli_commands():
    """The one-command tool must work end to end in practice mode."""
    import subprocess, sys as _s
    root = Path(__file__).resolve().parent.parent
    for argv in (["check"], ["tickets"], ["docs"],
                 ["find", "re-entry interval Product X"],
                 ["ask", "--no-docs", "What is the rate of Product X on corn?"],
                 ["tools", "--no-tools", "Is Product Y labelled for wheat?"]):
        r = subprocess.run([_s.executable, "run.py", *argv], cwd=root,
                           capture_output=True, text=True,
                           env={**os.environ, "LLM_PROVIDER": "mock"})
        assert r.returncode == 0, f"run.py {argv[0]} failed:\n{r.stderr}"


def test_worksheets_present():
    ws = Path(__file__).resolve().parent.parent / "worksheets"
    for name in ("lab1", "lab2", "lab3", "lab4", "lab5", "capstone", "glossary"):
        assert (ws / f"{name}.md").exists(), f"missing worksheet {name}.md"


# --- friendly failures instead of tracebacks --------------------------------
def test_bad_provider_config_gives_readable_error():
    """A wrong key or missing SDK must not hand a participant a traceback."""
    import subprocess, sys as _s
    root = Path(__file__).resolve().parent.parent
    cases = [
        {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""},        # no key
        {"LLM_PROVIDER": "anthropik"},                            # typo
    ]
    for extra in cases:
        env = {**os.environ, **extra}
        env.pop("ANTHROPIC_API_KEY", None)
        r = subprocess.run([_s.executable, "run.py", "check"], cwd=root,
                           capture_output=True, text=True, env=env)
        out = r.stdout + r.stderr
        assert "Traceback" not in out, f"participant saw a traceback for {extra}:\n{out}"
        assert "LLM_PROVIDER=mock" in out, f"no offline fallback suggested for {extra}"


# --- the second worked example ----------------------------------------------
def _run(argv, domain=None):
    import subprocess, sys as _s
    root = Path(__file__).resolve().parent.parent
    env = {**os.environ, "LLM_PROVIDER": "mock"}
    if domain:
        env["WORKSHOP_DOMAIN"] = domain
    return subprocess.run([_s.executable, "run.py", *argv], cwd=root,
                          capture_output=True, text=True, env=env)


def test_office_domain_runs_every_command():
    """A finance or HR attendee must get the same experience as an ag one."""
    for argv in (["--domain", "office", "check"],
                 ["--domain", "office", "tickets"],
                 ["--domain", "office", "docs"],
                 ["--domain", "office", "find", "how much can I spend on dinner in Chicago"],
                 ["--domain", "office", "ask", "--no-docs", "What is the meal cap in Chicago?"],
                 ["--domain", "office", "tools", "What is the daily meal limit in Chicago?"]):
        r = _run(argv)
        assert r.returncode == 0, f"run.py {argv} failed:\n{r.stderr}"
        assert "Traceback" not in r.stdout + r.stderr


def test_office_retrieval_finds_the_right_policy():
    os.environ["WORKSHOP_DOMAIN"] = "office"
    try:
        import importlib
        from scaffold import rag as _rag
        importlib.reload(_rag)
        idx = _rag.build_index(_rag.chunk_fixed)
        r = _rag.retrieval_eval(idx, k=5, mode="hybrid")
        assert r["recall@k"] >= 0.8, r
    finally:
        os.environ["WORKSHOP_DOMAIN"] = "ag"
        import importlib
        from scaffold import rag as _rag
        importlib.reload(_rag)


def test_office_claim_schema():
    os.environ["WORKSHOP_DOMAIN"] = "office"
    try:
        from scaffold.prompts import TRIAGE_CLAIM
        from scaffold.structured import Claim, structured_call
        rec = structured_call(get_llm(), TRIAGE_CLAIM,
                              "Hotel in New York at $410 a night, I didn't ask first.", Claim)
        assert rec.category == "LODGING" and rec.needs_human
    finally:
        os.environ["WORKSHOP_DOMAIN"] = "ag"


# --- the guided tour --------------------------------------------------------
def test_demo_runs_in_both_domains():
    """`run.py demo` is the first thing an attendee types. It must never fail."""
    for domain in ("ag", "office"):
        r = _run(["--domain", domain, "demo", "--auto"])
        assert r.returncode == 0, f"demo failed for {domain}:\n{r.stderr}"
        out = r.stdout
        assert "Traceback" not in out + r.stderr
        for beat in ("STEP 1 of 5", "STEP 5 of 5", "That is the whole workshop"):
            assert beat in out, f"{domain} demo missing '{beat}'"
        # the irreversible action must stop at the gate, in both examples
        assert "NOT" in out and "approval" in out.lower()


# --- provider parameter compatibility ---------------------------------------
class _FakeOpenAIError(Exception):
    """Stands in for openai.BadRequestError: carries a status_code like the real one."""

    def __init__(self, message: str):
        super().__init__(message)
        self.status_code = 400


def test_openai_drops_parameters_the_model_rejects():
    """Which sampling/length parameters a model accepts changes every few months.

    `OpenAILLM._call` must react to a 400 that names a parameter by dropping it and
    retrying, and must fall back to `max_tokens` when `max_completion_tokens` is
    refused. Exercised with a fake client so it needs no key and no network.
    """
    from types import SimpleNamespace
    from scaffold.llm import OpenAILLM

    reject = ["reasoning_effort", "max_completion_tokens"]
    seen: list[dict] = []

    def create(**kwargs):
        seen.append(dict(kwargs))
        for name in reject:
            if name in kwargs:
                raise _FakeOpenAIError(f"Unsupported parameter: '{name}' is not supported "
                                       f"with this model.")
        usage = SimpleNamespace(prompt_tokens=11, completion_tokens=3)
        msg = SimpleNamespace(content="ok", tool_calls=None)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)], usage=usage)

    llm = OpenAILLM.__new__(OpenAILLM)          # skip __init__: no key, no SDK client
    llm.models = {"small": "test-model", "large": "test-model"}
    llm.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    out = llm._call(create, dict(model="test-model", messages=[], reasoning_effort="low",
                                 max_completion_tokens=256),
                    OpenAILLM._CHAT_OPTIONAL,
                    {"max_completion_tokens": ("max_tokens", 256)})

    assert out.choices[0].message.content == "ok"
    assert len(seen) == 3, [sorted(k) for k in seen]
    assert "reasoning_effort" not in seen[-1]
    assert seen[-1]["max_tokens"] == 256, "should fall back to the older parameter name"


def test_anthropic_omits_temperature_by_default(monkeypatch):
    """Claude 4.7+ returns 400 on a non-default temperature; the SDK v1.0+ removed it."""
    from scaffold.llm import _send_temperature

    monkeypatch.delenv("ANTHROPIC_SEND_TEMPERATURE", raising=False)
    assert _send_temperature() is False
    monkeypatch.setenv("ANTHROPIC_SEND_TEMPERATURE", "1")
    assert _send_temperature() is True


def test_openai_tool_calling_uses_the_responses_api():
    """Current OpenAI models require the Responses API for tool calling.

    Drives a full two-turn agent loop against a fake client: the model asks for a
    tool, we run it, and the result goes back as a `function_call_output` keyed by
    `call_id`. Also checks that reasoning items are returned with the tool output,
    which those models require.
    """
    from types import SimpleNamespace
    from scaffold.agent import run_agent
    from scaffold.llm import OpenAILLM
    from scaffold.tools import Registry, registry as real

    requests: list[dict] = []

    def responses_create(**kwargs):
        requests.append(dict(kwargs))
        if len(requests) == 1:                       # first turn: ask for the tool
            out = [SimpleNamespace(type="reasoning", id="rs_1",
                                   model_dump=lambda **k: {"type": "reasoning", "id": "rs_1"}),
                   SimpleNamespace(type="function_call", id="fc_1", call_id="call_1",
                                   name="calculate", arguments='{"expression": "137 * 2.5 / 320"}',
                                   model_dump=lambda **k: {"type": "function_call",
                                                           "call_id": "call_1"})]
            return SimpleNamespace(output=out, output_text="",
                                   usage=SimpleNamespace(input_tokens=40, output_tokens=9))
        return SimpleNamespace(output=[], output_text="You need 2 jugs.",
                               usage=SimpleNamespace(input_tokens=60, output_tokens=12))

    def chat_create(**kwargs):
        raise AssertionError("tool calling must not go through chat completions")

    llm = OpenAILLM.__new__(OpenAILLM)
    llm.models = {"small": "test-model", "large": "test-model"}
    llm.client = SimpleNamespace(
        responses=SimpleNamespace(create=responses_create),
        chat=SimpleNamespace(completions=SimpleNamespace(create=chat_create)))

    reg = Registry()
    reg.tools = real.tools
    res = run_agent(llm, reg, "How many 2.5-gallon jugs for 137 acres of corn?",
                    tool_names=["calculate"], max_steps=3)

    assert res.text == "You need 2 jugs." and res.stopped_reason == "done"
    assert len(requests) == 2

    first = requests[0]
    assert first["tools"][0]["type"] == "function"
    assert first["tools"][0]["name"] == "calculate", "Responses API wants the flat tool shape"
    assert "function" not in first["tools"][0], "nested chat-completions shape would 400 here"
    assert first["instructions"], "the system prompt belongs in `instructions`"

    sent_back = requests[1]["input"]
    kinds = [i.get("type") for i in sent_back if isinstance(i, dict)]
    assert "reasoning" in kinds, "reasoning items must go back with the tool result"
    result = [i for i in sent_back if isinstance(i, dict)
              and i.get("type") == "function_call_output"]
    assert len(result) == 1 and result[0]["call_id"] == "call_1"
    assert "1.07" in result[0]["output"] or "value" in result[0]["output"]
