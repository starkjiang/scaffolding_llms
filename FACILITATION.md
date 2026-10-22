# Running the hands-on sessions

Everything in this file is for the instructor. The participant-facing pieces are
`worksheets/lab-card.md` (print one per seat) and `SETUP.md`.

The single biggest risk to a hands-on workshop is spending the first forty minutes
installing Python. Almost everything below exists to stop that happening.

---

## 0. Read `WALKTHROUGH.md` once

About 45 minutes. It explains every module and every lab in order, with the exact
commands to run as you read. Knowing where participants get stuck is worth more than
any other preparation.

---

## 1. Two weeks before — the setup email

Send this, then send it again three days before. Expect roughly half the room to do it.
That is fine; the other half has a no-code path.

> **Subject: Before the Scaffolding LLMs workshop — 10 minutes of setup**
>
> Hello,
>
> Looking forward to seeing you on [date]. Two things to do beforehand, and one thing
> to think about.
>
> **1. Bring a laptop.** You will use it for about half the day.
>
> **2. If you are comfortable installing software, do this once before you arrive**
> — it takes about ten minutes and saves you a scramble on the day:
>
> ```
> [repository link]
> cd llm-scaffolding-workshop
> python -m venv .venv
> source .venv/bin/activate          # Windows: .venv\Scripts\activate
> pip install -r requirements.txt
> python run.py check
> ```
>
> If the last line prints a setup summary, you are done. If anything fails, do not
> spend more than fifteen minutes on it — reply to this email and we will sort it out
> on the day.
>
> **If you would rather not install anything, that is completely fine.** Every exercise
> has a version that runs in a normal chat tool (ChatGPT, Claude, Copilot — whatever
> your company allows). Just bring the laptop and a browser.
>
> **3. Think of one problem from your own work** where you suspect AI might help, or
> where someone has already asked you whether it could. You will use it in the
> discussion breaks. It does not need to be well formed.
>
> No preparation beyond that. See you on [date].

**Three days before**, resend with one addition: *"If you got the setup working, reply
'done'."* The count tells you how to run the first lab.

---

## 2. The morning of

- [ ] Write on the whiteboard, and leave it there all day:
      `python run.py demo`  ·  `--domain office`  ·  `worksheets/`
- [ ] Put a printed `lab-card.md` on every seat.
- [ ] Have the repository on a USB stick **and** a short link. Venue Wi-Fi fails.
- [ ] Run `python run.py demo --auto` once on the presenting machine, on venue Wi-Fi.
- [ ] If you have API keys, put them on a slide or a slip of paper per table, not in chat.
- [ ] Decide your fallback: if the network dies, everyone runs in practice mode. Say so
      cheerfully; it changes nothing about the labs.

---

## 3. The first ten minutes of hands-on time — do this together

**Do not start with Lab 1.** Start with everybody typing the same thing and seeing the
same thing. One shared win before anybody diverges.

> "Everyone open a terminal and type exactly this: `python run.py check`.
> Hands up if you got a block of text that says 'You are ready.'"

Count the hands. Then:

> "Now type `python run.py demo` and press Enter between each step. Five steps, about
> five minutes. Read what comes back. I will walk around."

While they run it, circulate and solve setup problems. The demo is deliberately
self-narrating, so you do not need to talk over it — spend the time on the people whose
laptops are unhappy.

Bring the room back together with one question:

> "Step 1 gave an answer. Step 2 gave a different one. What actually changed?"

Somebody will say "it had the document." That is Part 3, discovered rather than
lectured. Then start Lab 1.

**Anyone still broken after ten minutes** goes to `worksheets/chat-track.md`, or
`chat-track-office.md` for the expense example — every lab as paste-ready text for
whatever chat tool they already have — and pairs and pairs with a
working neighbour. Say this out loud and without drama — it is a legitimate path, not a
consolation prize, and a mixed pair is the best pair anyway.

---

## 4. Running each lab

A rhythm that works, roughly 25–30 minutes per lab:

| Minutes | What happens | What you say |
|---|---|---|
| 0–2 | Set it up | Show the lab slide. Read the goal aloud. Name both tracks. |
| 2–5 | They start | Circulate. Do not answer questions yet; let them read. |
| 5–8 | First checkpoint | "Hands up if you have run it once." Fix stragglers. |
| 8–20 | Work | Circulate constantly. Listen more than you talk. |
| 20–22 | The pivot | Call out the one thing most pairs are missing. |
| 22–28 | Finish | "Five minutes — make sure you have something to report." |
| 28–30 | Debrief | Two or three pairs report. You synthesise. |

