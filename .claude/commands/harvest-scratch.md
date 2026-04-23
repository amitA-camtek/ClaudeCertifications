---
description: Harvest weak spots from a reading-session scratch file into the week's notes/weak_spots.md as exam flashcards.
argument-hint: [relative path to scratch file, e.g. 12-week-program/W02_Multi_Agent_Orchestration/notes/session_2026-04-23.md]
---

You are harvesting weak spots from a reading-session scratch file into the same week's `weak_spots.md`.

## Input
Scratch file path: `$ARGUMENTS`

If `$ARGUMENTS` is empty, stop and ask the user which scratch file to harvest.

## Steps

1. **Locate the target files.**
   - Read the scratch file at `$ARGUMENTS`.
   - The week's `weak_spots.md` lives in the SAME `notes/` folder as the scratch file. Read it if it exists; otherwise plan to create it.
   - If the scratch file is empty or only whitespace, report that and exit without changes.

2. **Classify every bullet / line** from the scratch file into exactly one of:
   - `weak-spot` — confusion, a concept they stumbled on, a distinction they find unclear, a question they couldn't answer from memory
   - `insight` — an "aha" moment or summary of understanding (save for their info, do NOT add to weak_spots.md)
   - `todo` — a concrete follow-up action (build X, re-read Y, ask about Z)
   - `skip` — noise / chatter / partial line

3. **For each `weak-spot`, rewrite as an exam flashcard:**

   ```
   **Q:** <a specific question capturing what they were unsure about>
   **A:** <a tight 2-3 sentence answer grounded in the week's reference.md concepts>
   ```

   If the original bullet is too vague to flashcard cleanly (e.g., "hooks confuse me"), ask the user one clarifying question before finalizing that flashcard. Do NOT invent specifics the user didn't imply.

4. **Deduplicate against existing `weak_spots.md`.**
   - If a harvested flashcard covers the same concept as an existing entry, **merge** — extend the existing **A** with any new nuance. Do not create a duplicate card.
   - If different angle on same concept, append a "See also: ..." line to the existing card.

5. **Append new flashcards to `weak_spots.md`** under a dated section header:

   ```markdown
   ## Harvested from session_YYYY-MM-DD
   
   **Q:** ...
   **A:** ...
   
   **Q:** ...
   **A:** ...
   ```

   If `weak_spots.md` does not exist, create it with a top-level header derived from the week folder name, for example:
   ```markdown
   # Weak Spots — W02 Multi-Agent Orchestration
   ```

6. **Handle `todo` items** by appending them to a `## Todos` section at the end of `weak_spots.md` (create the section if missing). Format:
   ```markdown
   - [ ] <todo text> (from session_YYYY-MM-DD)
   ```

7. **Archive the scratch file.** Rename it from `session_YYYY-MM-DD.md` to `session_YYYY-MM-DD_harvested.md` in the same folder. Do NOT delete it — the user may want to re-read the raw bullets later.

8. **Report a summary** in one short message:
   - N weak-spot flashcards added (M brand-new, K merged into existing)
   - N todos appended
   - N items skipped as insight (list them verbatim — user may want to save insights elsewhere manually)
   - N skipped as noise (just the count, no detail)
   - Scratch file archived to `session_YYYY-MM-DD_harvested.md`

## Principles
- Flashcards must be exam-specific. No fluffy prose, no "it depends."
- Never invent concepts the scratch file doesn't hint at.
- Merging is preferred over duplication — the weak_spots.md file should stay dense, not accumulate near-duplicates.
- If the scratch file contains content that clearly belongs to a different week (e.g., user was reading W05 but the scratch has a W01 topic), flag it in the report but still add it to the target week's weak_spots.md — the user knows their own intent.
