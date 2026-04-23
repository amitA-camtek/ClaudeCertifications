# Practice Test 4 — Answer Key & Explanations

## Quick key
| Q  | Answer |
|----|--------|
| 1  | C |
| 2  | C |
| 3  | B |
| 4  | B |
| 5  | C |
| 6  | B |
| 7  | C |
| 8  | C |
| 9  | D |
| 10 | C |

## Detailed explanations

### Q1 — Answer: C

**Why C is correct:** §1 states the `description` field is the primary selection signal — not the name, not the system prompt. A good description is a specification: what the tool does, input format with examples, return shape, positive boundary, negative boundary, and error behavior. Tokens spent on descriptions are "the best-spent tokens in your whole prompt"; the good example is ~8× longer than the bad one and that trade is correct.

**Why the others are wrong:**
- A. §1 and §9's last row: system-prompt instructions are probabilistic hints; the model will sometimes skip them. Deterministic mechanisms (the description in the catalog) beat prompt instructions.
- B. §5: forcing `tool_choice: any` is a band-aid for a bad description — it forces *a* tool, not the *right* one.
- D. §1: the model picks by reading the description, not the name. Renaming alone doesn't fix selection.

**Reference:** §1 of reference.md

---

### Q2 — Answer: C

**Why C is correct:** §2's table says that when two tools are truly different (like `check_stock` vs `check_availability`), the fix is to keep both and sharpen descriptions with explicit negative-boundary clauses — "Do NOT use this for X; use `Y` instead." This is the single highest-leverage addition for disambiguating near-similar tools (§1 item 5).

**Why the others are wrong:**
- A. §2: a mega-tool with a `mode` enum hides intent from the selector; splitting/explicit-descriptions is the fix, not consolidating behind an enum.
- B. §2: deletion is the fix only when two tools do the *same* thing. Here they are genuinely different.
- D. §5: forcing a specific tool at every turn is a band-aid; good descriptions let `auto` work.

**Reference:** §2 of reference.md

---

### Q3 — Answer: B

**Why B is correct:** §3 defines the minimal structured-error shape as `isError`, `errorCategory`, `isRetryable`, and `message`. Without `errorCategory` the model can't distinguish `validation`/`not_found`/`timeout`/`policy`/`internal`, and without `isRetryable` retry becomes probabilistic string-parsing rather than a deterministic branch. Adding both fixes the infinite-retry and no-escalate behavior.

**Why the others are wrong:**
- A. §3: stack traces and HTTP status codes are explicitly discouraged in the `message` field; neither is part of the minimal shape.
- C. §3 uses `isError` (not `success`), and there's no `fallback_tool` field in the prescribed shape.
- D. §3: neither `severity` nor `retry_count` is in the minimal error schema. `isRetryable` is the field that "is load-bearing" for retry logic.

**Reference:** §3 of reference.md

---

### Q4 — Answer: B

**Why B is correct:** §2's third row and §9's anti-pattern row explicitly call out the `mode` enum pattern: "The model selects against tool names and descriptions, not enum values inside inputs. Modes inside one tool hide the intent from the selector." The fix is to split into `lookup_sku`, `create_sku`, `delete_sku` with distinct descriptions.

**Why the others are wrong:**
- A. §2 does not claim enums are unsupported; the problem is about selector visibility, not schema support.
- C. §1: the fix is richer descriptions and/or splitting, not more parameters.
- D. §2: a default value doesn't surface the three distinct intents to the catalog the selector sees.

**Reference:** §2 of reference.md

---

### Q5 — Answer: C

**Why C is correct:** §4 states the hard rule: 4–5 tools per agent, maximum. Selection accuracy drops measurably past ~6–7 tools. "Never hand one agent the union of every MCP server's tools." The coordinator should delegate to specialist subagents, each with its own scoped list (the W02 tie-in in §4).

**Why the others are wrong:**
- A. §1 and §9: system-prompt instructions are probabilistic; scoping is the deterministic fix.
- B. §5: `tool_choice: any` forces *a* tool, not the *right* one — it doesn't repair bloated catalogs.
- D. §4's anti-pattern: "Give every agent every tool for maximum flexibility" is explicitly wrong — flexibility isn't the bottleneck; selection is.

