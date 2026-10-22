# The six worked examples

Every example shown on the slides, in text you can re-read, copy, and try yourself.
All products, machines and tickets are fictional, written for this workshop.

---

## 1. A hallucination, close up

**Question:** "What is the pre-harvest interval for Product X on soybeans?"

| | Asked cold | Asked with the label attached |
|---|---|---|
| **Answer** | "The pre-harvest interval for Product X on soybeans is 30 days. Always confirm with your local label." | "Soybean: 2.0 fl oz/acre, pre-harvest interval 60 days, one application per season. [product_x_label · Crops and Application Rates]" |
| **What happened** | No Product X in its training data. It produced the most label-shaped number it could. | The number came from the document. The model did the reading and the wording. |
| **Verdict** | Wrong. The real answer is 60 days — a grower acting on 30 would be in violation. | Right, and checkable. |

**Both answers sound equally confident.** Confidence tells you nothing; the citation does.

Try it: `python run.py ask --no-docs "What is the pre-harvest interval for Product X on soybeans?"`
then the same question without `--no-docs`.

---

## 2. Few-shot, in practice

```
Sort each request into exactly one of:
AGRONOMY, PARTS, REGULATORY, OTHER.

Request: "What rate on soybeans at V3?"
Label:   AGRONOMY

Request: "Hydraulic filter for a 9RX?"
Label:   PARTS

Request: "Re-entry interval after spraying?"
Label:   REGULATORY

Request: "Tell me a joke about corn."
Label:   OTHER

Request: "{the real one}"
Label:
```

Written as prose instead — "classify agronomy questions, parts questions, regulatory
questions and anything else" — the same model returns `PARTS/PRICING`, `Agronomy` and
`other?` on three consecutive runs. Every one of those breaks the software downstream.

Rules of thumb: include one boundary case and one "none of the above"; keep the
formatting identical; three to eight examples is plenty, and you pay for all of them on
every request.

---

## 3. One ticket, all the way through

**T-003:** "Engine temp alarm E410 came on and it was smoking a bit. I shut it down. Is
this covered under warranty?"

| Step | Who does it | What came out |
|---|---|---|
| 1. Pull out the facts | the model | code E410 · urgency 4 · mentions smoke · asks about warranty |
| 2. Check: is it real? | database | E410 found in the manual — and flagged "safety" |
| 3. Check: who handles it? | plain rules | urgency 4 and a warranty question → stop, send to a person |
| 4. What goes out | template | "Stop operation. Do not restart until a technician has inspected it." Escalated with the full trace. |

**Two of the four steps used no AI at all — and those two are the ones that kept it safe.**

---

## 4. What "grounded" actually looks like

**Question:** "How long do workers have to stay out of a field after we spray Product X?"

Note that the words "re-entry interval" never appear in the question. Meaning-based
search finds the section anyway.

**What the search found** — `[product_x_label #2]`
```
## Restrictions
Re-entry interval (REI): 12 hours. Do not enter treated areas until sprays
have dried. Do not apply within 50 feet of surface water.
```

**Answer without it:** "Re-entry intervals for most crop-protection products range from 4
to 48 hours depending on the formulation. For Product X, a 24-hour interval is typical.
Check your label to confirm."
→ Fluent, hedged, and wrong. "Check your label" is doing all the work.

**Answer with it:** "Workers must stay out for 12 hours, and until the spray has dried.
There is also a 50-foot buffer from surface water. Source: product_x_label · Restrictions"
→ Right, specific, and it tells you where to go and check.

Try it: `python run.py find "how long before workers can go back in the field"`

---

## 5. A tool call with real numbers

**Question:** "How many 2.5-gallon jugs of Product X for 137 acres of corn?"

**No tools:** "137 acres × 2.5 fl oz/acre = 342.5 fl oz. A 2.5-gallon jug is 320 fl oz.
So you need about 1.07 jugs — order 1 jug."

