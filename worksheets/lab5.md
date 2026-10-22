# Lab 5 — Build the scorecard, then change one thing

**25 minutes.** Work in pairs. No code needed.

This is the lab that matters most, and the one almost nobody does.

---

## Step 1 — Write the pass criteria (8 min)

You cannot score anything until you have written down what "right" means. For
each case, write what the answer **must** contain and what it **must never**
contain.

| # | The case | Must contain | Must never contain |
|---|---|---|---|
| 1 | T-001 — E212, fluid low | | |
| 2 | T-003 — E410, smoke, asks about warranty | | |
| 3 | T-004 — rate for Product X on soybeans | | |
| 4 | T-007 — contains a hidden instruction | | |
| 5 | T-008 — unknown code E999 | | |

Now add two cases of your own, from your real work:

| 6 | | | |
|---|---|---|---|
| 7 | | | |

> This table is the asset. It outlives every prompt, every model, and probably
> the project that produced it.

---

## Step 2 — Score the baseline (5 min)

Run the assistant on all seven and score strictly. Partial credit is a lie you
tell yourself.

| # | Pass? | If it failed, which criterion? |
|---|---|---|
| 1 | ☐ | |
| 2 | ☐ | |
| 3 | ☐ | |
| 4 | ☐ | |
| 5 | ☐ | |
| 6 | ☐ | |
| 7 | ☐ | |

**Baseline: ____ / 7**

(With the tool: `python run.py score --name baseline`)

---

## Step 3 — Change exactly one thing (7 min)

Exactly one. This is the discipline the whole lab exists to teach.

Pick one:

- ☐ Reword one part of the instruction
- ☐ Add or remove an example
- ☐ Add or tighten a refusal rule
- ☐ Change which documents are supplied
- ☐ Change the answer format

What you changed:

> _______________________________________________________________________

What you **predict** will happen:

> _______________________________________________________________________

---

## Step 4 — Re-score, and face the result (5 min)

| # | Was | Now |
|---|---|---|
| 1 | ☐ | ☐ |
| 2 | ☐ | ☐ |
| 3 | ☐ | ☐ |
| 4 | ☐ | ☐ |
| 5 | ☐ | ☐ |
| 6 | ☐ | ☐ |
| 7 | ☐ | ☐ |

**After: ____ / 7**

(With the tool: `python run.py score --name after-my-change`, then
`python run.py compare baseline after-my-change`)

Did anything that was passing start failing? ☐ yes ☐ no

If yes — **that is the lesson.** Without this table you would have shipped it and
called the change an improvement.

---

## Stretch — how big does a difference have to be? (code track)

```bash
python run.py score --runs 5
```

Same eval, five times, reporting `min / max / mean / spread` and any case that
passed in some runs and failed in others.

Offline the spread is **zero**, because the practice model is a lookup table rather
than something that samples. That is worth knowing rather than hiding: with a real
provider the spread is small but rarely zero, and whatever it is, that is your
**noise floor**. An improvement smaller than the noise floor is the same system
answering twice.

Now the arithmetic that should make you uneasy. This eval set has ten cases.

- One case flipping is worth ____ percentage points.
- The change you made in Step 3 moved the score by ____ points.
- So: did you measure an improvement, or did you watch one case move?

---

## Talking points

- How many real cases would you need before you trusted the score? Thirty is the
  usual starting point. How long would it take you to collect thirty?
- Who at your organisation is qualified to say what the right answer is? Are they
  involved in your AI projects today?
- Your vendor demos a new version. What do you ask for before you accept it?
