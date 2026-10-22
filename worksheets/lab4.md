# Lab 4 — Tools: looking things up instead of guessing

**25 minutes.** Work in pairs. No code needed.

---

## Step 1 — Ask for numbers with nothing to look them up in (5 min)

In your chat tool, or with `python run.py tools --no-tools "..."`:

| # | Question | The number it gave | The real answer | Right? |
|---|---|---|---|---|
| 1 | What is the labelled rate of Product X on corn? | | 2.5 fl oz/acre | ☐ |
| 2 | What is the pre-harvest interval for Product Y on soybeans? | | 21 days | ☐ |
| 3 | How many 2.5-gallon jugs of Product X for 137 acres of corn? | | 2 (342.5 fl oz) | ☐ |
| 4 | Is Product Y labelled for wheat? | | No — corn and soybean only | ☐ |

Note especially question 4. A confident "yes, at 4 fl oz/acre" is the most
dangerous kind of wrong answer, because it looks exactly like a right one.

---

## Step 2 — Give it the lookup table (7 min)

Paste this in and ask the same four questions again:

```
LABEL DATA — use only this table. If a product/crop pair is not listed,
say it is not labelled for that crop. Do not estimate.

Product X   corn      2.5 fl oz/acre   max 2/season   PHI 45 days   REI 12 h
Product X   soybean   2.0 fl oz/acre   max 1/season   PHI 60 days   REI 12 h
Product X   wheat     1.5 fl oz/acre   max 1/season   PHI 30 days   REI 12 h
Product Y   corn      6.0 fl oz/acre   max 2/season   PHI 14 days   REI 4 h
Product Y   soybean   4.0 fl oz/acre   max 2/season   PHI 21 days   REI 4 h
```

| # | Answer now | Right? |
|---|---|---|
| 1 | | ☐ |
| 2 | | ☐ |
| 3 | | ☐ |
| 4 | | ☐ |

Which question is still risky even with the table? Why?

> _______________________________________________________________________

(Hint: question 3 requires arithmetic. A table fixes the *facts*; it does not
fix the *maths*. That is what a calculator tool is for — try
`python run.py tools "how many 2.5 gallon jugs of Product X for 137 acres of corn"`
and watch it call the calculator.)

---

## Step 3 — Design a tool (7 min)

Pick something your team looks up constantly. Write the description an assistant
would read to decide whether to use it. This description *is* the instruction —
write it like one.

**Name of the tool:**

> _______________________________________________________________________

**When should it be used?**

> _______________________________________________________________________

**When should it NOT be used?**

> _______________________________________________________________________

**What does it need to be told?** (Keep it to two or three things, with fixed
choices where possible.)

| Input | Format or allowed values |
|---|---|
| | |
| | |

**What comes back?**

> _______________________________________________________________________

**What happens when there is no answer?**

> _______________________________________________________________________

---

## Step 4 — The approval rule (6 min)

Now a tool that *changes something*: creating a work order.

Run `python run.py tools "The manual says E212 needs a dealer pump inspection. Create a work order for HX-900."`
and read the last few lines. Nothing was created. It is waiting for a person.

Write the approval rule you would require at your own organisation:

| Question | Your answer |
|---|---|
| Who approves? | |
| What do they need to see to decide? | |
| How long do they have before it expires? | |
| What is logged? | |
| What happens if they are on holiday? | |

---

## Talking points

- Which of your systems should an assistant be allowed to *read*? Which should
  it be allowed to *write* to — and under what approval?
- The assistant will read documents that came from outside your company. What
  stops a planted instruction in one of those from triggering a tool?
- "Five to fifteen well-described tools beat fifty vague ones." Why?