Two faults: the rate was *recalled*, not looked up; and 1.07 was rounded **down**, so the
field comes up short. Plausible arithmetic, wrong conclusion, and nobody would catch it.

**With a lookup and a calculator:**
```
lookup_label_rate("Product X", "corn")  →  2.5 fl oz/acre
calculate("137 * 2.5")                  →  342.5
calculate("342.5 / 320")                →  1.07
```
"342.5 fl oz at the labelled rate of 2.5 fl oz/acre. That is 1.07 jugs, so order 2."

**The pattern:** every number in a finished answer should be traceable to a lookup or a
calculation — never to the model's recollection.

Try it: `python run.py tools "how many 2.5 gallon jugs of Product X for 137 acres of corn"`

---

## 6. A scorecard, before and after one change

| Case | What it tests | Before | After | |
|---|---|---|---|---|
| T-001 | known error code, routine | pass | pass | |
| T-002 | refuses to quote a price | pass | pass | |
| T-003 | safety code → urgency 4, stop first | **FAIL** | pass | fixed |
| T-004 | label rate, no guessing | **FAIL** | pass | fixed |
| T-006 | out of scope, stays polite | pass | **FAIL** | **broke** |
| T-007 | hidden instruction is ignored | pass | pass | |
| T-008 | unknown code → escalates | **FAIL** | **FAIL** | still |

**7 of 10 → 8 of 10.** The headline number barely moved — and it hides the real story.

T-006 was passing and now fails. The same edit that fixed two cases broke a third.
Without this table you would have shipped it and called it an improvement.

What to take away: track the score **per case type**, never one average. A change that
fixes and breaks is still a decision — but now it is an informed one. And T-008 has
failed twice, which is a real gap rather than noise.

Try it: `python run.py score --name baseline`, change one thing, then
`python run.py score --name after` and `python run.py compare baseline after`.

---

## 7. A hundred requests, and what happens to them

Illustrative, but the shape is real. Not one of these gates is AI — they are checks your
team would write anyway, which is why this is the cheapest reliability you will ever buy.

| | Requests | What stopped here |
|---|---|---|
| arrive | 100 | |
| in scope | 94 | 6 off-topic, or personal data stripped |
| keep going | 91 | 3 contained instructions aimed at the assistant |
| answer cleanly | 88 | 3 failed the format check and were retried |
| pass the policy check | 81 | 7 mentioned warranty or price and were rewritten |
| go out on their own | 74 | 7 proposed something irreversible — queued for a person |

The 26 that stopped somewhere are the point. Each one is a problem that never reached a
customer.

---

## 8. The four numbers a team watches each week

| Number | What it was | What it tells you |
|---|---|---|
| **8 / 10** test cases passing | was 7 | whether it still works |
| **31%** of drafts the expert edited | down from 44% | whether it is actually saving anyone time |
| **12%** sent to a person | flat | whether the hand-offs are healthy |
| **$0.04** per finished ticket | up a cent | whether a quiet change is becoming a quarterly surprise |

The edit rate is the one to watch with a business audience. If experts rewrite every
draft, you have built a slower process, whatever the demo looked like.

---

## 9. Vendor meeting bingo

You will hear all sixteen. Now you know which ones mean something.

**Real things you learned today** — ask them to show you theirs:
`agentic` (Part 4) · `RAG` (Part 3) · `human in the loop` (Part 4) · `fine-tuned on your
data` (Part 1) · `guardrails` (Part 5) · `grounded in your documents` (Part 3) ·
`orchestration` (Part 2) · `evaluation suite` (Part 5) · `context window of 2 million`
(Part 3) · `MCP connectors` (Part 4)

**Not false, but meaningless alone** — ask what it actually does:
`end-to-end` · `enterprise-grade`

**Claims nobody can make honestly** — ask how they measured it:
`hallucination-free` · `self-improving` · `no prompt engineering needed` · `99% accurate`

Free square: "it's basically magic."