**The pivot matters.** About two-thirds through, stop the room and name the sticking
point you have been watching. Known ones:

- **Lab 1** — people write a long, vague instruction. Pivot: *"Add one sentence saying
  what to do when the ticket does not say. Just one. Run it again."*
- **Lab 2** — people put AI in every step. Pivot: *"Which of your steps could a database
  do? Mark them. That is usually half."*
- **Lab 3** — people conclude the model is bad when the search was bad. Pivot:
  *"Run `find` on the question it got wrong. Did it even retrieve the right page?"*
- **Lab 4** — people write a thin tool description. Pivot: *"Read your description back
  as if you were the model. Would you know when to use it?"*
- **Lab 5** — people change three things at once. Pivot: *"Change one. Only one. The
  whole lab is about being able to say what caused what."*

**Debriefs: ask for failures, not successes.** "Who got something surprising?" produces
better discussion than "who got it working?" and it lets the pairs who struggled
contribute something valuable.

---

## 5. Handling the mixed room

- **Seat people across tracks from the start.** Say at the beginning of the day: "Find
  someone whose job is different from yours." The expert defines correct; the builder
  makes it happen. Neither gets there alone, and the Capstone depends on it.
- **Name the no-code track as equal, repeatedly.** The worksheets are not a fallback —
  they cover the half of the work that actually determines whether a project succeeds.
- **When a non-technical attendee asks "what am I looking at?"** — that is the signal to
  switch examples. `--domain office` needs no industry knowledge at all.
- **Let the fast finishers help.** "If you are done, find someone who isn't." It is
  better than giving them extra work, and it is how the room scales past one instructor.

---

## 5b. When the room is mostly data scientists and data engineers

A technical room is not a harder room — it is a room whose instincts are *adjacent*
to this material and wrong in specific places. Lean on that rather than on more theory.

**Lead with the bridge slide.** "What you already know, and where it breaks" (Part 0,
`FOR BUILDERS`) maps unit test → eval, feature store → retrieval, schema → structured
output, idempotent write → tool call. Spend five minutes there and ask which row has
already bitten someone. With a DS/DE-heavy room that slide lets you move fast through
the next three: the model mechanism, the three limitations, and good-at/bad-at are all
material they have.

**Do not cut the plain-language slides — demote them.** Deliver the analogy as a
single caption and move on. The brilliant-new-hire table, the kitchen line and the
intern dial are each worth one sentence to this room and five minutes to a mixed one.
Watch the faces on the first analogy and calibrate.

**The five slides that carry this audience**, and the ones to protect if you run late:

| Slide | Part | Why it lands |
|---|---|---|
| What you already know, and where it breaks | 0 | Gives them the whole day's map in their own vocabulary |
| The knobs you can actually turn | 1 | "Temperature 0 is not determinism" is the line they write down |
| When a step fails — and it will | 2 | Retries, idempotency, partial failure. The data engineers have been waiting for it |
| The retrieval ceiling | 3 | Real numbers, run live, where the aggregate hides the failure |
| Is the difference real? | 5 | Noise floor, n, judge agreement. Expect an argument — that is the goal |

**Run two commands live.** Both take seconds and need no key:

```bash
python run.py sweep          # recall moves 0.400 → 0.800 on the hard half
python run.py score --runs 5 # the noise floor (zero offline — say why)
```

The sweep is the strongest five minutes in the deck for this audience, because the
numbers on screen are the numbers on the slide. Finish it with the question that
actually changes behaviour: *who wrote your eval set — the same person who wrote the
documents?*

**Where they will push back, and the honest answer:**

- *"Isn't this just RAG plus prompt engineering?"* Largely, yes. The claim is that the
  engineering around the model decides the outcome more than the model choice does,
  and the sweep is the evidence.
- *"Why not fine-tune?"* Fine-tuning moves style and format reliably, and facts badly.
  Everything that changes weekly belongs in retrieval.
- *"Our vendor says they handle all this."* Good — then ask them for recall@k on your
  own questions, the eval set, and the noise floor. Part 5 is a procurement checklist.

**What you can safely shorten:** the Part 0 model mechanism, the jargon material (it
is in `worksheets/glossary.md` and was deliberately cut from the deck), and the
analogy slides in Parts 2 and 5. That buys roughly 40 minutes, which is what the five
slides above and the two live commands cost.

---

## 5c. Running the day with real API keys

Practice mode teaches the plumbing. Real keys add the one thing it cannot fake:
**answer quality**, which is what Lab 1 and Lab 5 are actually about. If you have a
key, use it — but set it up like this rather than handing out one key and hoping.

