# Capstone — find the weakest link

**30 minutes.** Pair up across tracks: one person scores, one person changes.

---

## Step 1 — Run the whole thing (8 min)

The complete assistant sorts each incoming request, then handles it with the
right approach: troubleshooting goes down the assembly line, agronomy questions
go to the documents, label questions go to the lookup tool, parts and pricing go
to a person.

Run all ten tickets (`python capstone.py`, or work through them in the chat
tool), and score:

| Ticket | Kind | Handled well? | What went wrong |
|---|---|---|---|
| T-001 | troubleshoot | ☐ | |
| T-002 | parts | ☐ | |
| T-003 | safety | ☐ | |
| T-004 | regulatory | ☐ | |
| T-005 | troubleshoot | ☐ | |
| T-006 | out of scope | ☐ | |
| T-007 | injection | ☐ | |
| T-008 | unknown code | ☐ | |
| T-009 | agronomy | ☐ | |
| T-010 | agronomy | ☐ | |

**Score: ____ / 10**

---

## Step 2 — Diagnose (7 min)

Pick the single worst failure. Not the most common — the worst, meaning the one
that would cause the most damage if it reached a real customer.

The failure:

> _______________________________________________________________________

Why is it the worst?

> _______________________________________________________________________

Now place it. Which part of the day does it belong to?

- ☐ **Instructions** — it was not told clearly enough what to do
- ☐ **Steps** — the job was not broken up, or a check was missing
- ☐ **Memory** — it did not have, or did not find, the right material
- ☐ **Tools** — it guessed instead of looking up, or acted without approval
- ☐ **Trust** — nobody would have noticed this until a customer did

---

## Step 3 — Fix one thing (10 min)

Agree **one** change with your partner. The non-coder decides what should change
and why; the coder decides how.

What changes:

> _______________________________________________________________________

Prediction — which tickets will move?

> _______________________________________________________________________

Re-run and re-score. **After: ____ / 10**

What actually moved?

> _______________________________________________________________________

---

## Step 4 — Report to the room (5 min)

Two minutes, both of you:

1. What broke, and why it mattered
2. Which of the five parts it belonged to
3. What you changed
4. What moved — including anything that got worse

The most useful reports are the ones where the fix broke something else.
