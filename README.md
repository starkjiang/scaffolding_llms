# Scaffolding LLMs — Workshop Codebase

Hands-on companion to the one-day industry workshop **Scaffolding LLMs: Prompts, Workflows,
Memory, and Tools for Reliable AI Applications**, run by the Translational AI Center (TrAC),
Iowa State University.

**Two worked examples.** The default is a dealer / agronomy support desk. Pass
`--domain office` for an expense-and-travel-claims desk that needs no industry
knowledge — same scaffolding, same labs, same failure modes. See
`worksheets/pick-your-example.md`.

The repo serves both halves of the room. If you write code, it is a small, readable reference
implementation of every pattern shown in the slides. If you do not, `worksheets/` and `run.py`
let you do every single lab without opening a Python file. The running example is a **dealer / agronomy support assistant**
that triages support tickets, grounds answers in product labels and equipment manuals, calls
tools, and is evaluated against a fixed test set. All documents and tickets are fictional.

## Quick start

**Not a programmer?** You still get every lab. `worksheets/chat-track.md` (equipment) and
`worksheets/chat-track-office.md` (expenses) have all six labs as paste-ready text for
ChatGPT or Claude — nothing to install. Or open
`worksheets/README.md` and start with `worksheets/lab1.md` — they need nothing but a chat tool. If you want
to see the machinery too, the one-command tool below needs no editing.

```bash
git clone <this-repo>
cd llm-scaffolding-workshop
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py check                                   # is everything set up?
python run.py demo                                    # a guided five-minute tour
```

Full instructions, including what to do when something breaks: **`SETUP.md`**.

**No API key?** Everything runs in *practice mode*: a keyword-based stand-in that
exercises every code path so you can see the scaffolding work. It is not a
language model — switch to a real provider to judge answer quality. With
`ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, the provider is detected
automatically.

## The one-command tool

`run.py` is the no-code entry point. Nothing to edit; you type one line at a time.

```bash
python run.py tickets                      # the sample support tickets
python run.py triage                       # run YOUR instruction over them      [Lab 1]
python run.py ask "what is the REI for Product X?"        # with documents       [Lab 3]
python run.py ask --no-docs "..."          # without them, to compare
python run.py find "..."                   # which sections the search found     [Lab 3]
python run.py sweep                        # chunking / mode / k vs recall@k     [Lab 3]
python run.py tools "how many jugs for 137 acres of corn?"                     # [Lab 4]
python run.py score --name baseline        # score against the test set          [Lab 5]
python run.py score --runs 5               # score 5x, report the noise floor     [Lab 5]
python run.py compare baseline after-my-change
```

Add `--verbose` to any command to see every step the system took. For Lab 1 you
write your instruction in `my_instruction.txt` — a plain text file, not code.

## Layout

```
worksheets/          the no-code track — printable lab sheets, glossary, worked examples
run.py               one-command entry point; no editing required
SETUP.md             setup for both tracks, with a troubleshooting table
FACILITATION.md      instructor runbook: setup email, lab timings, what to do when it goes wrong
WALKTHROUGH.md       what every part does, lab by lab — read this once before teaching
my_instruction.txt   your Lab 1 instruction, in plain text (created on first run)
scaffold/            the library — one module per workshop pillar
  llm.py             provider-agnostic client (Anthropic / OpenAI-compatible / mock)
  prompts.py         layered Prompt templates + the reference prompts        (Part 1)
  structured.py      schema-validated calls with feedback-on-retry           (Part 1)
  workflow.py        chain · route · parallel_map · vote · evaluator_optimizer (Part 2)
  memory.py          Session: typed facts + rolling summary + recent turns    (Part 3)
  rag.py             load · chunk · index · hybrid search · retrieval eval    (Part 3)
  tools.py           @tool registry, schemas from docstrings, approval gate   (Part 4)
  agent.py           bounded agent loop (steps / time / tokens)               (Part 4)
  evals.py           eval runner: deterministic checks + model-as-judge      (Part 5)
  tracing.py         nested spans, token totals, printed trace tree           (Part 5)
labs/                lab1 … lab5 with TODOs — what participants edit
solutions/           reference solutions (also imported by lab5 and the capstone)
capstone.py          router → chain / RAG / tools, plus `capstone.py eval`
data/                fictional labels, manual, agronomy guide, policy, tickets, eval sets
tests/               smoke tests (CI runs them in mock mode)
reports/             eval reports written by scaffold.evals (git-ignored)
```

## The labs

Every lab has **two tracks**. Track A needs no code; Track B is the Python
version. They answer the same question, and pairs that mix the two get the most
out of them.

| Lab | Time | Track A (no code) | Track B (code) |
|-----|------|-------------------|----------------|
| 1 — Instructions | 25 min | `worksheets/lab1.md` + `run.py triage` | `labs/lab1_prompts.py` |
| 2 — Steps | 30 min | `worksheets/lab2.md` | `labs/lab2_workflow.py` |
| 3 — Memory | 30 min | `worksheets/lab3.md` + `run.py ask` / `find` | `labs/lab3_rag.py` |
| 4 — Tools | 25 min | `worksheets/lab4.md` + `run.py tools` | `labs/lab4_tools.py` |
| 5 — Trust | 25 min | `worksheets/lab5.md` + `run.py score` | `labs/lab5_evals.py` |
| Capstone | 30 min | `worksheets/capstone.md` | `capstone.py` |

Each Track B file has numbered `TODO`s and a matching file in `solutions/`.

## Design notes (what the code is trying to teach)

- **Prompts are contracts.** `Prompt` renders stable sections first and always delimits untrusted
  input. `structured_call` validates with Pydantic and feeds the validation error back on retry.
- **Code decides where it can.** `workflow.chain` is a list of plain functions; gates are
  deterministic; `Escalate` is a normal outcome, not an exception the user sees.
- **Retrieval is measured separately.** `rag.retrieval_eval` reports recall@k / MRR before any
  answer prompt is involved. `chunk_by_section` enriches chunks with document and section names.
- **Tools are the risk surface.** `Registry` builds schemas from docstrings; `write=True` tools are
  queued for human approval by default; tool errors go back to the model as data.
- **Agents are bounded.** `run_agent` stops on step, time, or token limits and says so.
- **Evals are the product.** `run_eval` scores per case type and writes a JSON report so two runs
  can be diffed. The planted prompt injection in `data/docs/service_policy.md` and ticket T-007
  are part of the test set on purpose.

## Providers

`scaffold/llm.py` normalises three back-ends behind `complete()` and `chat(messages, tools=…)`.
Model names come from `.env` (`LLM_MODEL_SMALL`, `LLM_MODEL_LARGE`) so tiering is a one-line change.
To add another provider, subclass `LLM`, implement `_chat`, and the two message-format helpers.

## Instructor setup checklist

- [ ] Provision per-participant keys the day before; put them in a shared `.env` snippet.
- [ ] Run `python -m pytest -q && python capstone.py eval` on the venue network with a real key.
- [ ] Print (or share) the `TODO` list per lab; most pairs need the hint for Lab 2 TODO 3 and Lab 3 TODO 4.
- [ ] Keep the `solutions/` folder public — the point is comparison, not secrecy.

## License

MIT — see `LICENSE`. Sample documents are fictional and for training only; never use them as
agronomic or safety guidance.
