# Setup

Two paths. Pick the one that matches you.

---

## Path A — I don't write code

You can do every lab in this workshop with **nothing but a chat tool** (Claude,
ChatGPT, Copilot — whatever your company allows) and the worksheets in
`worksheets/`.

1. Open `worksheets/README.md` and start with `worksheets/lab1.md`.
2. Keep `worksheets/glossary.md` open in another tab.

That is it. Nothing to install.

**Optional, and worth 10 minutes:** the repository also has a one-command tool
that lets you see what the system is doing underneath, without editing anything.
Follow Path B's first three steps, then type:

```
python run.py check     # is everything set up?
python run.py demo      # then take the five-minute guided tour
```

Everything after that is typing one line at a time. `python run.py` on its own
lists what you can do.

---

## Path B — I want to run the code

**You need:** Python 3.10 or newer. Check with `python --version`.

**macOS / Linux**

```bash
git clone <this-repo>
cd llm-scaffolding-workshop

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

python run.py check          # is everything set up?
python run.py demo           # then take the five-minute guided tour
```

**Windows (Command Prompt)**

```bat
git clone <this-repo>
cd llm-scaffolding-workshop

py -m venv .venv
.venv\Scripts\activate

python -m pip install -r requirements.txt

python run.py check
python run.py demo
```

Three things that trip people up on Windows:

- **In PowerShell, activation may be blocked.** You will see a message about
  execution policies. Either use the Command Prompt instead, or run
  `Set-ExecutionPolicy -Scope Process -Bypass` in that window first, then
  activate. The setting lasts only for that window.
- **Use `python -m pip`, not bare `pip`.** Bare `pip` can belong to a different
  Python than the one that runs `run.py`, which is how you end up with packages
  installed and still get `No module named 'dotenv'`.
- **If you unzipped rather than cloned**, you may have a folder inside a folder
  of the same name. `cd` until you are in the one that directly contains
  `run.py` and `requirements.txt`.

If a package is missing, `run.py` tells you which ones and prints the exact
install command for the Python you are actually running. Copy that line.

### Using a real AI model

Everything runs without an API key in **practice mode**, which uses a simple
stand-in so the labs work offline. It is not a language model — it is enough to
see the plumbing, not enough to judge quality.

For a real model:

```bash
cp .env.example .env
```

Open `.env` and fill in **one** of:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

Then `python run.py check` should report your provider instead of `mock`.

> Workshop attendees: keys are provided on the day. Do not commit `.env` — it is
> already in `.gitignore`.

**Check the model IDs before you rely on them.** Model IDs retire on a published
schedule and a retired ID fails every request, so confirm the current list before
a workshop rather than on the morning:

| Provider | `LLM_MODEL_SMALL` | `LLM_MODEL_LARGE` | Current list |
|---|---|---|---|
| OpenAI | `gpt-6-luna` | `gpt-6.1-sol` | <https://developers.openai.com/api/docs/models> |
| Anthropic | `claude-haiku-5-5` | `claude-sonnet-5-5` | <https://platform.claude.com/docs/en/models/overview> |

`gpt-4o` and `gpt-4o-mini` are deprecated and leave the API on 14 January 2027;
the `gpt-4o-2024-05-13` snapshot goes sooner. If you have older notes or an older
`.env`, update them.

**Parameters, which are the part that bites.** Current models have been removing
sampling and length parameters, and the rules differ by provider and generation:

- `temperature` / `top_p` / `top_k` are deprecated on Claude 4.7 and later — a
  non-default value returns a 400, and the Python SDK v1.0+ removed them
  outright. On OpenAI they are still accepted on chat completions but restricted
  on reasoning models.
- `max_tokens` is deprecated on OpenAI in favour of `max_completion_tokens`.
- `reasoning_effort` is only valid on some models, and not every model accepts
  every value.

Rather than hard-coding a table that goes stale, `scaffold/llm.py` sends a
conservative set and **drops whatever the API objects to**, printing a one-line
note when it does. So an unsupported setting costs you one wasted request, not a
crash. If you pinned an older model and want the old behaviour back, set
`OPENAI_SEND_TEMPERATURE=1` or `ANTHROPIC_SEND_TEMPERATURE=1`.

**OpenAI users: tool calling goes through the Responses API.** The current GPT-6
models require it — chat completions returns a 400 for a request carrying tools.
`scaffold/llm.py` handles this automatically: plain text calls use chat
completions, and anything with tools (Lab 4, the capstone) uses the Responses
API, where tools are declared flat, the system prompt travels as `instructions`,
and results come back as `function_call_output` items keyed by `call_id`.
Reasoning items are handed back with the tool results, which those models
require. You do not need to configure any of this, but it is worth knowing when
someone asks why Lab 4 looks different in the trace.

**OpenAI users: try `OPENAI_REASONING_EFFORT=low` first.** The current models
default to medium reasoning effort, which makes every lab slower and more
expensive than it needs to be. If your model supports `none`, that is the right
setting for the classification and extraction steps.

### Running the labs

```bash
python -m pytest -q          # confirm everything works
python labs/lab1_prompts.py  # Lab 1
```

Each lab file has numbered `TODO`s. `solutions/` has a worked answer for each
one — look freely, the point is comparison, not secrecy.

---

## If something goes wrong

| Problem | Fix |
|---|---|
| `python: command not found` | Try `python3` instead, everywhere |
| `No module named 'scaffold'` | You are in the wrong folder. `cd` into `llm-scaffolding-workshop` |
| `No module named 'dotenv'` (or `pydantic`, `numpy`, `rank_bm25`) | The dependencies are not installed for the Python you are running. `run.py` prints the exact command — copy it. Usually it means the virtual environment was not activated in this window. |
| You installed the packages and still get `No module named …` | `pip` went to a different Python. Use `python -m pip install -r requirements.txt` so it matches. |
| PowerShell refuses to activate the venv | `Set-ExecutionPolicy -Scope Process -Bypass`, then activate again. Or use the Command Prompt. |
| `provider mock` but you added a key | Check `.env` is in the repository root and the line has no quotes |
| An error about a key or a provider | Read the two lines it prints — it names the problem and the fix |
| Nothing works and the lab is starting | Use Path A. Every lab has a no-code track. |
