# Key Notes — Moving Pass Probability from 85% to 95%

The 12-week plan as it stands puts a diligent candidate at roughly **80–90%** probability of passing (≥ 720 / 1000). This file lists the specific levers that separate "strong candidate" from "walk in confident". Not generic advice — each item is a concrete practice that empirically moves exam scores when the baseline is already solid.

Ranked by expected impact on the 85 → 95 delta.

---

## 1. Ship something real alongside the plan (biggest lever)

**What:** during W01–W10, build one **small production-like agent** outside the exam exercises. Options: a personal MCP server you actually use daily, a Claude Code skill you invoke weekly on a real codebase, a mini customer-support agent with real hooks and escalation. Anything with **real inputs, real stakes, and real feedback**.

**Why it matters:** Anthropic targets this exam at candidates with **6+ months hands-on** — the scenario questions assume you've *lived* the failure modes. Reading about "the model silently re-issued a refund" is not the same as having fixed it at 2am. Real builds produce the intuition exam distractors are designed to probe.

**How:** pick one idea in W01, work on it 1 h/week on top of the 5 h plan. By W10 you'll have ~10 h of production-grade Claude experience that the 4 W11 exercises can't replicate.

**If you skip this:** you top out around 85%. The plan teaches recognition; real work teaches reflexes.

---

## 2. Reject the 3 distractors out loud on every practice question

**What:** after each practice question, before moving on, say out loud (or write):
- Why the correct answer is correct.
- **For each of the 3 distractors:** what concept it's trying to exploit, and what single fact makes it wrong.

**Why it matters:** 85% candidates pick the right answer. 95% candidates pick it **while rejecting the other three with named reasons**. On the real exam, that process survives time pressure and ambiguity; pattern-matching alone doesn't.

**How:** add ~90 seconds per question to your practice-test review. On 100 practice questions that's ~2.5 hours of added review time over the program — very high ROI.

**Diagnostic:** if you can't name why a distractor was tempting, you'd have picked it under time pressure on a parallel question.

---

## 3. Teach every fuzzy concept out loud (Feynman drill)

**What:** for every flashcard in `weak_spots.md` marked ⭐, deliver a **90-second spoken explanation** to an imaginary colleague who's never used Claude. No notes. No re-reading.

**Why it matters:** the gap between *recognition* (I saw this in a table) and *retrieval* (I can reconstruct it cold) is the gap between 80% and 95%. Teaching forces retrieval + composition + explanation — the actual cognitive demand of scenario questions.

**How:** at the end of each Practice Day, pick the 3 newest ⭐ cards and talk them out. The moment you stumble, note which transition broke — that's the sub-concept to re-read.

**Signal of readiness:** if you can deliver a fluent 2-minute talk on "how do you decide between PreToolUse hook and PostToolUse hook" without hesitation, you own that concept.

---

## 4. Add a timed full-length exam at end of W06

**What:** slot a **third full practice exam** into end of W06 (mid-program). Treat it exactly like the real thing: 60 questions (or whichever length Anthropic ships), timed, closed-book, no pausing.

**Why it matters:** the current plan has Practice Exam 1 at W11 — too late to fix pacing or stamina issues. A W06 full run gives you 6 weeks to close the pacing gap before exam day. The cost is 90 min + ~45 min review.

**How:** reuse sample questions from the exam guide + any official Anthropic practice bank. Don't re-use questions from the weekly tests (you'll pattern-match to your prior answers instead of retrieving the concept).

**Threshold read:** < 60% at W06 = plan is underperforming, course-correct (usually toward more hands-on); 60-75% = on track; > 75% = ahead of schedule.

---

## 5. Run an error-pattern journal

**What:** a single text file. Every wrong practice answer gets **one line**: `W{XX} Q{N}: I picked {wrong} because {temptation}; correct is {right} because {discriminator}. Pattern: {one tag}.`

After 50+ wrong answers, tags cluster. You will see your **personal blind spots**: maybe you always conflate `tool_choice: any` with forced-specific, or always miss PostToolUse timing. These are the cards that belong at the top of every Warmup.

**Why it matters:** the master anti-pattern list tells you the traps the exam uses. The error-pattern journal tells you the traps **you personally fall for**. That's a narrower, higher-yield target.

**How:** append to `notes/error_patterns.md` (or similar) after every practice test review. 5 minutes of real reflection beats 30 minutes of generic re-reading.

---

## 6. Do 4 full practice exams, not 2