### Two weeks before

1. **Confirm the model IDs still exist.** IDs retire on a published schedule and a
   retired ID fails every request. Check the list for your provider —
   [OpenAI](https://developers.openai.com/api/docs/models) or
   [Anthropic](https://platform.claude.com/docs/en/models/overview) — and check it
   again the week of the workshop. `.env.example` has a table of the current
   small/large pairs for both.
2. **Run the whole repo end to end against the real key yourself**, both domains.
   This is the step people skip:

   ```bash
   python run.py check
   python run.py demo --auto
   python run.py score --judge --runs 3
   python capstone.py eval
   python run.py --domain office demo --auto
   ```
3. **Set a hard spend cap on the key in the console.** Not a reminder — a cap.
4. **Measure your own cost for one full pass** and multiply by the headcount. One
   attendee working hard through every lab is a small number of dollars, not tens,
   but measure rather than trust anyone's estimate including this file's. Add
   `--verbose` to any command to see the per-call input and output token counts.
5. **On OpenAI, set the reasoning effort down.** The current models default to
   medium reasoning effort, which the labs do not need — most steps are
   classification and extraction. Put `OPENAI_REASONING_EFFORT=low` in `.env`
   before you measure the cost in step 4, or you will measure the wrong number.
   An unsupported value is dropped automatically with a printed note, so trying
   `none` costs you nothing but one wasted request.

### Which key goes to whom

| Option | When it fits | Watch out for |
|---|---|---|
| One key per attendee, issued on the day | Smaller rooms, partner org can issue them | Fifteen minutes of setup time; budget for it |
| One key per table of 4–5 | The usual sweet spot | Tables hit rate limits together during Lab 5 |
| One shared key for the room | Only if you have no alternative | A 25-person room running `score` at once will hit per-minute token limits |

Put keys on paper or in a sealed per-table envelope. Do not put them on a slide,
and **revoke every key at the end of the day** — this is the single most common
loose end from a hands-on workshop.

### Rate limits are a scheduling problem

The expensive moments are the ones that fan out: `score` runs the whole chain over
ten cases, `--judge` adds a second model call per case, and `--runs 5` multiplies
all of it. Thirty people doing that simultaneously is a burst.

- Stagger Lab 5: ask half the room to write their pass criteria while the other
  half scores, then swap.
- Keep `--judge` and `--runs` as the **stretch** steps, not the main path.
- Tell the room up front that a rate-limit error is expected, is not their fault,
  and is itself a Part 2 lesson — then point at the "When a step fails" slide.

### What to run live from the front

Use your own key for these, so a room-wide limit never touches them:

- The cold-versus-grounded pair from Part 0. With a real model the confidently
  wrong answer is far more persuasive than the scripted one.
- `run.py tools --no-tools` versus with tools, in Part 4.
- `run.py sweep` — but note this one needs **no key at all**: retrieval, chunking
  and scoring are real in practice mode. Only the model's wording is simulated.

### The fallback, which you should rehearse

If keys fail, the venue network dies, or a provider has an incident, say this and
keep going:

> "We're switching to practice mode. Everything in every lab still runs. The only
> difference is that the model's wording is simulated — the retrieval, the tools,
> the gates, the evals and the traces are all real."

Then have everyone run `LLM_PROVIDER=mock python run.py check` (Windows:
`set LLM_PROVIDER=mock`). Budget two minutes for this, not twenty. Having said it
calmly once is the difference between a blip and a lost hour.

---

## 6. If the day goes sideways

| Problem | What to do |
|---|---|
| Network is dead | Everyone runs in practice mode. Nothing changes. Say so immediately and move on. |
| API keys fail or run out | Same — practice mode. The labs teach the same thing. |
| Half the room cannot install | Switch everyone to the paper track for Lab 1, fix laptops over the break. |
| A lab is running long | Cut Lab 4 to a demo you drive from the front. Protect Lab 5; it is the one that changes behaviour. |
| Nobody is talking in the debrief | Ask a specific pair by name about a specific thing you watched them hit. |
| Someone is far ahead | Point them at the stretch goal on the lab slide, or ask them to help a neighbour. |
| Someone is lost and quiet | Sit with them for two minutes. It is nearly always one typo or the wrong folder. |

---

## 7. What to collect at the end

- The score each pair reached in Lab 5, on the whiteboard. Seeing the spread is useful.
- One failure per pair, written on an index card. These are the best material for the
  next run of the workshop, and they tell you what your own examples are missing.
- A show of hands on `--domain office` versus the equipment example. It tells you which
  audience actually turned up.
