# W06 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** plan mode vs direct execution, iterative refinement, headless CI (`-p`, `--output-format json`, `--json-schema`), generator/reviewer separation, Message Batches API for SLA windows.

---

## Talk 1 — Plan mode vs direct execution

- **Rule of thumb:**
  - **Direct execution** — single-file fix, small refactor, known-scope change. Plan mode is overhead.
  - **Plan mode** — 45-file migration, feature touching 3 subsystems, any "I'm not sure what this will affect." The plan itself is the artifact; you review it *before* any code changes, which is when rollback is free.
  - **Explore subagent** — open-ended discovery ("what do we have for observability?"). Plan mode is premature; you don't know enough to plan yet.
- **The trap:** skipping plan mode to "save time" on a 45-file migration and discovering after file 20 that you misread the pattern. Plan mode would have caught it in 2 minutes.
- **ExitPlanMode is a commit point.** Once you exit, the model starts executing. Review the plan thoroughly — after that, the model treats the plan as ground truth.

---

## Talk 2 — Iterative refinement patterns

- **Be concrete, not aspirational.**
  - Bad: "improve the error handling in this file."
  - Good: "in `api/client.py`, the `fetch_user()` function swallows network errors — change it to raise `UserFetchError` with the original exception as `__cause__`, and update the two callers in `service.py` lines 42 and 87."
  - **Why:** the first prompt makes the model invent what "improve" means; the second removes ambiguity.
- **TDD loop (red/green/refactor) is a natural fit.** Write a failing test first, ask the model to make it pass, then ask for refactor with the test as the invariant. Each step has a verifier (the test).
- **Interview / clarifying-questions pattern.** For ambiguous requests, ask the model to *list the ambiguities* before proposing a solution. Cheaper than discovering them after 300 lines of generated code.

---

## Talk 3 — Headless CI with Claude Code

- **`claude -p "prompt"`** — headless run, single prompt in, output to stdout.
- **`--output-format json`** — machine-readable response; pipe to `jq`.
- **`--json-schema schema.json`** — forces the model's final output to conform to a schema. Use this for checks that a downstream CI step consumes.
- **Canonical CI pattern:**
  1. Generator step: `claude -p "Review the diff in PR X and list regressions" --output-format json`.
  2. **Fresh session** reviewer step: a *different* `claude -p` invocation (new context) that consumes the generator's output and verifies it. Never let the same session review its own work — self-review retains reasoning bias.
  3. Exit-code contract: non-zero on problems found. CI blocks the merge.
- **Context isolation = the bug-you-won't-catch fix.** If the same session generates code and reviews it, the reviewer's premise is the generator's premise. An independent reviewer starts cold, reads the code with fresh eyes, and catches what self-review misses.

---

## Talk 4 — Message Batches API as a CI contrast

- **Batches are NOT for pre-merge checks.** Up to 24-hour completion window and no SLA. A PR reviewer that blocks a merge cannot use batch — use sync.
- **Right use cases:** overnight bulk extraction, weekly analytics refresh, nightly regression sweeps. 50% cost savings, and you get up to 24 h to process millions of records.
- **Exam distractor:** "Use Message Batches for the pre-merge lint check to save cost." Wrong — the PR author is waiting; no SLA is a blocker.
- **`custom_id` is the correlation key.** Batches return results out of order. Stamp each request with a `custom_id` so you can rejoin results to inputs.

---

## Exam-relevance one-liners

- "Use plan mode for a typo fix" → **overkill, use direct execution.**
- "Use direct execution for a 45-file migration" → **risky, use plan mode.**
- "Same session generates and reviews" → **self-review bias, use a fresh session.**
- "Use Message Batches for blocking pre-merge checks" → **no SLA, use sync.**
- "Exponential-backoff retry forever" → **useless when source info is absent.**

---

## Optional external viewing

- Search — Claude Code plan mode: https://www.youtube.com/results?search_query=claude+code+plan+mode
- Search — Claude Code CI GitHub Actions: https://www.youtube.com/results?search_query=claude+code+ci+github+actions
- Search — Message Batches API: https://www.youtube.com/results?search_query=anthropic+message+batches+api
