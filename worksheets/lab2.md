# Lab 2 — Break the job into steps

**30 minutes.** Work in pairs. No code needed.

In Lab 1 you asked for one thing. Here you design the whole line, and decide
where the checks go — including which steps need no AI at all.

---

## Step 1 — Map the line (8 min)

Take the dealer support job, or better, a real process from your own team. Write
the steps. Four to six is usually right.

| # | Step | Does this need AI? | Why / why not |
|---|---|---|---|
| 1 | | ☐ AI  ☐ ordinary software  ☐ a person | |
| 2 | | ☐ AI  ☐ ordinary software  ☐ a person | |
| 3 | | ☐ AI  ☐ ordinary software  ☐ a person | |
| 4 | | ☐ AI  ☐ ordinary software  ☐ a person | |
| 5 | | ☐ AI  ☐ ordinary software  ☐ a person | |

> If every row says "AI", look again. In a well-built system, most steps do not.

---

## Step 2 — Design the checkpoints (8 min)

Between every two steps there is a gap. Write the check that goes in it.

| Between steps | The check, in plain English | What it needs to know | What happens if it fails |
|---|---|---|---|
| 1 → 2 | | | |
| 2 → 3 | | | |
| 3 → 4 | | | |
| 4 → 5 | | | |

Each check should be one of these four kinds:

- **Complete and well-formed** — are all the fields there, in the right range?
- **Exists in our records** — is that code, part, or product real?
- **Sensible** — is the number plausible, is the date in the future?
- **Allowed** — no banned claims, no personal data, no competitor mentions.

---

## Step 3 — Where does it go to a person? (5 min)

"Send it to a person" is a proper outcome, not a failure. List every condition
that should trigger it:

1. _______________________________________________________________________
2. _______________________________________________________________________
3. _______________________________________________________________________
4. _______________________________________________________________________

And then: **who** is that person, and how do they find out?

> _______________________________________________________________________

---

## Step 4 — Run two steps by hand (9 min)

Pick two steps from your line and run them in the chat tool, one at a time, on
ticket T-001 and ticket T-003.

Pass the output of step 1 into step 2 yourself. That hand-off is exactly what
the software does.

| | T-001 | T-003 |
|---|---|---|
| Step 1 output | | |
| Did your checkpoint pass? | | |
| Step 2 output | | |
| Would you send this to a customer? | | |

---

## Talking points

- Which checkpoint would have caught your most expensive real-world mistake?
- Which of your steps could run on a cheaper, faster model — and how would you
  know if that were a bad idea?
- Compare your line with your partner's. Did either of you put a check where the
  other did not?
