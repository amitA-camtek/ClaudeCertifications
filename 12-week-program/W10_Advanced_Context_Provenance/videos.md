# W10 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** scratchpad files for durable state, `/compact` as lossy compression, subagent delegation for context management, stratified sampling, provenance (claim→source→date), conflict annotation.

---

## Talk 1 — Long-session degradation and durable state

- **Three degradation modes of long sessions:**
  1. **Attention fade** — the model's focus on earlier content drifts. Even if it's in context, it's weighted less.
  2. **Retrieval drift** — asked about a fact from 50 turns ago, the model retrieves a plausible-sounding wrong answer.
  3. **Reasoning drift** — intermediate conclusions that were tentative become "facts" the model builds on. Errors compound.
- **Scratchpad files = durable state.** Write key facts, intermediate conclusions, and decisions to a plain file. Survives `/compact`, crashes, session restarts. Re-read at session start; update after each meaningful step.
- **Why files not in-context:** files are cheaper (not paying per-turn for the same content), survivable, and inspectable by humans. In-context state is lossy by design.

---

## Talk 2 — `/compact` and subagent delegation

- **`/compact` is lossy compression.** It produces a summary, not a deduplication. Numbers, exact quotes, dates — the things you most need to preserve — are the things most likely to blur.
- **Pair `/compact` with a scratchpad.** Before `/compact`, flush key facts to disk. After `/compact`, read them back. The summary handles the "what we've been doing" prose; the scratchpad handles the precision.
- **Subagent delegation as a context-management tool.** If a subtask would bloat the main context with 20k tokens of transient logs, delegate to a subagent. Subagent does the heavy lifting in its own context; returns a 500-token distilled result. Coordinator context stays clean.

---

## Talk 3 — Crash recovery via manifests

- **Manifest pattern:** a file that records, in order, each intended step, the input, the output (or "pending"). Written *before* each step, updated after.
- **Recovery algorithm:** on restart, read the manifest. Find the last completed `step_index`. Resume at `step_index + 1`. Skip idempotent steps; re-run non-idempotent ones only if the manifest proves they didn't complete.
- **Why this beats `--resume`:** `--resume` gets you back into the conversation, but doesn't tell you whether the tool call that crashed the session actually ran. The manifest does.
- **Distractor:** "use a bigger context window so the session doesn't need recovery." Doesn't address the failure mode (crashes, non-idempotent operations, cost, token loss). Scratchpad + manifest does.

---

## Talk 4 — Stratified sampling and source characterization

- **Aggregate accuracy hides the failure mode.** 95% overall could be 99% on 80% of cases and 60% on the remaining 20%. Customers live in that 20%.
- **Stratified sampling:** bucket your eval set by (document_type × field × confidence bucket) and measure per bucket. Now you know *where* you fail, and can fix targetedly.
- **Source characterization, for research agents:**
  - **Primary vs derivative.** A financial report is primary; a news article about it is derivative.
  - **Publication date.** A 2021 report citing "current year" numbers ≠ the same story as a 2024 report.
  - **Credibility.** Peer-reviewed, authoritative, anonymous — these are separate attributes worth tagging.
- **Why tag: downstream synthesis depends on it.** A coordinator cannot weight sources sensibly if they come in as a flat list of quotes.

---

## Talk 5 — Provenance and conflict annotation

- **Per-claim provenance.** Subagents return `{ claim, source_url, publication_date }` objects, not prose paragraphs. The coordinator synthesizes while *preserving* the claim→source mapping.
- **Dates disambiguate "old vs new" from "conflict."** Two sources giving different numbers may be (a) out-of-date and (b) current — not a conflict, just a timeline. Without dates, the coordinator mis-reads this as contradiction.
- **Annotate conflicts, don't resolve them arbitrarily.** If Source A says 12% and Source B says 15%, the synthesis output should preserve both with attribution:
  > "Source A reports 12% (2022 report); Source B reports 15% (2024 update). The discrepancy likely reflects revised methodology in 2024."
  Picking one and discarding the other is the *worst* option — you lose both accuracy and verifiability.
- **Confidence tiers:** `well-established` (multiple primary sources agree), `contested` (primary sources disagree), `single-source` (only one source supports). Render these tags in the final output so readers can weight claims themselves.
- **Content-type-aware rendering.** Quantitative data → tables with source columns. Narrative claims → prose with inline citations. Don't force everything into one format.

---

## Exam-relevance one-liners

- "`/compact` to free tokens" → **fine, but pair with scratchpad; lossy for precision.**
- "Bigger window instead of scratchpad" → **doesn't solve attention fade or crashes.**
- "Synthesize by picking the most recent source" → **loses the contested evidence; annotate instead.**
- "Measure aggregate accuracy" → **stratify by type and field.**
- "Treat old-source vs new-source as a conflict" → **look at dates; may be a timeline.**

---

## Optional external viewing

- Search — Anthropic multi-agent provenance / citations: https://www.youtube.com/results?search_query=claude+multi+agent+provenance+citations
- Search — Anthropic long-running agents / scratchpads: https://www.youtube.com/results?search_query=anthropic+long+running+agents+scratchpad
- "How we built our multi-agent research system": https://www.anthropic.com/engineering/built-multi-agent-research-system
