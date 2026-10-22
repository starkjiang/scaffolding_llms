#!/usr/bin/env python3
"""
run.py — the no-code entry point for this workshop.

You never need to edit a Python file to use this. You type one command, and
where a lab asks you to write something, you write it in a plain text file.

    python run.py check                      is everything set up?
    python run.py tickets                    show the sample support tickets
    python run.py docs                       show the sample documents

    python run.py triage                     run YOUR instruction (my_instruction.txt)
                                             over every ticket                   [Lab 1]
    python run.py triage --ticket T-007      run it over one ticket

    python run.py ask "your question"        answer using the documents          [Lab 3]
    python run.py ask --no-docs "question"   answer WITHOUT the documents, to compare
    python run.py find "your question"       show which document sections were found
    python run.py sweep                      chunking / search mode / k vs recall@k

    python run.py tools "your question"      let it use the lookup + calculator   [Lab 4]
    python run.py tools --no-tools "..."     same question, no tools, to compare

    python run.py score                      score the assistant on the test set  [Lab 5]
    python run.py score --name after-change  save the result under a name, to compare
    python run.py score --runs 5             score five times, report the spread (noise floor)
    python run.py compare before after       show what changed between two runs

Add --verbose to any command to see every step the system took.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# --domain has to be honoured before anything reads a data path, and it should work
# wherever the person puts it, so take it out of argv ourselves.
def _take_domain_flag(argv: list[str]) -> None:
    for i, a in enumerate(list(argv)):
        if a == "--domain" and i + 1 < len(argv):
            os.environ["WORKSHOP_DOMAIN"] = argv[i + 1].strip().lower()
            del argv[i:i + 2]
            return
        if a.startswith("--domain="):
            os.environ["WORKSHOP_DOMAIN"] = a.split("=", 1)[1].strip().lower()
            del argv[i]
            return


_take_domain_flag(sys.argv)


def _check_dependencies() -> None:
    """A missing package is the most common first failure. Say so in English.

    The usual cause is `pip install` landing in a different Python from the one
    running this file — so the fix we print uses THIS interpreter explicitly.
    """
    required = {"dotenv": "python-dotenv", "pydantic": "pydantic",
                "numpy": "numpy", "rank_bm25": "rank-bm25"}
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if not missing:
        return

    windows = os.name == "nt"
    req = ROOT / "requirements.txt"
    lines = [
        "",
        f"  Missing {'package' if len(missing) == 1 else 'packages'}: {', '.join(missing)}",
        "",
        "  They are not installed for the Python that is running this file:",
        f"      {sys.executable}",
        "",
        "  Install them into that exact Python:",
        f'      "{sys.executable}" -m pip install -r "{req}"',
    ]
    if sys.prefix == sys.base_prefix:
        lines += [
            "",
            "  You are not in a virtual environment. If you created one, activate it",
            "  first and then run the install again:",
            "      " + (r".venv\Scripts\activate" if windows
                        else "source .venv/bin/activate"),
        ]
        if windows:
            lines += [
                "  (PowerShell may block that. Either use the Command Prompt, or run:",
                "       Set-ExecutionPolicy -Scope Process -Bypass",
                "   in this window first.)",
            ]
    if not req.exists():
        lines += ["", f"  Note: {req} does not exist, so you may be in the wrong folder.",
                  "  cd into the folder that contains run.py and requirements.txt."]
    lines += ["", "  No key is needed for any of this. Once it installs, run:",
              "      python run.py check", ""]
    raise SystemExit("\n".join(lines))


_check_dependencies()

from scaffold import get_llm, trace                                    # noqa: E402
from scaffold.agent import run_agent                                   # noqa: E402
from scaffold.evals import load_jsonl, print_summary, run_eval         # noqa: E402
from scaffold.domains import DOMAINS, current, data_dir, info          # noqa: E402
from scaffold.prompts import (ANSWER_WITH_SOURCES, TRIAGE, TRIAGE_CLAIM,  # noqa: E402
                              Prompt)
from scaffold.rag import build_index, render_context                   # noqa: E402
from scaffold.structured import Claim, Triage, structured_call         # noqa: E402
from scaffold.tools import registry, tools_for                         # noqa: E402

def instruction_file() -> Path:
    return ROOT / ("my_instruction.txt" if current() == "ag"
                   else f"my_instruction_{current()}.txt")
REPORTS = ROOT / "reports"

W = 92


def rule(title: str = "") -> None:
    if title:
        print("\n" + "=" * W + f"\n{title}\n" + "=" * W)
    else:
        print("-" * W)


def wrap(text: str, indent: str = "  ") -> str:
    return "\n".join(textwrap.fill(line, W - len(indent), initial_indent=indent,
                                   subsequent_indent=indent) or indent
                     for line in str(text).splitlines())


# ---------------------------------------------------------------------------
# check
# ---------------------------------------------------------------------------
def cmd_check(args) -> None:
    rule("Setup check")
    llm = get_llm()
    print(f"  Worked example    {info()['label']}   (--domain {current()})")
    print(f"  Python            {sys.version.split()[0]}")
    print(f"  AI provider       {llm.provider}")
    if llm.provider == "mock":
        print(wrap("No API key found, so you are in PRACTICE MODE. Everything runs and every "
                   "lab works, but the answers come from a simple stand-in rather than a real "
                   "model. To use a real model, put a key in the .env file — see SETUP.md.", "                    "))
    print(f"  Documents         {len(list((data_dir() / 'docs').glob('*.md')))} files in data/docs/")
    print(f"  Sample tickets    {len(load_jsonl(data_dir() / 'tickets.jsonl'))}")
    print(f"  Test cases        {len(load_jsonl(data_dir() / 'eval_cases.jsonl'))}")
    print(f"  Your instruction  {'found' if instruction_file().exists() else 'MISSING — see Lab 1'}"
          f"  ({instruction_file().name})")
    flag = " --domain office" if current() == "office" else ""
    print(f"\n  You are ready. Start here:  python run.py{flag} demo")


# ---------------------------------------------------------------------------
# tickets / docs
# ---------------------------------------------------------------------------
def cmd_tickets(args) -> None:
    rule(f"Sample {info()['unit']}s — {info()['label']}")
    for t in load_jsonl(data_dir() / "tickets.jsonl"):
        print(f"\n  {t['id']}")
        print(wrap(t["text"], "      "))
    hid = "C-007" if current() == "office" else "T-007"
    print(f"\n  {hid} contains a hidden instruction aimed at the assistant."
          "\n  A well-written instruction treats it as information, not as an order.")


def cmd_docs(args) -> None:
    rule(f"Documents the assistant can use — {info()['label']}")
    for p in sorted((data_dir() / "docs").glob("*.md")):
        text = p.read_text(encoding="utf-8")
        head = next((l for l in text.splitlines() if l.startswith("# ")), p.stem)
        print(f"\n  {p.name}")
        print(f"      {head.lstrip('# ')}")
    print("\n  All of these are fictional, written for this workshop. Never use them as real "
          "\n  agronomic or safety guidance.")


# ---------------------------------------------------------------------------
# triage — Lab 1
# ---------------------------------------------------------------------------
DEFAULT_INSTRUCTION_OFFICE = """\
# This is YOUR instruction to the assistant. Edit it, save the file, and run:
#     python run.py --domain office triage
#
# Lines starting with # are notes to yourself and are not sent to the AI.
#
# Cover the five things from the slides:
#   1. Who it should be          2. What to do, step by step
#   3. What the answer looks like (the fields below are required)
#   4. What to do when it does not know
#   5. Examples of a good answer (optional, but they help)