**Reference:** §4 of reference.md

---

### Q6 — Answer: B

**Why B is correct:** §6 "Community MCP servers vs custom implementations" states: for any standard integration (Jira, GitHub, Postgres, Sentry, S3, Slack, Linear, ...) use the community server. Community servers have tools iterated against the real API and descriptions refined across many PRs (which matters per §1). Write custom only for team-specific systems or when a real gap can't be upstreamed.

**Why the others are wrong:**
- A. §6's anti-pattern box directly says "Build a custom MCP server for Jira integration to ensure team-specific behavior" is wrong in the default case.
- C. §6 doesn't recommend bypassing MCP for standard integrations; the whole point of MCP is to avoid writing per-integration glue.
- D. §7: Jira actions are actions (tools), not read-only resources.

**Reference:** §6 of reference.md

---

### Q7 — Answer: C

**Why C is correct:** §7's rule: "If the thing modifies state or executes a query with parameters, it's a **tool**. If it's 'here's a fixed document the agent should be able to pull into context', it's a **resource**." `run_query` executes with parameters → tool. A static style-guide PDF → resource.

**Why the others are wrong:**
- A. §7: `place_order` has side effects, so it's a tool, not a resource (this is the exact distractor §7 calls out). A style guide is read-only content → resource, not a tool.
- B. §7: `send_email` is an action with side effects → tool. The API reference doc is read-only → resource.
- D. §7: both concepts exist distinctly; tools are not a legacy term.

**Reference:** §7 of reference.md

---

### Q8 — Answer: C

**Why C is correct:** §6 "`.mcp.json` (project) vs `~/.claude.json` (user)" — `.mcp.json` at repo root is for shared team tools checked into git. §6 "`${ENV_VAR}` expansion — secrets" shows `"INVENTORY_API_KEY": "${INVENTORY_API_KEY}"` as the correct pattern: commit the config, keep the env value uncommitted.

**Why the others are wrong:**
- A. §6: `~/.claude.json` is per-user; each dev would have to reconfigure and drift across the team (also listed as an anti-pattern in §9).
- B. §6 anti-pattern: "Embed the API key directly in `.mcp.json` and check it into the repo" is the explicit wrong pattern; it leaks the secret into git history.
- D. §6: omitting env blocks the server from authenticating; MCP does not magically handle third-party auth.

**Reference:** §6 of reference.md

---

### Q9 — Answer: D

**Why D is correct:** §8's selection cheatsheet: "Searching content → **Grep**." Grep is the tool for searching file contents (`import pandas` is a string inside files). §8's distractor pattern is exactly this question's A option.

**Why the others are wrong:**
- A. §8's distractor pattern: "To find all files that import `pandas`, use Glob with pattern `import pandas` — wrong. Glob matches *paths*, not contents. Use Grep." Option A is the textbook wrong answer.
- B. §8: Bash for file ops that have a dedicated tool is explicitly the wrong pattern; Grep is cheaper and safer.
- C. §8: Read is for when you already know the file path and want its contents — not for searching across unknown files.

**Reference:** §8 of reference.md

---

### Q10 — Answer: C

**Why C is correct:** Two anti-patterns are combined here. §3 and §9 row 2: generic error strings destroy the signals needed for retry/escalation decisions; use structured `isError`/`errorCategory`/`isRetryable`/`message`. §9 row 3: "Retry on every error with exponential backoff" wastes budget on `validation`/`not_found`/`policy` errors that will never succeed — retry should branch on `isRetryable`. §1 also rejects terse descriptions outright: "Tokens spent on descriptions are the best-spent tokens in your whole prompt."

**Why the others are wrong:**
- A. §3 and §9: generic strings plus blanket retries is explicitly the anti-pattern, not the standard pattern.
- B. §1: terser descriptions collapse selection quality — "that is the wrong trade."
- D. §3: generic strings break the model's ability to paraphrase meaningfully and destroy retry branching; user-friendly `message` inside a structured object is the right pattern, not a bare string.

**Reference:** §§1, 3, 9 of reference.md