**What:** the plan currently has 2 full timed exams (W11, W12). Add two more: one at W06 (see lever #4), one retake at end of W12. Total: 4.

**Why it matters:**
- **Stamina is real.** Attention drifts around minute 45 of 60; the only cure is practice under the full duration.
- **Pacing is only calibrated by repetition.** Knowing "at Q30 I should be at minute 25" has to be automatic, not calculated.
- **Retake after 10 days shows retention**, not recognition. If you pass a retake 10 days later without re-studying, the material is stored. If you drop 15 points, it's still recognition-only.

**How:** extend practice question inventory. Anthropic's sample questions + course bank + your own test1-10 questions (resampled) supply enough.

---

## 7. Re-read the foundational research 2–3 times

**What:**
- ["Building effective agents" — Anthropic research](https://www.anthropic.com/research/building-effective-agents)
- ["How we built our multi-agent research system" — Anthropic engineering](https://www.anthropic.com/engineering/built-multi-agent-research-system)

Read each **at least twice**: once at W01 (orientation) and once at W10 (before Practice Exam 1). A third pass on the Saturday before exam day.

**Why it matters:** the 30 task statements are *derived from* these two articles. Distractors are built on misreadings of concepts introduced in them. Knowing the source makes the distractors visibly fake — you spot them before parsing the answer choices.

**How:** 45 minutes total for both. Note every phrase that becomes a term of art in the exam (hub-and-spoke, reasoning trails, poisoned context, etc.).

---

## 8. Rehearse exam-day conditions literally

**What:** for Practice Exams 2–4, match the real exam environment:
- **Same time of day** as your scheduled exam slot (circadian alertness matters).
- **Same browser, same chair, same lighting.**
- **No lookup, no pausing, no snacks unless you'll have them on exam day.**
- **Caffeine/food timed the way you'll time them on exam day.**

**Why it matters:** novelty in the physical environment costs 2–5 points under pressure. Exam-day anxiety is real; desensitization through repetition is free insurance.

**How:** schedule the 4 practice exams on 4 different calendar dates at the same time slot as the real exam. Treat each as a dress rehearsal.

---

## 9. Track per-task-statement rolling accuracy

**What:** a spreadsheet (or markdown table) with all 30 task statements as rows and your last 20 practice questions per task as a rolling accuracy %.

**Why it matters:** the coverage matrix ([coverage_matrix.md](coverage_matrix.md)) tells you *where* each topic lives. This tells you *where you're weak*. When a task statement drops below 80% over 20 Q, that's a targeted re-read trigger — you know exactly which `reference.md` section to reopen.

**How:** tag every practice question with its task statement (1.1, 1.2, ...). 20 minutes/week of bookkeeping; massive targeting precision at W11.

---

## 10. Physical discipline for the last 72 hours

**What:**
- **3 nights of ≥ 7 hours sleep** before the exam. Sleep-deprivation costs 5–15 points.
- **Caffeine match-day same as practice days.** Don't introduce novel stimulants.
- **No new studying in the last 24h.** New content displaces retrieval.
- **Light review only:** ⭐ cards, anti-pattern list, adjacent-concept drill.
- **Eat and hydrate on schedule.** Low blood sugar is indistinguishable from not knowing the answer.

**Why it matters:** 5–15 points at 72% threshold is the entire margin. A candidate who'd pass at 78% on a rested day can fail at 68% on a sleep-deprived one. Protecting the body is protecting 10 points.

---

## How these compose

Baseline plan: 80–90% (with honest execution).

Stack these levers cumulatively:

| Added levers | Rough probability ceiling |
|---|---|
| Baseline (current plan, honestly executed) | 85% |
| + lever 2 (distractor rejection) + lever 3 (Feynman) | 88–90% |
| + lever 4 (W06 full exam) + lever 6 (4 full exams total) | 90–92% |
| + lever 1 (real production work) | 92–94% |
| + lever 5 (error-pattern journal) + lever 9 (rolling accuracy) | 93–95% |
| + lever 7 (re-read foundational research 2x) + lever 8 (rehearse conditions) + lever 10 (72h discipline) | 94–96% |

These are rough — the real distribution depends heavily on your starting experience. A candidate with 2 years of hands-on + full lever stack is probably > 96%; a candidate with zero hands-on + full lever stack might be 85%.

## The single highest-leverage item if you only pick one

**Lever 1 — ship something real.** Nothing else substitutes for hands-on experience in scenario-question performance. If you genuinely can't do it, lever 2 (distractor rejection) is the next-best single lever.

## The single lowest-cost item

**Lever 10 — sleep and caffeine discipline in the final 72 hours.** Zero study time, pure execution. Gives back 5–15 points that are otherwise lost to biology.

---

## Honest warnings

- **None of these work if you skim.** All 10 levers assume you're already doing the plan's cold-recall Warmups, reviewing every wrong answer, and running the exercises for real.
- **Stacking levers has diminishing returns.** Lever 5 + 9 together are *not* 2x the value of either alone; they overlap in what they catch. Pick what's realistic, not the maximalist stack.
- **The exam has a ceiling.** A few questions may be genuinely ambiguous or test material not in any published source. Plan for ~95% max, not 100%. Don't mistake "perfect on practice" for "perfect on exam".
- **Pass-probability estimates are rough.** Your actual outcome is binary — you pass or you don't. Probabilities describe the population of candidates who follow the plan; yours is a sample of size 1. The levers move the expected value; they don't guarantee the draw.

---

## Exam-week-of checklist

- [ ] All ⭐-starred cards retrievable in < 10s
- [ ] Adjacent-concept drill: all 24 pairs, can name the discriminator cold
- [ ] Final practice exam ≥ 80% (4 of 4 practice exams completed)
- [ ] Error-pattern journal reviewed; top-3 personal traps memorized
- [ ] Coverage matrix self-audit: every box ticked
- [ ] Sleep plan locked for last 3 nights
- [ ] Exam environment rehearsed (same time/browser/setup as exam day)
- [ ] Foundational research re-read on Saturday
- [ ] No new content in last 24h

If every box is ticked, you're at the top of the probability distribution. Go take it.