You are a triage assistant for a company expense desk.

Read the expense claim and fill in a triage record.

Return ONLY a JSON object with exactly these fields:
  category     MEALS, LODGING, TRAVEL, EQUIP, or OTHER; null if the claim does not say
  amount_usd   the amount claimed as a number, or null if not stated
  summary      one sentence, under 30 words
  risk         a number 1-4
  needs_human  true or false
"""

DEFAULT_INSTRUCTION = """\
# This is YOUR instruction to the assistant. Edit it, save the file, and run:
#     python run.py triage
#
# Lines starting with # are notes to yourself and are not sent to the AI.
# Everything else IS sent. Write it the way you would brief a new colleague.
#
# Try to cover the five things from the slides:
#   1. Who it should be
#   2. What to do, step by step
#   3. What the answer should look like   (the fields below are required)
#   4. What to do when it does not know
#   5. Examples of a good answer          (optional, but they help a lot)

You are a triage assistant for an equipment dealer support desk.

Read the support ticket and fill in a triage record.

Return ONLY a JSON object with exactly these fields:
  machine_model  the machine model mentioned, or null if the ticket does not say
  error_code     the diagnostic code mentioned, or null if the ticket does not say
  summary        one sentence, under 30 words
  urgency        a number 1-4
  needs_human    true or false
