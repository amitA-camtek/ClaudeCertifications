# Weakest-Domain Deep Dive — Plan Template

Fill this in on Thursday of W12, immediately after Wednesday's full practice exam. This is your structured plan for the one day you'll spend drilling your weakest area. Don't skip the diagnosis step — drilling the wrong domain wastes the whole session.

---

## Step 1 — Diagnosis (10 minutes)

Pull your Practice Exam 2 results and Practice Exam 1 results (from W11). For each of the 5 domains, compute your accuracy.

| Domain | Weight | PE1 score | PE2 score | Average | Questions missed |
|---|---|---|---|---|---|
| 1. Agentic Architecture & Orchestration | 27% | __ / __ | __ / __ | __% |  |
| 2. Tool Design & MCP Integration | 18% | __ / __ | __ / __ | __% |  |
| 3. Claude Code Configuration & Workflows | 20% | __ / __ | __ / __ | __% |  |
| 4. Prompt Engineering & Structured Output | 20% | __ / __ | __ / __ | __% |  |
| 5. Context Management & Reliability | 15% | __ / __ | __ / __ | __% |  |

**Weakest domain (lowest average):** _______________
**Second-weakest:** _______________

If the gap between weakest and second-weakest is small (< 5 percentage points), treat both as weak — alternate between them during this session.

If any domain is below 50%, that domain alone is the focus; a 27%-weighted domain at 40% accuracy alone can sink you below 720/1000.

---

## Step 2 — Root-cause the misses (30 minutes)

For the weakest domain, write down every question you missed. For each, identify the failure mode:

| Q# | What was the question about? | Which option did I pick? | Which was correct? | Why did I pick the wrong one? |
|---|---|---|---|---|
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

Tag each miss with one of:

- **[KNOWLEDGE GAP]** — I did not know the fact being tested.
- **[DISTRACTOR TRAP]** — I knew the material but fell for a distractor (prompt-rule bait, sentiment trigger, "every agent every tool", etc.).
- **[MISREAD]** — I misread the scenario or the options.
- **[TIME PRESSURE]** — I rushed and skipped the elimination procedure.

Distractor traps and time-pressure misses are fixable on exam day with the playbook. Knowledge gaps need content review.

---

## Step 3 — Map misses to task statements (10 minutes)

For each miss, identify which task statement (1.1, 2.3, 4.4, etc.) it tests. Cross-reference the domain cheat sheet section in `exercises/domain_cheatsheet.md` and the relevant W0N reference.md.

| Q# | Task statement | Reference file |
|---|---|---|
|  |  | `12-week-program/W0N_Name/reference.md` |
|  |  |  |
|  |  |  |

---

## Step 4 — Targeted content review (45 minutes)

Based on the task statements clustered in Step 3, identify 1–3 specific sections to re-read. Don't re-read the whole reference — re-read only the sections that map to your misses.

Plan:
- [ ] Re-read `12-week-program/W__/reference.md` sections: _______________
- [ ] Re-read `12-week-program/W__/reference.md` sections: _______________
- [ ] Re-read `12-week-program/W__/reference.md` sections: _______________

For each section, after reading, **close the file and speak the key bullets aloud in 20 seconds each**. If you can't, re-read. This is the retention test.

---

## Step 5 — Re-do specific past exercises (30 minutes)

Identify 1–2 practice tests that heavily cover the weak domain:

- [ ] Re-do Practice Test __ (from `W__/practice_test/`) — focus on the 3 questions I previously missed.
- [ ] Re-do Practice Test __ (from `W__/practice_test/`) — focus on the scenario-framing questions.
- [ ] Rework exercise: _______________ from `W__/exercises/`.

For each re-done question, if you miss it twice, that's a deep weak spot — log it in `notes/weak_spots.md` with the full "why I missed it" explanation.

---

## Step 6 — Drill the distractor families (20 minutes)

Open `exercises/exam_day_playbook.md` section 2 (distractor families A–I). For your weakest domain, identify which distractor families are most common:

- Domain 1: usually Family A (add prompt rule), Family C (every agent every tool), Family G (resume after crash), Family E (bigger context window).
- Domain 2: usually Family A, Family C, Family F (retry forever).
- Domain 3: usually Family A, Family D (self-review), Family I (batches for blocking).
- Domain 4: usually Family A, Family B (parse text), Family H (self-report confidence).
- Domain 5: usually Family B, Family E, Family H.

Pick the 2–3 families most associated with your weak domain and:
- [ ] Re-read the "why tempting / why wrong" entries in `exercises/anti_patterns_master_list.md` for each.
- [ ] Write out one example distractor from your missed exam questions in each family.
- [ ] Practice the elimination response — "I see an Family A distractor here because it says 'add to the system prompt'; the deterministic alternative is ____."

---

## Step 7 — Consolidate into exam-day notes (15 minutes)

Write the 3 most important things you learned in this session into a single short file you'll reread on Saturday and Sunday morning:

```
# My weak-spot reminder (domain: _______)

1. ________________________________________________________
   (One bullet — the fact or pattern I missed.)

2. ________________________________________________________
   (A second bullet — usually the distractor family to watch for.)

3. ________________________________________________________
   (The deterministic alternative I will pick instead.)
```

Save it as `notes/weak_spot_reminder.md`. This is one of the last two files you read before the exam.

---

## Step 8 — Decide whether to also do the second-weakest domain

Only if:
- You finished Steps 1–7 with time to spare, AND
- The second-weakest domain is within 10 percentage points of the weakest, AND
- You have at least 45 minutes of focused energy left.

If yes, repeat Steps 3–6 for the second-weakest domain. Skip Steps 1, 2, 7 (already done).

If no, stop. Diminishing returns past this point; fatigue does more harm than marginal extra review does good.

---

## What to NOT do during the weakest-domain session

- **Do not re-read every reference.md file.** That's a 6-hour task, not a 2.5-hour one, and it dilutes focus.
- **Do not attempt Practice Exam 3 early.** Friday is for PE3. Thursday is for targeted drilling.
- **Do not learn a new concept not covered in W01–W10.** Anything you don't know by Thursday of W12 will not meaningfully land before Sunday.
- **Do not grind on one question for an hour.** If a concept is resisting, note it as a potential exam-day flag-and-revisit target and move on.

---

## Completion checklist

- [ ] Weakest domain identified with data (Step 1).
- [ ] All misses tagged with failure mode (Step 2).
- [ ] Task statements mapped (Step 3).
- [ ] 1–3 reference sections re-read and rehearsed aloud (Step 4).
- [ ] 1–2 past practice tests re-done on specific questions (Step 5).
- [ ] 2–3 distractor families drilled (Step 6).
- [ ] `notes/weak_spot_reminder.md` written (Step 7).
- [ ] Second-weakest domain considered and addressed if appropriate (Step 8).

When every box is checked, you're done. Go rest. Friday is PE3; you'll need fresh focus.
