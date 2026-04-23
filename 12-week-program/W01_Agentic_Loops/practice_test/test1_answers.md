# Practice Test 1 — Answer Key & Explanations

## Quick key
| Q  | Answer |
|----|--------|
| 1  | B |
| 2  | C |
| 3  | C |
| 4  | B |
| 5  | C |
| 6  | B |
| 7  | C |
| 8  | B |
| 9  | C |
| 10 | B |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** Termination is decided by `stop_reason == "end_turn"`, not by substring-matching the model's text. Model phrasing is probabilistic and unreliable for control flow (§2, §7).

**Why the others are wrong:**
- A. Swapping the search string still uses text parsing — the underlying anti-pattern remains.
- C. `end_turn` with no tool call is a perfectly valid completion; absence-of-tool is not a reliable termination signal (§7, "Re-prompt if no tool was called").
- D. Indexing a different content block doesn't fix the fact that text parsing is the wrong mechanism.

**Reference:** §2 ("Exam rule: if a distractor says 'check the text'..."), §7 (anti-patterns table).

---

### Q2 — Answer: C

**Why C is correct:** If the assistant turn contained N `tool_use` blocks, the next `user` turn must bundle all N `tool_result` blocks together — one message, N blocks, each with a matching `tool_use_id` (§3 "Tool-use ↔ tool-result pairing", §3 "Parallel tool calls").

**Why the others are wrong:**
- A. There is no `"tool"` role in this API (§3, §7).
- B. Splitting tool_results across separate user turns violates the API contract (§3 "Common wrong answers").
- D. Tool results go in a `user` message, never in `assistant` (§3 role conventions).

**Reference:** §3 of reference.md.

---

### Q3 — Answer: C

**Why C is correct:** `tool_choice = {"type": "tool", "name": "extract_invoice_fields"}` forces the model to call that specific tool on this turn — a deterministic mechanism (§6).

**Why the others are wrong:**
- A. Prompt instructions are probabilistic; the model will sometimes skip. The reference explicitly calls out "deterministic mechanisms beat prompt instructions" (§7 last row, §10).
- B. `"any"` forces *some* tool call but not a specific one (§6).
- D. `"auto"` lets the model decide whether to call any tool at all (§6).

**Reference:** §6 and §7 of reference.md.

---

### Q4 — Answer: B

**Why B is correct:** `max_tokens` means the response was truncated. Treating it as `end_turn` silently returns incomplete output. Correct handling is to raise or retry with a larger cap (§2, §7 "Silently converting max_tokens to end_turn").

**Why the others are wrong:**
- A. `max_tokens` is explicitly listed as "not a normal terminator" (§2).
- C. Simply re-prompting "please continue" isn't the reference's prescribed fix; raise or enlarge the cap.
- D. `max_tokens` has nothing specifically to do with tool calls — it's a length cutoff on the response.

**Reference:** §2 and §7 of reference.md.

---

### Q5 — Answer: C

**Why C is correct:** The reference defines `safety_fuse` as a high crash-prevention cap (25/50/100), there only to catch bugs like infinite loops — not a task-level iteration limit (§4 "Invariants", §4 "Why safety_fuse and not a tight cap?").

**Why the others are wrong:**
- A. Normal termination is `stop_reason == "end_turn"` (§2, §4).
- B. A cap of 3–5 is explicitly flagged as wrong because real multi-tool tasks routinely need 10+ steps (§4, §7).
- D. The cap is decoupled from the specific tool count of any given task.

**Reference:** §4 of reference.md.

---

### Q6 — Answer: B

**Why B is correct:** The reference states plainly: tool results are sent as a `user` message, and there is no `"tool"` role in this API — inventing one is explicitly called out as wrong (§3 role conventions, §7 anti-pattern row).

**Why the others are wrong:**
- A. There is no such replacement; `"tool"` role does not exist in this API.
- C. The role is always `user` regardless of how many results are in the message (§3).
- D. The API does not normalize a fake role; using `"role": "tool"` is simply invalid.

**Reference:** §3 and §7 of reference.md.

---

### Q7 — Answer: C

**Why C is correct:** A tight iteration cap (here, 5) truncates valid multi-step tasks. The prescribed fix is a high safety fuse plus natural termination via `end_turn` (§4 "Why safety_fuse and not a tight cap?", §7 "Iteration cap of 3–5 as termination").

**Why the others are wrong:**
- A. Asking the model to batch work doesn't address the underlying wrong-termination-mechanism problem.
- B. W01 is explicitly about the raw loop; and the SDK doesn't fix a mis-designed termination strategy anyway (§8).
- D. Parsing text for "task complete" is the flagged anti-pattern from §7.

**Reference:** §4 and §7 of reference.md.

---

### Q8 — Answer: B

**Why B is correct:** Every iteration must append to `messages`; never overwrite. Feeding only the latest tool result breaks history and the model loses context (§3, §7 "Feeding only the latest tool result", §10).

**Why the others are wrong:**
- A. The reference directly contradicts this — full history is required.
- C. `stop_reason` handling doesn't compensate for a broken message history.
- D. History preservation is independent of `tool_choice`.

**Reference:** §3, §7, and §10 of reference.md.

---

### Q9 — Answer: C

**Why C is correct:** `{"type": "none"}` means the model cannot call any tool this turn, even if tools are listed (§6 table).

**Why the others are wrong:**
- A. Swapped — `"auto"` means the model decides (§6).
- B. Swapped — `"any"` means the model must call some tool (§6).
- D. Forced-specific `{"type": "tool", "name": "X"}` is a requirement, not a suggestion (§6).

**Reference:** §6 of reference.md.

---

### Q10 — Answer: B

**Why B is correct:** `end_turn` with no tool call is a valid completion. The reference explicitly lists "Re-prompt if no tool was called" as an anti-pattern and says to trust `end_turn` (§7).

**Why the others are wrong:**
- A. The reference directly flags this as an anti-pattern.
- C. Changing which role carries the re-prompt doesn't fix the fact that the re-prompt shouldn't exist in the first place.
- D. `max_tokens` is a separate concern (truncation, §2/§7); it does not justify re-prompting on `end_turn`.

**Reference:** §7 of reference.md.