"""


def load_instruction() -> str:
    if not instruction_file().exists():
        starter = DEFAULT_INSTRUCTION if current() == "ag" else DEFAULT_INSTRUCTION_OFFICE
        instruction_file().write_text(starter, encoding="utf-8")
        print(f"  Created {instruction_file().name} with a starting instruction for you to edit.\n")
    raw = instruction_file().read_text(encoding="utf-8")
    body = "\n".join(l for l in raw.splitlines() if not l.lstrip().startswith("#"))
    if not body.strip():
        sys.exit(f"{instruction_file().name} is empty. Write your instruction in it and run again.")
    return body.strip()


def cmd_triage(args) -> None:
    llm = get_llm()
    instruction = load_instruction()
    office = current() == "office"
    schema = Claim if office else Triage
    prompt = Prompt(name="my_instruction", version="file", system=instruction,
                    input_tag="claim" if office else "ticket")
    tickets = load_jsonl(data_dir() / "tickets.jsonl")
    if args.ticket:
        tickets = [t for t in tickets if t["id"].upper() == args.ticket.upper()]
        if not tickets:
            sys.exit(f"No ticket called {args.ticket}. Run: python run.py tickets")

    rule(f"Running YOUR instruction from {instruction_file().name}  (provider: {llm.provider})")
    ok = 0
    for t in tickets:
        trace.reset()
        print(f"\n  {t['id']}  {t['text'][:70]}{'…' if len(t['text']) > 70 else ''}")
        try:
            rec = structured_call(llm, prompt, t["text"], schema)
            ok += 1
            if office:
                amt = f"${rec.amount_usd:,.2f}" if rec.amount_usd is not None else "—"
                print(f"      category: {rec.category or '—':<8} amount: {amt:<10}"
                      f" risk: {rec.risk}   needs a person: {rec.needs_human}")
            else:
                print(f"      machine: {rec.machine_model or '—':<10} code: {rec.error_code or '—':<8}"
                      f" urgency: {rec.urgency}   needs a person: {rec.needs_human}")
            print(wrap(f"summary: {rec.summary}", "      "))
        except Exception as e:
            print(f"      COULD NOT USE THE ANSWER: {e}")
            print("      → the answer did not have the fields you asked for. Make the format "
                  "instruction more explicit.")
        if args.verbose:
            trace.print_last()
    rule()
    print(f"  {ok} of {len(tickets)} answers were usable.\n")
    print("  Now look at the hard ones:")
    if office:
        print("    C-003  over the hotel cap, asks you to approve → flagged, and no approval given?")
        print("    C-007  contains a hidden order                 → flagged instead of obeyed?")
        print("    C-008  one purchase split into two claims      → spotted as a violation?")
    else:
        print("    T-003  smoke and an engine alarm   → is urgency 4, and does it need a person?")
        print("    T-007  contains a hidden order     → did it get flagged instead of obeyed?")
        print("    T-008  an error code we don't know → did it refuse rather than invent a fix?")
    print(f"\n  Edit {instruction_file().name} and run this again to see what changes.")


# ---------------------------------------------------------------------------
# ask / find — Lab 3
# ---------------------------------------------------------------------------
def cmd_ask(args) -> None:
    llm = get_llm()
    question = " ".join(args.question)
    rule(f"Question: {question}")
    trace.reset()
    if args.no_docs:
        print("  Mode: NO DOCUMENTS — answering from the model's own memory only.\n")
        answer = llm.complete(question, system="You are an assistant for agronomists and "
                              "equipment technicians. Answer the question.", tier="large")
        sources = []
    else:
        index = build_index()
        chunks = index.search(question, k=5, mode="hybrid")
        sources = [c.id for c in chunks]
        print(f"  Mode: WITH DOCUMENTS — found {len(chunks)} relevant sections.\n")
        answer = llm.complete(ANSWER_WITH_SOURCES.render_user(question, context=render_context(chunks)),
                              system=ANSWER_WITH_SOURCES.render_system(), tier="large")
    print(wrap(answer))
    if sources:
        print(f"\n  Sections used: {', '.join(sources)}")
    if args.verbose:
        trace.print_last()
    if not args.no_docs:
        print("\n  Try the same question with --no-docs and compare. That difference is the "
              "\n  whole point of Part 3.")


def cmd_sweep(args) -> None:
    """Turn the retrieval knobs and watch recall move. Nothing downstream can beat this number."""
    from scaffold.rag import Index, chunk_by_section, chunk_fixed, load_docs, retrieval_eval

    docs = load_docs()
    cases = load_jsonl(data_dir() / "eval_retrieval.jsonl")
    trace.reset()

    def build(kind: str, size: int) -> Index:
        if kind == "section":
            chunks = [c for d in docs for c in chunk_by_section(d, max_chars=size)]
        else:
            chunks = [c for d in docs for c in chunk_fixed(d, size=size, overlap=min(60, size // 4))]
        return Index(chunks)

    easy = [c for c in cases if not c.get("hard")]
    hard = [c for c in cases if c.get("hard")]

    rule(f"Retrieval sweep — {len(cases)} questions with a known right answer, "
         f"{len(docs)} documents ({current()})")
    print(wrap("Recall@k is the share of questions where the correct document made it into the "
               "top k. It is a ceiling: if the right section never arrives, no prompt wording, "
               "no bigger model and no amount of temperature tuning downstream can recover it."))
    print(wrap(f"The set is split: {len(easy)} EASY questions worded the way the document is "
               f"worded, and {len(hard)} HARD ones worded the way a person actually types. "
               "Watch those two columns separately — the overall average hides which one is "
               "moving, and it is never the easy one."))

    print(f"\n  1. CHUNKING      (search mode: {args.mode}, k={args.k})\n")
    print("     strategy   size   chunks   avg chars   recall@k     easy     hard      MRR")
    print("     " + "-" * 76)
    best = None
    for kind, size in (("section", 400), ("section", 900), ("section", 1500),
                       ("fixed", 200), ("fixed", 400), ("fixed", 800)):
        idx = build(kind, size)
        r = retrieval_eval(idx, cases, k=args.k, mode=args.mode)
        re_, rh = (retrieval_eval(idx, s, k=args.k, mode=args.mode) for s in (easy, hard))
        avg = round(sum(len(c.text) for c in idx.chunks) / max(1, len(idx.chunks)))
        print(f"     {kind:<10} {size:>4}   {len(idx.chunks):>6}   {avg:>9}   "
              f"{r['recall@k']:>8.3f} {re_['recall@k']:>8.3f} {rh['recall@k']:>8.3f}   "
              f"{r['mrr']:>6.3f}")
        if best is None or (rh["recall@k"], r["recall@k"]) > (best[1], best[2]):
            best = ((kind, size), rh["recall@k"], r["recall@k"], idx)

    (bk, bs), bhard, ball, bidx = best
    print(f"\n     Best on the hard half: {bk}/{bs} — recall@{args.k} {bhard:.3f} hard, "
          f"{ball:.3f} overall.\n     Chunking is usually the biggest single lever in this "
          "table, and it costs nothing\n     but a re-index. Teams reach for a bigger model first "
          "and leave this on the table.")

    print(f"\n  2. SEARCH MODE   (chunking: {bk}/{bs}, k={args.k})\n")
    print("     mode       recall@k     easy     hard      MRR")
    print("     " + "-" * 50)
    for mode in ("keyword", "dense", "hybrid"):
        r = retrieval_eval(bidx, cases, k=args.k, mode=mode)
        re_, rh = (retrieval_eval(bidx, s, k=args.k, mode=mode) for s in (easy, hard))
        print(f"     {mode:<10} {r['recall@k']:>8.3f} {re_['recall@k']:>8.3f} "
              f"{rh['recall@k']:>8.3f}   {r['mrr']:>6.3f}")
    print("\n     Keyword wins on part numbers, error codes and exact policy wording; dense wins"
          "\n     on paraphrase, which is most of the hard column. Hybrid fuses the two rankings"
          "\n     (reciprocal rank fusion) and rarely loses badly to either — which is why it is"
          "\n     the default even where one mode beats it on a particular set.")

    print(f"\n  3. HOW MANY TO RETRIEVE   (chunking: {bk}/{bs}, mode: {args.mode})\n")
    print("     k    recall@k      MRR")
    print("     " + "-" * 32)
    for k in (1, 3, 5, 10):
        r = retrieval_eval(bidx, cases, k=k, mode=args.mode)
        print(f"     {k:<4} {r['recall@k']:>8.3f}   {r['mrr']:>6.3f}")
    print("\n     Recall only goes up with k. So does cost, latency, and the amount of "
          "\n     near-miss text the model has to ignore. That trade is the whole decision.")

    final = retrieval_eval(bidx, cases, k=args.k, mode=args.mode)
    if final["misses"]:
        print(f"\n  Still missed at k={args.k}:")
        for q in final["misses"]:
            print(f"     ✗ {q}")
        print(wrap("Read those. They are not model failures — they are questions whose wording "
                   "shares no vocabulary with the section that answers them. The fix is in the "
                   "index or the query, never in the prompt.", "     "))
    else:
        print(f"\n  No misses at k={args.k} on this set — which mostly means the set is too easy."
              "\n  Add harder questions to data/eval_retrieval.jsonl. A test set that always "
              "\n  passes measures nothing.")


def cmd_find(args) -> None:
    question = " ".join(args.question)
    index = build_index()
    rule(f"What the search finds for: {question}")
    for i, c in enumerate(index.search(question, k=5, mode="hybrid"), 1):
        print(f"\n  {i}. [{c.id}]  section: {c.section or '(none)'}")
        print(wrap(c.text[:300].replace("\n", " ") + "…", "      "))
    print("\n  If the section that actually answers your question is not in this list, no "
          "\n  amount of prompt wording will fix the answer. That is a search problem.")


# ---------------------------------------------------------------------------
# tools — Lab 4
# ---------------------------------------------------------------------------
def cmd_tools(args) -> None:
    llm = get_llm()
    question = " ".join(args.question)
    rule(f"Question: {question}")
    trace.reset()
    if args.no_tools:
        print("  Mode: NO TOOLS — the model must answer from memory.\n")
        answer = llm.complete(question, system="You are an assistant for agronomists and "
                              "equipment technicians. Answer the question.", tier="large")
        print(wrap(answer))
        print("\n  Check every number above against data/labels.json. Were they right?")
        return
    registry.approvals.clear()
    print(f"  Mode: WITH TOOLS — available: {', '.join(tools_for())}\n")
    res = run_agent(llm, registry, question, tool_names=tools_for(), max_steps=6)
    print(wrap(res.text))
    print(f"\n  Steps taken: {res.steps}   Stopped because: {res.stopped_reason}")
    if res.pending_approvals:
        print("\n  WAITING FOR A HUMAN — these actions were proposed but NOT carried out:")
        for p in res.pending_approvals:
            print(f"      {p['tool']}  {p['args']}")
        print("  Nothing was written to any system. Someone has to approve it first.")
    if args.verbose:
        trace.print_last()


# ---------------------------------------------------------------------------
# score / compare — Lab 5
# ---------------------------------------------------------------------------
def _assistant(ticket: dict):
    if current() == "office":
        from solutions.lab2_office_solution import handle_with_trace
    else:
        from solutions.lab2_solution import handle_with_trace

    out, triage, article = handle_with_trace(ticket)
    return (triage.model_dump() if triage else None), out.text, article


def cmd_score(args) -> None:
    llm = get_llm()
    n_cases = len(load_jsonl(data_dir() / "eval_cases.jsonl"))
    runs = max(1, getattr(args, "runs", 1))
    rule(f"Scoring the {info()['unit']} chain on {n_cases} test cases"
         f"  (run name: {args.name}{f', {runs} repeats' if runs > 1 else ''})")
    print("  This scores the Lab 2 assembly line. For the full routed assistant (ag only), use:"
          "\n      python capstone.py eval\n")

    if runs == 1:
        summary = run_eval(_assistant, llm=llm, use_judge=args.judge, name=args.name)
        print_summary(summary)
        print(f"\n  Saved to reports/{args.name}.json")
        print("  Change one thing, then run:  python run.py score --name after-my-change")
        print("  and compare:                 python run.py compare baseline after-my-change")
        print("  Not sure a difference is real?  python run.py score --runs 5")
        return

    import statistics
    summaries = []
    for i in range(1, runs + 1):
        s = run_eval(_assistant, llm=llm, use_judge=args.judge, name=args.name)
        summaries.append(s)
        print(f"   run {i} of {runs}:  pass rate {s['pass_rate']:.0%}")
    print_summary(summaries[-1])

    rates = [s["pass_rate"] for s in summaries]
    failed_in = [{f["id"] for f in s["failures"]} for s in summaries]
    ever, always = set().union(*failed_in), set.intersection(*failed_in)
    flipped = sorted(ever - always)
    spread = (max(rates) - min(rates)) * 100

    rule()
    print(f"  Across {runs} runs:  min {min(rates):.0%}   max {max(rates):.0%}   "
          f"mean {statistics.mean(rates):.0%}   spread {spread:.0f} points")
    if flipped:
        print(f"  Unstable cases (passed in some runs, failed in others): {', '.join(flipped)}")
        print(wrap(f"That {spread:.0f}-point spread is your noise floor. A change that moves the "
                   "pass rate by less than that is not evidence yet — it is the same system "
                   "answering twice. Re-run before you believe it, and look at the unstable "
                   "cases first: they are usually the ones your instruction underspecifies."))
    else:
        print(wrap(f"All {runs} runs came out identical, so the spread is zero. The offline "
                   "practice model is deterministic by construction — it is a lookup table, not "
                   "a sampler. Point this at a real provider and run it again: whatever spread "
                   "you see there is your noise floor, and any improvement smaller than it is "
                   "not yet a result. This is the number teams skip, and it is why so many "
                   "prompt changes look like wins."))
    print(f"\n  Saved to reports/{args.name}.json (the last run)")


def cmd_compare(args) -> None:
    rows = []
    for name in (args.before, args.after):
        p = REPORTS / f"{name}.json"
        if not p.exists():
            sys.exit(f"No report called '{name}'. Run: python run.py score --name {name}")
        rows.append(json.loads(p.read_text())["summary"])
    before, after = rows
    rule(f"{args.before}  →  {args.after}")
    d = after["pass_rate"] - before["pass_rate"]
    arrow = "better" if d > 0 else ("worse" if d < 0 else "no change")
    print(f"  Overall: {before['pass_rate']:.0%}  →  {after['pass_rate']:.0%}   ({arrow})\n")
    for t in sorted(set(before["by_type"]) | set(after["by_type"])):
        b, a = before["by_type"].get(t, "—"), after["by_type"].get(t, "—")
        flag = "" if b == a else "   <-- changed"
        print(f"    {t:<16} {b:>6}  →  {a:>6}{flag}")
    still = {f["id"] for f in after["failures"]}
    was = {f["id"] for f in before["failures"]}
    if was - still:
        print(f"\n  Now passing:  {', '.join(sorted(was - still))}")
    if still - was:
        print(f"  Newly broken: {', '.join(sorted(still - was))}   <-- watch this")
    if still & was:
        print(f"  Still failing: {', '.join(sorted(still & was))}")
    print("\n  A change that fixes one case and breaks another is why you keep a test set.")


# ---------------------------------------------------------------------------
# demo — a guided tour anybody can run alone
# ---------------------------------------------------------------------------
def _pause(auto: bool, prompt: str = "    [Enter] to continue, or q to stop  ") -> bool:
    """Returns False if the viewer asked to stop."""
    if auto:
        return True
    try:
        return input(prompt).strip().lower() not in ("q", "quit", "exit")
    except (EOFError, KeyboardInterrupt):
        print()
        return False


def _beat(n: int, total: int, title: str, why: str) -> None:
    print("\n" + "=" * W)
    print(f"  STEP {n} of {total}   {title}")
    print("=" * W)
    print(wrap(why, "  "))
    print()


def cmd_demo(args) -> None:
    """Five short steps, one per pillar. No key, no editing, about five minutes."""
    auto = args.auto
    llm = get_llm()
    d = info()
    unit = d["unit"]
    office = current() == "office"
    total = 5

    rule(f"A five-minute tour of what scaffolding does  —  {d['label']}")
    print(wrap(d["blurb"], "  "))
    print()
    print(wrap("You will watch the same assistant get steadily more reliable, one addition at a "
               "time. Nothing here needs editing and nothing is saved. Just read what comes back "
               "and ask why it changed.", "  "))
    if llm.provider == "mock":
        print()
        print(wrap("You are in PRACTICE MODE (no API key). The shape of every answer is real; the "
                   "wording comes from a simple stand-in. Everything below still demonstrates the "
                   "point.", "  "))
    print()
    if not _pause(auto, "    [Enter] to begin, or q to stop  "):
        return

    # ---- 1. the raw model ------------------------------------------------
    q = ("What is the daily meal cap for Chicago, and does it include tip?" if office
         else "How long do workers have to stay out of a field after we spray Product X?")
    _beat(1, total, "The model on its own",
          "First, the question with nothing attached. The model has never seen your documents, "
          "so whatever comes back is a guess dressed as an answer.")
    print(f"    Question:  {q}\n")
    trace.reset()
    bare = llm.complete(q, system="You are an assistant for this organisation. Answer the question.",
                        tier="large")
    print(wrap(bare, "    "))
    print()
    if llm.provider == "mock":
        print(wrap("In practice mode the stand-in refuses honestly. A real model usually does not — "
                   "it produces a confident, plausible, wrong number instead. That gap between how "
                   "sure it sounds and how right it is, is the whole reason for step 2.", "  "))
    else:
        print(wrap("Notice how confident it sounds, and that nothing tells you where it came from. "
                   "Confidence is not accuracy — nothing in the mechanism makes it stop when it "
                   "does not know.", "  "))
    if not _pause(auto):
        return

    # ---- 2. retrieval ----------------------------------------------------
    _beat(2, total, "Hand it the page  (memory / RAG)",
          "Now the same question, with the relevant section of your own documents found and pasted "
          "in first. This is what people mean by RAG — an open-book exam.")
    index = build_index()
    chunks = index.search(q, k=4, mode="hybrid")
    print("    The search found these sections:")
    for c in chunks[:3]:
        print(f"      [{c.id}]  {c.section or '(no heading)'}")
    print()
    grounded = llm.complete(ANSWER_WITH_SOURCES.render_user(q, context=render_context(chunks)),
                            system=ANSWER_WITH_SOURCES.render_system(), tier="large")
    print(wrap(grounded, "    "))
    print()
    print(wrap("Same model, same question. The only thing that changed is that the right page was "
               "in front of it — and now the answer cites where it came from, so you can check it.", "  "))
    if not _pause(auto):
        return

    # ---- 3. structure ----------------------------------------------------
    _beat(3, total, "Ask for a fixed shape  (instructions)",
          "Prose is unusable by software. Here the same assistant is told exactly which fields to "
          "return, and the code refuses anything that does not fit.")
    sample = load_jsonl(data_dir() / "tickets.jsonl")[0]
    print(f"    A real {unit}:")
    print(wrap(sample["text"], "      "))
    print()
    schema = Claim if office else Triage
    prompt = TRIAGE_CLAIM if office else TRIAGE
    try:
        rec = structured_call(llm, prompt, sample["text"], schema)
        for k, v in rec.model_dump().items():
            text = str(v)
            if len(text) > 60:
                print(f"      {k:<14} {textwrap.fill(text, W - 24, subsequent_indent=' ' * 21)}")
            else:
                print(f"      {k:<14} {text}")
        print()
        print(wrap("Every field is checked before anything downstream sees it. A missing or "
                   "out-of-range value is rejected and retried automatically.", "  "))
    except Exception as e:
        print(wrap(f"The output failed validation: {e}", "    "))
        print(wrap("Which is the point — bad output is caught rather than passed on.", "  "))
    if not _pause(auto):
        return

    # ---- 4. tools --------------------------------------------------------
    tq = ("Is an $88 dinner for three people in Chicago within policy?" if office
          else "How many 2.5-gallon jugs of Product X do I need for 137 acres of corn?")
    _beat(4, total, "Let it look things up  (tools)",
          "Numbers should never come from the model's memory. Here it can ask your software to do "
          "the lookup and the arithmetic, and the real values come back.")
    print(f"    Question:  {tq}\n")
    registry.approvals.clear()
    trace.reset()
    res = run_agent(llm, registry, tq, tool_names=tools_for(), max_steps=6)
    print(wrap(res.text, "    "))
    print()
    print("    What it actually did:")
    trace.print_last()
    print()
    print(wrap("Every number in that answer is traceable to a lookup or a calculation. That is the "
               "difference between an assistant and a guess.", "  "))
    if not _pause(auto):
        return

    # ---- 5. the gate -----------------------------------------------------
    gq = ("Claim C-003 is $410 a night, over the limit, because cheaper rooms were sold "
          "out. Raise a policy exception for it." if office
          else "The manual says E212 needs a dealer pump inspection. Create a work order for HX-900.")
    _beat(5, total, "Stop before it changes anything  (trust)",
          "Last, something irreversible. Reading is free; writing is not. Watch what happens.")
    print(f"    Request:  {gq}\n")
    registry.approvals.clear()
    trace.reset()
    res2 = run_agent(llm, registry, gq, tool_names=tools_for(), max_steps=5)
    print(wrap(res2.text, "    "))
    if res2.pending_approvals:
        print()
        print("    WAITING FOR A HUMAN — proposed, but NOT carried out:")
        for p in res2.pending_approvals:
            print(f"      {p['tool']}  {p['args']}")
    print()
    print(wrap("Nothing was written to any system. A person has to approve it first — and that is "
               "a rule in the software, not a hope about the model's behaviour.", "  "))

    # ---- wrap ------------------------------------------------------------
    rule("That is the whole workshop, in five steps")
    print(wrap("  1  the model alone          guesses, confidently", "  "))
    print(wrap("  2  + your documents         answers from a source you can check", "  "))
    print(wrap("  3  + a fixed shape          output software can rely on", "  "))
    print(wrap("  4  + tools                  numbers that are looked up, not recalled", "  "))
    print(wrap("  5  + a gate                 nothing irreversible without a person", "  "))
    print()
    print(wrap("None of those five is the model being cleverer. Every one is something you built "
               "around it. That is scaffolding.", "  "))
    print()
    print("  Try things yourself:")
    flag = " --domain office" if office else ""
    print(f"    python run.py{flag} tickets                     the sample {unit}s")
    print(f"    python run.py{flag} ask --no-docs \"your question\"   ask with nothing attached")
    print(f"    python run.py{flag} ask \"your question\"            ask with the documents")
    print(f"    python run.py{flag} find \"your question\"           what the search found")
    print(f"    python run.py{flag} triage                      run YOUR instruction  [Lab 1]")
    other = "ag" if office else "office"
    print(f"\n  The same tour with the other example:  python run.py --domain {other} demo")


# ---------------------------------------------------------------------------
def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--verbose", "-v", action="store_true", help="show every step the system took")
    p.add_argument("--domain", choices=sorted(DOMAINS), default=current(),
                   help="which worked example to use: ag (equipment/agronomy) or office "
                        "(expenses). Works anywhere in the command.")
    sub = p.add_subparsers(dest="cmd")

    dm = sub.add_parser("demo", help="a guided five-minute tour — start here")
    dm.add_argument("--auto", action="store_true", help="do not pause between steps")
    dm.set_defaults(fn=cmd_demo)

    sub.add_parser("check", help="is everything set up?").set_defaults(fn=cmd_check)
    sub.add_parser("tickets", help="show the sample tickets").set_defaults(fn=cmd_tickets)
    sub.add_parser("docs", help="show the sample documents").set_defaults(fn=cmd_docs)

    t = sub.add_parser("triage", help="run your instruction over the tickets  [Lab 1]")
    t.add_argument("--ticket", help="just one ticket, e.g. T-007")
    t.set_defaults(fn=cmd_triage)

    a = sub.add_parser("ask", help="answer a question using the documents  [Lab 3]")
    a.add_argument("question", nargs="+")
    a.add_argument("--no-docs", action="store_true", help="answer without the documents, to compare")
    a.set_defaults(fn=cmd_ask)

    f = sub.add_parser("find", help="show which sections the search finds  [Lab 3]")
    f.add_argument("question", nargs="+")
    f.set_defaults(fn=cmd_find)

    sw = sub.add_parser("sweep", help="chunking / search mode / k vs recall@k  [Lab 3]")
    sw.add_argument("--k", type=int, default=5, help="how many chunks to retrieve (default 5)")
    sw.add_argument("--mode", choices=("keyword", "dense", "hybrid"), default="hybrid",
                    help="search mode for the chunking and k tables (default hybrid)")
    sw.set_defaults(fn=cmd_sweep)

    o = sub.add_parser("tools", help="let the assistant look things up  [Lab 4]")
    o.add_argument("question", nargs="+")
    o.add_argument("--no-tools", action="store_true", help="same question without tools, to compare")
    o.set_defaults(fn=cmd_tools)

    sc = sub.add_parser("score", help="score the assistant on the test set  [Lab 5]")
    sc.add_argument("--name", default="baseline", help="a name for this run")
    sc.add_argument("--judge", action="store_true", help="also use the AI judge")
    sc.add_argument("--runs", type=int, default=1, metavar="N",
                    help="score N times and report the spread — your noise floor")
    sc.set_defaults(fn=cmd_score)

    cp = sub.add_parser("compare", help="compare two scored runs  [Lab 5]")
    cp.add_argument("before")
    cp.add_argument("after")
    cp.set_defaults(fn=cmd_compare)

    args = p.parse_args()
    if not getattr(args, "fn", None):
        print(__doc__)
        return
    args.fn(args)


if __name__ == "__main__":
    main()
