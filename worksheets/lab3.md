# Lab 3 — Memory: answering from documents

**30 minutes.** Work in pairs. No code needed.

The point of this lab is to feel the difference between an assistant answering
from memory and the same assistant answering from the right page.

---

> **Office version:** use these five questions instead, with
> `python run.py --domain office ask --no-docs "..."` — what is the daily meal cap in
> Chicago? the nightly hotel cap in New York? the mileage rate? can I claim a beer with
> dinner? who signs off on a $4,000 purchase? The answers are in `data/office/docs/`.

## Step 1 — Ask with no documents (6 min)

Ask these five questions in your chat tool with **nothing attached**, or run
`python run.py ask --no-docs "..."`.

| # | Question | What it answered | Right? |
|---|---|---|---|
| 1 | What is the labelled rate of Product X on soybeans? | | ☐ |
| 2 | What is the re-entry interval for Product X? | | ☐ |
| 3 | How long after spraying Product Y on soybeans can I harvest? | | ☐ |
| 4 | What should an operator do when an HX-900 shows E410? | | ☐ |
| 5 | What is the hydraulic filter part number for the HX-900? | | ☐ |

The real answers are in `../data/docs/`. **Do not look yet.**

Before you check: how confident did the answers *sound*, on a scale of 1–5? ____

Now check them. How many were actually right? ____ / 5

> This gap — between how confident it sounded and how right it was — is the
> single most important thing to understand about these systems.

---

## Step 2 — Ask with the documents (8 min)

Open `../data/docs/product_x_label.md`, `product_y_label.md`, and
`harvester_manual.md`. Paste the relevant one in, then ask again. Add this line:

> "Answer using only the document above. If it does not say, tell me it does not
> say. Quote the section you used."

| # | Answer with the document | Right? | Did it cite a section? |
|---|---|---|---|
| 1 | | ☐ | ☐ |
| 2 | | ☐ | ☐ |
| 3 | | ☐ | ☐ |
| 4 | | ☐ | ☐ |
| 5 | | ☐ | ☐ |

Score now: ____ / 5

---

## Step 3 — Break the search (8 min)

Attaching the right page by hand is easy. A real system has to *find* it. Try
these, using `python run.py find "..."` if you have it, or by searching the
document yourself with Ctrl-F:

| Question | Would a plain keyword search find the right section? |
|---|---|
| "re-entry interval Product X" | ☐ yes ☐ no |
| "how long before workers can go back in the field" | ☐ yes ☐ no |
| "HX-F-4410" | ☐ yes ☐ no |
| "what filter do I need for low hydraulic pressure" | ☐ yes ☐ no |

Two of these fail with keyword search alone. Which two, and why?

> _______________________________________________________________________

That is why real systems search by meaning **and** by exact words, and merge the
results.

---

## Step 4 — The one that still fails (8 min)

Find a question that is answerable from the documents but that the assistant
still gets wrong or refuses.

The question:

> _______________________________________________________________________

Is the problem **finding** the right section, or **using** it once found?

> ☐ finding    ☐ using    ☐ not sure

That distinction decides who fixes it and how. Getting it wrong costs teams
weeks.

---

## Stretch — turn the knobs and watch recall move (code track)

```bash
python run.py sweep
python run.py sweep --domain office --k 10 --mode dense
```

Three tables: chunking, search mode, and how many chunks you retrieve. Every row
is split into **easy** and **hard** questions — easy ones are worded the way the
document is worded, hard ones the way a person types.

Two things to look for:

1. The hard column moves from **0.400 to 0.800** on chunk size alone. Nothing about
   the model or the prompt changed.
2. The easy column reads **1.000 in every row**. It cannot move. An eval set made
   only of easy questions will tell you retrieval is perfect forever.

Write down the answer to this one, because it is the question to take back to work:

Who would write the test questions for your documents — and would they write easy
ones or hard ones?

_______________________________________________________________________________

---

## Talking points

- Which documents in your organisation would an assistant need? Who owns them,
  and how often do they change?
- What happens when two versions of a document disagree?
- Should everyone be able to see every answer the assistant can produce?
