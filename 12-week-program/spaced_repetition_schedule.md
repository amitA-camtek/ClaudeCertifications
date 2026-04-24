# Spaced-Repetition Schedule for `weak_spots.md`

Weak-spot flashcards lose effectiveness fast if you only see them the week you harvest them. This schedule prescribes when each week's `weak_spots.md` gets revisited during later weeks' **Warmup** block (first 10 minutes of Study Day).

## The cadence — expanding intervals (1 / 3 / 6 / 9 weeks)

Each week's Warmup revisits prior weeks' cards at roughly these gaps:
- **1 week back** — last-week retention check (was the recent material learned or skimmed?)
- **3 weeks back** — fights forgetting-curve decay before cards calcify as wrong
- **6 weeks back** — consolidation check; cards still retrieved easily mean you own them
- **9 weeks back** — deep-retention probe near exam time

Missing any card on revisit → star it in that week's `weak_spots.md` (add `⭐` prefix) and move it to the top. Starred cards re-enter the next Warmup regardless of schedule.

## The table

| Week | Warmup revisits | Rationale |
|---|---|---|
| W01 | — | First week, nothing to revisit yet |
| W02 | W01 | Build the habit |
| W03 | W02 + W01 | Double-back while sets are small |
| W04 | W03 + W01 | 1-back + 3-back spacing begins |
| W05 | W04 + W02 | 1-back + 3-back |
| W06 | W05 + W03 | 1-back + 3-back |
| W07 | W06 + W04 + W01 | 1-back + 3-back + **6-back** enters |
| W08 | W07 + W05 + W02 | 1 / 3 / 6 |
| W09 | W08 + W06 + W03 | 1 / 3 / 6 |
| W10 | W09 + W07 + W04 + W01 | 1 / 3 / 6 + **9-back** enters |
| W11 | W10 + W08 + W05 + W02 | 1 / 3 / 6 / 9 |
| W12 | Full sweep of all starred cards across W01–W11 | Exam-week consolidation — prioritize `⭐` cards |

## How to run the Warmup

The 10-minute Warmup slot already exists in every `week_plan.md`. Instead of reading straight through a weak_spots.md file, do **cold recall**:

1. Open each prescribed `weak_spots.md` in turn (typically 2–4 files for the week).
2. For each flashcard, read only the **Q:** line. Say the answer out loud (or write it in 10 seconds).
3. Reveal **A:**. Compare.
4. If correct and fast → move on.
5. If wrong, slow, or hesitant → prefix the card with `⭐` and re-read the relevant `reference.md` section in-line (don't postpone — do it now, it's worth the minute).
6. When the 10-minute timer hits, stop. The goal is **frequency**, not exhaustive coverage. Next week's Warmup hits the same file again.

## Why not "just re-read all old weak_spots every week"

Because reading ≠ retrieval. Passive re-reading feels productive and produces near-zero retention transfer. The active recall of the cold-recall drill is what consolidates the card. Three cards tested cold beat thirty cards re-read.

## Why `⭐` and not a separate file

Keeping starred cards in-place (at the top of the same `weak_spots.md`) means you see them in context with their neighbors. Moving them to a separate file loses the domain grouping, and you'd have to merge during review anyway. One file, sorted by difficulty.

## W12 handling

W12's Warmup replaces "revisit 1/3/6/9 weeks back" with "full sweep of starred cards across W01–W11". By that point the cards you still miss are your actual exam risk. See [W12_Final_Exam_Prep/week_plan.md](W12_Final_Exam_Prep/week_plan.md) for the full-week prioritization.
