# Anti-Patterns Master List — Deeper Framing

The table in `reference.md` is your fast reject-on-sight reference. This file is the companion: for each anti-pattern, **why a learner might be tempted to pick it** and **why it's wrong in two or three sentences.** Use this for the final-week deep-review session — when you feel the pull of a distractor and want to understand what the trap is designed to exploit.

Grouped by domain. Same anti-patterns as the master table in `reference.md`, but with explanatory depth.

---

## Domain 1 — Agentic Architecture & Orchestration

### Parse model text for "done" / "finished" to terminate the loop
*Why tempting:* it feels natural — the model has written something that looks like a conclusion, and human readers can tell the task is done, so string-matching should be enough.
*Why wrong:* the model's phrasing varies across runs, system-prompt changes, and model versions. String-matching is probabilistic termination; the API already provides a deterministic signal (`stop_reason == "end_turn"`). Use the signal.

### Tight iteration cap (3–5) as the termination mechanism
*Why tempting:* "runaway loops are scary; cap it low to be safe." You've heard "agents can get stuck" and overcorrect.
*Why wrong:* real multi-tool tasks routinely need 10–30+ turns. A tight cap truncates correct work and produces half-finished output silently. Use a high `safety_fuse` (25/50/100) as a crash guard only; the normal terminator is `end_turn`.

### Running tools "inside" the model call
*Why tempting:* you've seen SDK examples that make it look like the model can run arbitrary code; you assume tool execution is an API feature.
*Why wrong:* the API only emits `tool_use` **requests**. Execution happens in your code; results go back as `tool_result` blocks in the next `user` message. This is the whole point of the loop architecture and the source of most "agent didn't call my tool" confusion.

### Using `"role": "tool"` for tool results
*Why tempting:* other ecosystems (e.g., some OpenAI-style chat APIs) use a `"tool"` role. Muscle memory carries over.
*Why wrong:* the Messages API has no `"tool"` role. Tool results live inside a `"user"` message as `tool_result` content blocks keyed by `tool_use_id`. Inventing a `"tool"` role fails API validation.

### Separate `user` turn per tool result
*Why tempting:* it looks tidy — one message per result, chronologically ordered.
*Why wrong:* when a single assistant turn emits N parallel `tool_use` blocks, the next `user` turn must contain all N paired `tool_result` blocks in one message. Splitting them across turns breaks the pairing contract and the model loses coherence.

### Give every subagent every tool ("for maximum flexibility")
*Why tempting:* "more options = more power." Scoping feels restrictive.
*Why wrong:* selection quality degrades past ~5–7 tools because descriptions compete for attention and near-similar tools blur. Flexibility isn't the bottleneck; selection accuracy is. Scope 4–5 per role and delegate cross-domain work.

### Subagents share memory or directly see each other's context
*Why tempting:* shared memory sounds efficient — why redo work? It feels like teamwork.
*Why wrong:* shared memory re-creates all the single-agent problems (context bloat, role conflict, poisoned trails from failed branches) at higher cost. The whole point of the hub-and-spoke pattern is isolation; inter-agent communication goes through structured prompts and compact return values.

### "Add instructions to the coordinator prompt telling it to delegate"
*Why tempting:* the fix for a coordinator doing everything itself feels like "tell it harder in the prompt".
*Why wrong:* without `"Task"` in `allowedTools`, the coordinator physically cannot delegate no matter what the prompt says. Configuration (tool allow-list) is the mechanism; the prompt is downstream of it.

