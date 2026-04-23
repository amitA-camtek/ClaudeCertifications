# Practice Test 9 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | B |
| 2 | B |
| 3 | C |
| 4 | C |
| 5 | D |
| 6 | B |
| 7 | C |
| 8 | C |
| 9 | B |
| 10 | C |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** Progressive summarization keeps the gist and silently drops numbers (order IDs, dollar amounts, dates). The reference's prescribed fix is a persistent `case_facts` block of durable values maintained in agent code and re-injected every turn, so summarization affects dialogue but leaves the structured values intact (§2).

**Why the others are wrong:**
- A. A bigger window does not prevent summarization loss; it only delays bloat (§3, §11).
- C. System prompt length is unrelated to lost identifiers during summarization.
- D. Temperature does not cause summarization to drop identifiers; the summarizer is structurally dropping them because they aren't where semantic content is (§2).

**Reference:** §2 of reference.md

---

### Q2 — Answer: B

**Why B is correct:** §3 describes the "lost in the middle" effect empirically: content at the start and end of context is well-attended, the middle is under-weighted. The remedy is positional (put the fact at the start AND end) and structural (use `## SECTION HEADERS`). Turn 17 of 40 sits exactly in the degradation zone.

**Why the others are wrong:**
- A. The reference frames this as attention degradation, not a "no memory" problem; adding a vector DB is not the fix it endorses.
- C. Max output tokens control response length, not input attention.
- D. Aggressive summarization is the §2 anti-pattern that loses the fact in the first place.

**Reference:** §3 of reference.md

---

### Q3 — Answer: C

**Why C is correct:** §6 explicitly lists model self-reported confidence (1–10 scale) as a distractor: LLM self-confidence is miscalibrated, especially where the model is wrong, so the number has no predictive value.

**Why the others are wrong:**
- A. Explicit customer request is the first reliable trigger (§5).
- B. Policy gap is the second reliable trigger (§5).
- D. Inability to progress after concrete attempts is the third reliable trigger (§5).

**Reference:** §5 and §6 of reference.md

---

### Q4 — Answer: C

**Why C is correct:** §4 prescribes trimming the tool output at the boundary in the tool-execution wrapper, before appending it as `tool_result`. This keeps irrelevant fields out of history entirely, so they don't eat tokens every turn or dilute attention.

**Why the others are wrong:**
- A. Dumping the full raw output and telling the model to "ignore" fields is the explicit anti-pattern in §4 and §11 — the cost is paid every turn forever.
- B. Model-summarized blobs risk dropping identifiers (§2 summarization loss problem).
- D. The reference does not describe external file storage; it prescribes trimming at the tool boundary.

**Reference:** §4 of reference.md

---

### Q5 — Answer: D

**Why D is correct:** §7 directly covers multiple-match scenarios: when a lookup returns N > 1 candidates for an entity that must be uniquely identified before an action, surface the ambiguity and ask for a distinguishing identifier, then re-query.

**Why the others are wrong:**
- A. Picking "most recent" is explicitly listed as a wrong move — a guess (§7).
- B. Picking the largest amount is heuristic, not evidence (§7).
- C. Confirming after initiating an action is too late; the refund may already be on the wrong order (§7).

**Reference:** §7 of reference.md

---

### Q6 — Answer: B

**Why B is correct:** §9 defines the subagent→coordinator flow: subagents never swallow errors and never escalate directly; they report structured errors upward (`status`, `failure_type`, `attempted_query`, `partial_results`, `alternatives`) and the coordinator decides the next move.

**Why the others are wrong:**
- A. Subagents don't escalate directly to humans; only the coordinator has the scope to decide (§9 rule 2).
- C. Silent empty result is the §8 anti-pattern — it hides failure as success.
- D. §9 distractor call-out: unbounded retry is explicitly wrong; retries are bounded and only for transient failures.

**Reference:** §9 of reference.md

---

### Q7 — Answer: C

**Why C is correct:** §8 gives the exact structured shape: `failure_type` (categorical), `attempted_query`, `partial_results`, and `alternatives`. This gives the caller enough information to decide whether to retry, try an alternative identifier, ask the user, or escalate.

**Why the others are wrong:**
- A. Anti-pattern A in §8 — generic "operation failed" kills recovery.
- B. Anti-pattern B in §8 — silent suppression makes "I failed" indistinguishable from "no matches."
- D. Crashing the loop is not one of the endorsed patterns; the reference wants structured, actionable context returned to the caller.

**Reference:** §8 of reference.md

---

### Q8 — Answer: C

**Why C is correct:** §3 and the anti-pattern table in §11 state explicitly that attention quality does not scale with window size. A bigger window gives more room, not better attention distribution. The fix is positional (start/end) plus structural (section headers).

**Why the others are wrong:**
- A. Attention is not uniform across the window; this claim is the distractor §3 warns about.
- B. Room is not the problem; mid-context under-weighting is.
- D. Latency is a real concern, but it is not what §3 / §11 are addressing; the core reason the reasoning is wrong is the attention-quality-vs-capacity distinction.

**Reference:** §3 and §11 of reference.md

---

### Q9 — Answer: B

**Why B is correct:** §6 lists sentiment analysis as a wrong escalation trigger: sentiment ≠ case complexity; frustrated customers often have simple cases. A clearly policy-covered refund should be processed, not escalated.

**Why the others are wrong:**
- A. "Frustrated ⇒ escalate" is exactly the noise trigger §6 rejects.
- C. Lowering temperature does not change whether escalation is warranted; the case is policy-covered.
- D. Customer-reported frustration scores have the same problem sentiment does — they are not observable, deterministic, tied-to-failure signals (§6 principle).

**Reference:** §5, §6 of reference.md

---

### Q10 — Answer: C

**Why C is correct:** §10 prescribes local recovery first: bounded retry for transient failures, then alternative query, then ask the user; only after concrete local attempts fail does the path go to coordinator/escalation. §11 also names "escalate immediately on first tool failure" and "retry forever" as anti-patterns.

**Why the others are wrong:**
- A. Immediate escalation is the §10 / §11 anti-pattern — skips cheap local recovery.
- B. Unbounded retry is the opposite anti-pattern in §10 — a recoverable error becomes a hung session.
- D. Returning empty on failure is the §8 silent-suppression anti-pattern — hides failure as success and corrupts downstream decisions.

**Reference:** §10 and §11 of reference.md
