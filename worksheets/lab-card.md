# Table card — keep this next to your laptop

**Pick your example.** Everything works with either. Add `--domain office` to any command
below for the expense-claims version; leave it off for equipment and agronomy.

---

## Start here

```
python run.py demo
```

A guided five-minute tour. Press Enter between steps. Nothing to edit, nothing saved.

---

## The commands you will use today

| Lab | Type this | What you will see |
|---|---|---|
| — | `python run.py check` | is everything set up? |
| — | `python run.py demo` | the five-minute tour |
| — | `python run.py tickets` | the ten sample tickets/claims |
| — | `python run.py docs` | the documents the assistant can use |
| **1** | `python run.py triage` | runs YOUR instruction over all ten |
| **1** | `python run.py triage --ticket T-007` | just the tricky one |
| **3** | `python run.py ask --no-docs "..."` | answered from memory alone |
| **3** | `python run.py ask "..."` | answered from the documents |
| **3** | `python run.py find "..."` | which sections the search found |
| **4** | `python run.py tools "..."` | watch it look something up |
| **4** | `python run.py tools --no-tools "..."` | the same question, guessing |
| **5** | `python run.py score --name baseline` | score it on the test set |
| **5** | `python run.py compare baseline after` | what your change moved |

Add `--verbose` to any command to see every step the system took.

---

## Lab 1: where your instruction lives

Open **`my_instruction.txt`** in any text editor (`my_instruction_office.txt` for the
office example). It is plain text, not code. Lines starting with `#` are notes to
yourself and are not sent to the AI.

Edit it, save it, and run `python run.py triage` again.

---

## If something breaks

| It says | Do this |
|---|---|
| `python: command not found` | try `python3` instead, everywhere |
| `No module named 'scaffold'` | you are in the wrong folder — `cd llm-scaffolding-workshop` |
| `No module named ...` | `pip install -r requirements.txt` |
| something about a key or provider | read the two lines it prints; they name the fix |
| nothing works and the lab has started | open `worksheets/chat-track.md` (or `chat-track-office.md`) — every lab works in ChatGPT or Claude with nothing installed |

You will not fall behind. Every lab also has a paper version in `worksheets/`, and
everything runs without an API key.

---

## The three tickets worth staring at

| Equipment example | Office example | Why |
|---|---|---|
| **T-003** smoke + a warranty question | **C-003** over the hotel cap, "just approve it" | should it be urgent, and must a person see it? |
| **T-007** a hidden "SYSTEM OVERRIDE" | **C-007** the same trick | did it get flagged, or obeyed? |
| **T-008** an error code nobody knows | **C-008** one purchase split in two | did it refuse, or invent something? |