### Run all subagents sequentially for safety
*Why tempting:* "order preserves correctness." Parallel sounds riskier.
*Why wrong:* order is preserved by task decomposition, not execution mode. Independent subtasks should be parallelized for wall-clock speedup; only dependencies (B needs A's output) require serial dispatch. The coordinator imposes order where needed.

### Adaptive decomposition for a fixed-shape task
*Why tempting:* adaptive sounds smart, general-purpose, future-proof.
*Why wrong:* adaptive decomposition adds a reasoning turn (the coordinator has to inspect and decide) and a failure mode (it can decompose badly). For known steps, a fixed prompt chain is simpler, faster, easier to debug, and hook-friendly between stages.

### Add "NEVER refund over $500" to the system prompt
*Why tempting:* it's the most natural-feeling control knob: you tell the model what not to do.
*Why wrong:* prompts are probabilistic. The model obeys most of the time and fails silently with confidence on the remaining cases — especially under prompt-injection, persistent customers, or confused reasoning chains. A PreToolUse hook that blocks `amount_usd > 500` is enforced by code, not hoped for by prose.

### PostToolUse hook to prevent a destructive action
*Why tempting:* "the hook sees the call, the hook should be able to stop it" — the distinction between *pre* and *post* feels like implementation detail.
*Why wrong:* PostToolUse fires AFTER the tool has run. The refund has been issued; the file has been deleted; the email has been sent. To prevent side effects, PreToolUse is the only option. PostToolUse is for shaping what the model sees next (redaction, normalization, logging).

### Resume a session after a failed destructive operation
*Why tempting:* "I lost progress; resuming preserves context." The alternative (fork or fresh) feels like it throws work away.
*Why wrong:* the failed turn's reasoning and the broken state are in the session history. The model will re-engage with them, likely mis-steer again, and compound the damage. **Fork from a clean point** (or start fresh) and seed the new session with a clean summary. Resume only into **clean** history.

### Sentiment analysis as an escalation trigger
*Why tempting:* upset customers are the ones who need escalation most, right?
*Why wrong:* sentiment ≠ case complexity. A polite customer can hit a policy gap that needs escalation; an angry customer can have a simple issue resolved quickly. Use categorical triggers: explicit customer demand, detected policy gap, inability to progress. Sentiment is noise on the wrong axis.

### "Increase the context window" to fix a stale session
*Why tempting:* "the model is losing track because it's running out of room" is an intuitive story.
*Why wrong:* attention quality does not scale with window size. The "lost-in-the-middle" effect means putting more content in a bigger window still leaves middle-of-context information poorly attended. Structural fixes (`/compact`, fork + seed, scratchpad file, start fresh) are the real lever.

---

## Domain 2 — Tool Design & MCP Integration

### Terse tool descriptions "to save tokens"
*Why tempting:* every token costs money; short is efficient; descriptions feel like overhead.
*Why wrong:* descriptions are the model's selector. A terse description produces wrong tool picks on every ambiguous call for the life of the agent. Tokens spent on rich descriptions (input format, examples, positive + negative boundaries, return shape) are the best-spent tokens in the whole prompt. This is the wrong place to economize.

### Return a generic `"operation failed"` string on error
*Why tempting:* one error string is simple; the model can figure out what to do.
*Why wrong:* the model cannot distinguish retryable from fatal, cannot pick an alternative tool, cannot explain the real failure to the user. A structured error — `isError`, `errorCategory`, `isRetryable`, user-friendly `message` — turns every failure into actionable branch logic.

### Retry every error with exponential backoff
*Why tempting:* "resilience = retry; retry everything" is a tempting one-size-fits-all.
*Why wrong:* validation errors, not-found errors, and policy errors will never succeed on retry. Exponential backoff wastes latency and budget; retryable-only logic (`isRetryable` flag) saves both. Distinguish transient from permanent.

### One mega-tool with a `mode` enum input (`action="lookup" | "create" | "delete"`)
*Why tempting:* fewer tools looks cleaner; a single endpoint feels tidy.
*Why wrong:* the model selects against *names and descriptions*, not enum values buried inside inputs. One mega-tool hides the intent from the selector; misrouting (picking "lookup" when it should be "delete", or vice versa) goes unnoticed until the wrong data is modified. Split into separately-named tools with distinct descriptions.

### Use `tool_choice: any` to force the model to pick the right tool
*Why tempting:* if the model picks the wrong tool, "force it harder" is the obvious next move.
*Why wrong:* `any` forces *a* tool call, not the *right* tool call. It's a band-aid for a bad description. Usually the right fix is to rewrite the descriptions with better positive/negative boundaries. Reserve forcing for genuinely scripted steps.

### Expose an action like `place_order` as an MCP resource
*Why tempting:* "resource" sounds general-purpose; maybe it can do anything.
*Why wrong:* MCP resources are read-only content catalogs — static documents, style guides, reference material. Actions with side effects are MCP tools. Getting this backward is a recurring distractor; remember "tools act, resources inform".

### Literal secrets in `.mcp.json`
*Why tempting:* it's the fastest way to get the integration working locally; you promise to rotate later.
*Why wrong:* committed secrets enter git history and are effectively permanent. `${ENV_VAR}` expansion is one line of ceremony and keeps the file safe to check in. Every `.mcp.json` entry that takes a credential should use `${...}`.

### Team MCP server in `~/.claude.json`
*Why tempting:* your config works; sharing feels like someone else's problem.
*Why wrong:* user scope isn't shared. Each teammate will need to reconfigure on their own machine, and the team will drift out of sync. Team-shared MCP servers belong in `<repo>/.mcp.json`, committed, with `${ENV_VAR}` placeholders for secrets.

### Use Glob to search inside files
*Why tempting:* Glob "finds files matching a pattern" — that phrasing is ambiguous, and searching for a string inside files feels like "matching files to content".
*Why wrong:* Glob matches **paths**, not contents. For content search, Grep. For filename patterns, Glob. Using Glob with `import pandas` as the pattern will match zero or confused results.

### `bash cat` to read a file whose path you know
*Why tempting:* you're a veteran shell user; `cat` is muscle memory.
*Why wrong:* Read is the dedicated tool: it's pageable, has defined return shape, and doesn't require a Bash shell-out. Use Read for known paths. Bash is for anything without a dedicated tool (git, test runners, miscellaneous shell).

---

## Domain 3 — Claude Code Configuration & Workflows

### Put every rule in root `CLAUDE.md`
*Why tempting:* one file is easier to maintain than many; you see all the rules at once.
*Why wrong:* every line in root CLAUDE.md is paid for on every turn, including turns editing code the rule has nothing to do with. Attention degrades with bloat; irrelevant rules drown out relevant ones. Path-specific rules belong in `.claude/rules/*.md` with `paths:` frontmatter.

### Rule file with no `paths:` frontmatter
*Why tempting:* you wrote a rule and moved on; frontmatter feels optional.
*Why wrong:* without `paths:`, the rule loads globally for every turn — same cost as root CLAUDE.md but harder to find. Add `paths:` to scope it, or move it into root CLAUDE.md if it really is global and belongs there.

### Use a rule for a user-initiated action like "/review the PR"
*Why tempting:* "the model should review; a rule tells the model to review" — the mental model conflates guidance with invocation.
*Why wrong:* rules are passive; the user cannot type a rule into the terminal. User-initiated workflows are **commands** (`.claude/commands/<name>.md`). Rules fire automatically based on file paths; commands fire on explicit invocation.

### Use a command for a tool-scoped multi-step workflow
*Why tempting:* it "runs when the user asks"; commands are the mechanism you already know.
*Why wrong:* commands are saved prompts that run in the current session; they can't scope tools or isolate context. For multi-step work with tool scoping and (usually) isolation, you want a skill with `allowed-tools` and `context: fork`.

### Skill does heavy exploration without `context: fork`
*Why tempting:* `context: default` is the default; it feels safer to leave defaults alone.
*Why wrong:* every intermediate turn (30 file reads, 5 greps, diff parses) lands in the main session's history and pollutes it. `context: fork` runs the skill in an isolated session; only its final message comes back. The default is fine for short skills; multi-step skills want fork.

### Team-wide config in `~/.claude/CLAUDE.md`
*Why tempting:* you're the main user; your user config works; why bother with project scope?
*Why wrong:* user scope is personal — not committed, not shared. Your teammates won't get it, and behavior will drift across the team. Team config goes in project scope (`<repo>/CLAUDE.md` or `<repo>/.claude/CLAUDE.md`), committed to git.

### "Add instructions to CLAUDE.md that the skill should fork its context"
*Why tempting:* prompt guidance is the generic control knob; it *feels* like it should work.
*Why wrong:* isolation is a runtime mechanism; the SDK has to create a fresh session. A CLAUDE.md bullet can't instantiate a new session. Set `context: fork` in the SKILL.md frontmatter — that's the mechanism the runtime honors.

### `@import` to "save tokens"
*Why tempting:* splitting a file feels like it reduces size.
*Why wrong:* `@import` inlines content at load time. The resulting prompt has the same token count whether it was one file or ten imports. Use `@import` for modularity (shared fragments, ownership, scannability), not size.

### Plan mode for a 3-line null check
*Why tempting:* "plan before act" is always a prudent habit; plan mode feels responsible.
*Why wrong:* plan mode has overhead — an exploration phase, a written plan, an approval round trip. For a 3-line well-specified edit, that overhead dwarfs the actual change. Plan mode is for *scope ambiguity*, multi-file work, or hard-to-reverse changes.

### Direct execution for a 45-file migration
*Why tempting:* "let Claude just do it" is fast; plan mode feels slow.
*Why wrong:* without a written plan, coverage is invisible. At some point mid-migration the agent loses track and ships a half-migrated codebase. Plan mode produces a file-by-file checklist; the checklist IS the coverage map.

### Same session generates AND reviews in CI
*Why tempting:* one session is simpler; `--resume` reuses context; it's faster.
*Why wrong:* self-review retains reasoning bias. The reviewer already "knows" why each choice was made and will rationalize its own mistakes instead of catching them. Independence is the property you need — separate fresh sessions, no `--resume`, artifacts-only.

### Regex natural-language CI output
*Why tempting:* `claude -p` returns text; you're used to parsing text; regex is universal.
*Why wrong:* natural-language phrasing drifts across model updates and inputs. A regex that works today fails silently next month. `--output-format json --json-schema` gives you a stable contract the pipeline can rely on.

### Message Batches for a blocking pre-merge check
*Why tempting:* batches are 50% cheaper; cost savings are attractive.
*Why wrong:* batches have up to 24 h window and no SLA. Your PR sits in "checks pending" for an unpredictable duration — no engineer will accept that. Batches are for latency-tolerant bulk; synchronous `claude -p` is for blocking paths.

### "Make it better" as iteration feedback
*Why tempting:* it's fast to type and "the model should know what I mean".
*Why wrong:* it doesn't. Vague feedback wastes a turn guessing. Concrete feedback references a file, function, identifier, or expected behavior: "Extract the nested try/except into `_safe_parse(row)`; keep the outer loop under 10 lines."

---

## Domain 4 — Prompt Engineering & Structured Output

### "Output JSON with these fields" in natural language
*Why tempting:* it's the simplest-seeming approach; the model is good at JSON.
*Why wrong:* natural-language JSON output produces trailing commas, markdown fences, commentary before/after the JSON, unquoted keys, and shape drift across runs. The correct mechanism is `tool_use` with `input_schema` — the SDK guarantees JSON syntactic validity.

### "JSON Schema eliminates all extraction errors"
*Why tempting:* schemas are strict; the output validates; it feels complete.
*Why wrong:* the schema guarantees **shape** (types, required fields, enum membership). It does NOT guarantee **meaning**. The model can put the customer's name in `vendor_name`, pick the wrong severity from an enum, or hallucinate a plausible but absent date. Semantic correctness needs downstream validators or human review.

### `tool_choice: auto` for mandatory extraction
*Why tempting:* `auto` is the default; defaults are usually sensible.
*Why wrong:* `auto` lets the model decide whether to call any tool. On some inputs it will reply in prose and skip the extraction entirely. For mandatory extraction, `{"type": "tool", "name": "..."}` (forced specific) guarantees the tool call.

### Non-nullable required fields everywhere
*Why tempting:* "required" sounds like "definitely got it"; nullables feel sloppy.
*Why wrong:* non-nullable required fields force the model to produce a value on every input. When the source is missing the data, the model fabricates a plausible one. Nullable fields (`type: ["string", "null"]`) combined with a null-when-absent rule give the model a legitimate "absent" answer — that's the primary anti-hallucination lever.

### Closed enum with no `"other"`
*Why tempting:* enums are precise; listing exactly the allowed values feels rigorous.
*Why wrong:* real input domains have novel values. A closed enum forces the model to either miscategorize silently (pick the closest enum value — catastrophic when downstream code routes on it) or violate the schema (which might not even surface). Adding `"other"` + a `detail` field preserves the raw signal and keeps the pipeline extensible.

### Vague criteria like "high confidence only" or "be conservative"
*Why tempting:* it sounds professional; it's how humans talk about risk.
*Why wrong:* "high confidence" has no shared definition between you and the model; the model's internal calibration drifts per input and model version. The fix is categorical: "respond only if the source contains a direct, verbatim answer." Thresholds, feature checks, explicit enums — not vibes.

### Self-reported confidence 1–10
*Why tempting:* "the model knows when it's unsure" — intuitive, and cheap to implement.
*Why wrong:* LLM self-reported confidence is badly miscalibrated, especially on hard cases (it tends to be confidently wrong). Measured calibration on held-out data, field-level empirical confidence, and categorical criteria work; asking the model to rate itself does not.

### One canonical few-shot example
*Why tempting:* "one example is better than zero; let me show it the happy path."
*Why wrong:* one example looks like pattern noise to the model, not pattern signal. Few-shot works at 2–4 examples, covering **ambiguous/edge cases** (where the model actually fails), with reasoning shown. Canonical cases don't teach; the model already gets those right.

### Fifteen few-shot examples to cover every case
*Why tempting:* more = better; exhaustive = rigorous.
*Why wrong:* diminishing returns past ~4, plus context bloat, plus over-fitting to the examples (the model mimics surface features instead of generalizing). 2–4 carefully chosen edge cases outperform 15 mediocre ones.

### Validation-retry with a generic "try again"
*Why tempting:* you saw the validation failed; retrying feels like resilience.
*Why wrong:* the model doesn't know what failed. It will produce the same output. Useful retry loops append the **specific validator error** and the **failed output** to the retry prompt so the model can correct the actual defect. And if the source information is absent, no retry will help; escalate or set null.

---

## Domain 5 — Context Management & Reliability

### Progressive summarization of case notes
*Why tempting:* it keeps the context small; it feels efficient.
*Why wrong:* summarization is lossy on exactly the details you cannot afford to lose — refund amounts, order numbers, promise dates, specific policy references. Extract those into a persistent "case facts" block that survives compaction; summarize the narrative, preserve the facts.

### Put the key finding in the middle of a long context
*Why tempting:* you put it where it logically flowed in the document.
*Why wrong:* the lost-in-the-middle effect: models attend best to the start and the end of long context. Content in the middle is disproportionately forgotten. Put key findings at the start or the end, use section headers, and order position-aware.

### Silent empty-result-set on tool timeout
*Why tempting:* returning `[]` is simple; the caller can "see there are no results".
*Why wrong:* the caller cannot distinguish "no matches" from "I failed". The agent tells the user "no orders found" when actually the warehouse API was down. Return a structured error — `{isError: true, errorCategory: "timeout", isRetryable: true, ...}` — so the caller can retry, escalate, or explain.

### Multiple matches → pick the most plausible one
*Why tempting:* the agent is trying to be helpful; picking one keeps the conversation moving.
*Why wrong:* heuristic guessing destroys data integrity. The "most plausible" match might be the wrong account, the wrong order, the wrong patient. Ask the user for more identifying information. The small friction of one clarifying question beats the large cost of a wrong action.

### Pick one source when sources conflict
*Why tempting:* a clean answer is more useful than "it depends"; you want to look authoritative.
*Why wrong:* silently picking discards the disagreement signal — which is often the most important information in the synthesis. Preserve both findings, attribute them, note the conflict, and include publication dates so the reader can weigh recency.

### Ignore publication dates in synthesis
*Why tempting:* the findings are what matter; dates feel like metadata.
*Why wrong:* old findings and new findings on the same question read as a contradiction when they're really a progression. Recording `publication_date` with every claim lets the synthesizer distinguish "contradiction" from "the field updated" and report accordingly.

### Aggregate accuracy only, no stratification
*Why tempting:* one headline number is easy to report and track over time.
*Why wrong:* aggregates hide domain-specific failure modes. The pipeline may be 98% accurate overall but 40% on a specific document type that represents 5% of volume — a disaster for the users receiving those. Stratify by document type AND by field; sample accordingly.

---

## How to use this list in the last days

1. **Saturday before exam:** read each section end-to-end once. For each anti-pattern, pause and try to generate the exam question that would make this distractor tempting. Saying the trap out loud is the drill.
2. If you find yourself nodding at the "why tempting" framing, that's a signal you'd fall for it on the exam. Tag it in `notes/weak_spots.md`, reread the underlying week's reference.md for that topic.
3. Pair this file with `reference.md`'s wrong-answer table for the full picture: master table for rapid rejection, this file for the *why* when two answers feel similar.
