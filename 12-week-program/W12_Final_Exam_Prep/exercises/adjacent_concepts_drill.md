# Adjacent-Concept Discrimination Drill

The hardest exam questions don't have one obviously-wrong distractor — they have **two plausible answers** where you pick between closely-related concepts. This file is a catalog of those pairs. For each, the drill is:

1. Read the Concept A / Concept B description.
2. Cover the discriminator column. Ask yourself: **what's the one test that tells these apart?**
3. Uncover. Compare.
4. Read the "trap" column to understand which direction exam writers prefer to fool candidates.

Pairs are organized by domain. Work through domain-by-domain, or shuffle for variety on a second pass.

---

## Domain 1 — Agentic Architecture & Orchestration

### Pair 1.1 — `PreToolUse` hook vs `PostToolUse` hook
| Concept A (PreToolUse) | Concept B (PostToolUse) |
|---|---|
| Fires **before** a tool call executes | Fires **after** the tool call returned |
| Can **block or modify** inputs | Can **shape** what the model sees next (redaction, normalization, logging) |
| The right layer for **policy enforcement** (refund caps, auth checks, dangerous-file guards) | The right layer for **data cleanup** (strip PII from outputs, normalize dates, log) |

**Discriminator:** *Does the wrong outcome have already happened when the hook fires?* If yes, you need PreToolUse. Refunds, deletions, emails → PreToolUse. "Strip SSNs from the model's next read" → PostToolUse.

**Trap:** exam asks "which hook prevents X destructive action" — PostToolUse is the tempting wrong answer because it does see the call.

---

### Pair 1.2 — `tool_choice: auto` vs `any` vs forced-specific
| `auto` | `any` | `{"type":"tool","name":"..."}` |
|---|---|---|
| Model decides whether to call *any* tool | Model **must** call some tool this turn, any of them | Model **must** call *this specific* tool this turn |
| Right for general agent loops (default) | Right when you need a tool call but model can choose which (rare, usually structured-output extraction) | Right for scripted steps or mandatory extraction |

**Discriminator:** *"If no tool is called, is the turn still useful?"* Yes → `auto`. No, but any tool works → `any`. No, and only one tool is correct → forced-specific.

**Trap:** exam gives you an extraction task that fails intermittently because the model sometimes replies in prose. "Switch to `any`" looks right. Usually the correct answer is **forced-specific**; `any` is only right when multiple extraction tools are valid and the model picks.

---

### Pair 1.3 — `fork_session` vs `--resume` vs fresh session
| `fork_session` | `--resume <name>` | Fresh session |
|---|---|---|
| Clones history up to a point, lets two branches diverge | Continues the exact same session as if never interrupted | Starts with empty history |
| Right for **branched exploration** ("what if we tried approach B?") | Right for **temporary interruption** (lunch, machine reboot) on a clean session | Right when **history is poisoned** (failed destructive action, bad reasoning trail) |

**Discriminator:** *"Is the prior history helping or hurting?"* Helping, and you want it twice → fork. Helping, and you want it once → resume. Hurting → fresh.

**Trap:** exam describes a failed refund; candidate wants to "resume to preserve context". Correct answer is **fresh** (or fork from a clean point *before* the failure) — resuming inherits the broken reasoning.

---

### Pair 1.4 — Subagent via `Task` tool vs inline tool call
| `Task`-spawned subagent | Inline tool call (coordinator calls directly) |
|---|---|
| Subagent runs in **isolated context**; coordinator only sees return message | Tool call's full output lands in coordinator's context |
| Right for **verbose exploration** (40 file reads, discovery) | Right for **cheap, structured** tool results (single API lookup, `get_weather`) |
| Requires `"Task"` in `allowedTools` | Requires the specific tool in `allowedTools` |

**Discriminator:** *"Will this expand the coordinator's context with stuff it doesn't need?"* Yes → delegate to subagent. No → inline.

**Trap:** "Scale the agent by giving it a Task tool for every subtask" — wrong. Over-delegation adds coordinator overhead for cheap lookups.

---

### Pair 1.5 — Fixed prompt chain vs adaptive decomposition
| Fixed chain | Adaptive |
|---|---|
| Steps known in advance; coordinator scripts them | Coordinator inspects and decides decomposition at runtime |
| Right for **known-shape** tasks (extract → validate → store) | Right for **open-ended** tasks (research a topic — subtopics not knowable in advance) |
| Simpler, faster, hook-friendly between stages | More flexible, but adds a reasoning turn and a failure mode |

**Discriminator:** *"Do I know the steps before I start?"* Yes → fixed chain. No → adaptive.

**Trap:** candidate reaches for adaptive because "it sounds smarter". For fixed-shape pipelines it's strictly worse — more turns, more failure modes, less debuggable.

---

## Domain 2 — Tool Design & MCP

### Pair 2.1 — MCP **tool** vs MCP **resource**
| Tool | Resource |
|---|---|
| Performs an **action** (side effects allowed) | Provides **read-only content** (static documents, style guides) |
| Model invokes via `tool_use` block | Model reads via resource URI |
| Example: `place_order(sku, qty)` | Example: `style-guide://eng/python` |

**Discriminator:** *"Does calling this change state?"* Yes → tool. No → resource.

**Trap:** "Expose `place_order` as a resource" — wrong, actions go in tools. "Expose the style guide as a tool" — wrong, static content goes in resources.

---

### Pair 2.2 — `Glob` vs `Grep` vs `Read` vs `Bash cat`
| Glob | Grep | Read | Bash cat |
|---|---|---|---|
| Match **file paths** by pattern | Search **file contents** for regex | Read a **known file** | Shell-out (last resort) |
| `**/*.test.ts` | `import pandas` across `.py` | `/src/app.py` | Anything else |

**Discriminator:** *"Do I know the path, or am I searching?"* Known path → Read. Searching paths → Glob. Searching contents → Grep. None of the above → Bash.

**Trap:** "Use Glob to find `import pandas`" — wrong, Glob matches paths not contents. "Use Bash cat to read `/src/app.py`" — wrong, Read is the dedicated tool.

---

### Pair 2.3 — `.mcp.json` vs `~/.claude.json`
| `<repo>/.mcp.json` (project scope) | `~/.claude.json` (user scope) |
|---|---|
| **Shared** with the team, committed to git | **Personal** to one machine, not shared |
| Use `${ENV_VAR}` placeholders for secrets | Can hold personal tokens (still best as env) |
| Team-wide MCP servers belong here | Personal productivity MCP servers belong here |

**Discriminator:** *"Will every teammate need this MCP server?"* Yes → `.mcp.json`. No → `~/.claude.json`.

**Trap:** "Put the team GitHub MCP server in `~/.claude.json`" — wrong, drift; teammates won't have it.

---

### Pair 2.4 — Split tools vs mega-tool with `mode` enum
| Split: `lookup_customer`, `create_customer`, `delete_customer` | Mega: `customer(mode="lookup" \| "create" \| "delete")` |
|---|---|
| Distinct **names** and **descriptions** — the model selects accurately | Name and description are generic; intent hidden in enum |
| Correct pattern | Anti-pattern |

**Discriminator:** *"Does the model select against the tool name, or against a nested enum?"* Name. Always split.

**Trap:** "Mega-tool is cleaner code" — yes for humans, wrong for model selection.

---

## Domain 3 — Claude Code Configuration

### Pair 3.1 — Command vs Skill vs Rule
| `.claude/commands/` | `.claude/skills/` | `.claude/rules/` |
|---|---|---|
| **User-initiated** saved prompt (`/review`) | **Claude-initiated** capability with tool scoping and optional context fork | **Passive** guidance loaded when `paths:` match |
| Runs in current session | Can run with `context: fork` (isolated) | Auto-loaded when editing matching files |
| Right for: manual workflows | Right for: multi-step capabilities with isolation (exploration, synthesis) | Right for: "when editing `*.test.tsx`, use vitest not jest" |

**Discriminator:** *"Who triggers this, and does it need tool scoping or isolation?"*
- User types `/X` → command
- Claude invokes based on request + needs scope/isolation → skill
- Auto-load based on file paths → rule

**Trap:** "I want a `/review` that Claude uses automatically" — conflates user-trigger with auto. Commands are user-triggered; for auto-invocation with scope, use a skill.

---

### Pair 3.2 — Root `CLAUDE.md` vs `.claude/rules/*.md` with `paths:`
| Root `CLAUDE.md` | `.claude/rules/*.md` with `paths:` |
|---|---|
| Loaded on **every turn** | Loaded only when `paths:` matches the file being edited |
| Right for **truly global** rules (monorepo-wide style) | Right for **path-scoped** rules (only tests, only frontend, only migrations) |

**Discriminator:** *"Does this rule apply when editing an unrelated file?"* Yes → root CLAUDE.md. No → scoped rule.

**Trap:** "Put every rule in root for discoverability" — context bloat, attention degrades. Scope it.

---

### Pair 3.3 — `context: fork` vs `context: default` in SKILL.md
| `context: fork` | `context: default` |
|---|---|
| Skill runs in **isolated session**; only final message returns | Skill runs in **current session**; all intermediate turns land in main history |
| Right for: multi-step exploration (30 reads, 5 greps, diff parses) | Right for: short, fast skills where isolation overhead isn't worth it |

**Discriminator:** *"Will this skill's intermediate steps pollute main context?"* Yes → fork. No → default.

**Trap:** "Add to CLAUDE.md: 'skills should fork their context'" — wrong layer, `context: fork` is frontmatter not prose instruction.

---

### Pair 3.4 — Plan mode vs direct execution
| Plan mode | Direct execution |
|---|---|
| Exploration phase + written plan + approval round-trip | Claude does it immediately |
| Right for: **scope ambiguity**, multi-file work, hard-to-reverse changes | Right for: small, well-specified, reversible edits |
| Overhead pays off when the task is big or risky | Overhead is pure cost on small tasks |

**Discriminator:** *"Would a written plan materially reduce risk?"* Yes → plan mode. No → direct.

**Trap:** "Always plan first" or "Never plan, go faster" — both wrong. Size-matched.

---

### Pair 3.5 — Sync `claude -p` vs Message Batches
| Sync `claude -p` | Message Batches |
|---|---|
| Immediate response (seconds) | Up to 24 h window, **no SLA** |
| Full price | 50% cheaper |
| Right for: **blocking** paths (CI pre-merge, user-facing) | Right for: **latency-tolerant** bulk (overnight scoring, weekly reports) |

**Discriminator:** *"Is anyone waiting?"* Yes → sync. No → batch.

**Trap:** "Use batches for CI to save money" — wrong, queueing kills PR velocity.

---

## Domain 4 — Prompt Engineering & Structured Output

### Pair 4.1 — NL JSON request vs `tool_use` with `input_schema`
| "Output JSON with these fields..." in prose | Declare a tool with `input_schema`; read `tool_use.input` |
|---|---|
| Shape drifts, trailing commas, markdown fences, commentary | SDK-guaranteed JSON syntactic validity |
| Anti-pattern | Correct |

**Discriminator:** not really a judgment call — tool_use is the mechanism.

**Trap:** appears in many forms: "give the model a few-shot JSON example and ask for same shape" — still wrong if the mechanism is NL.

---

### Pair 4.2 — Schema validation vs semantic validation
| Schema (structure) | Semantic (meaning) |
|---|---|
| Validates **types, required fields, enum membership** | Validates the **extracted values actually correspond to the source** |
| Handled by JSON Schema / Pydantic | Handled by a second LLM pass or human review |

**Discriminator:** schema guarantees shape, not correctness. Both are needed for reliable extraction.

**Trap:** "Schema passed, extraction is correct" — wrong. The model can put the customer's name in `vendor_name` with perfectly-valid schema output.

---

### Pair 4.3 — Closed enum vs open enum with `"other"`
| Closed enum: `["low","medium","high"]` | Open: `["low","medium","high","other"]` + `detail` field |
|---|---|
| Right when the domain is **truly finite and stable** | Right when **novel values** can appear |
| Model may silently miscategorize novel inputs | Novel values land in "other" with raw signal preserved |

**Discriminator:** *"Can a future input legitimately not fit any of these?"* Yes → open. No → closed.

**Trap:** "Closed is more rigorous" — wrong, rigor without realism loses the signal.

---

### Pair 4.4 — Non-nullable required vs nullable
| Non-nullable required everywhere | Nullable with "null when absent" rule |
|---|---|
| Model **fabricates** when source is missing data | Model returns `null` — explicit "don't know" |
| Anti-hallucination hole | Primary anti-hallucination lever |

**Discriminator:** *"Is it realistic for this field to be absent?"* Yes → nullable. No → non-nullable.

**Trap:** "Required = no missing values" — wrong, it forces fabrication.

---

### Pair 4.5 — 0 / 1 / 2–4 / 15 few-shot examples
| 0 examples | 1 example | 2–4 examples | 15 examples |
|---|---|---|---|
| Fine for well-known tasks | Looks like noise, not signal — model reads surface features | **Sweet spot** — especially for edge cases | Diminishing returns + context bloat + over-fitting to examples |

**Discriminator:** 2–4 carefully-chosen **edge cases** (with reasoning shown) is the target. Canonical examples don't teach what the model already gets right.

**Trap:** "More examples is always better" — false past ~4.

---

### Pair 4.6 — Self-reported confidence vs empirical calibration
| Self-reported (model says 1–10) | Empirical (measured on held-out data) |
|---|---|
| Badly miscalibrated, especially on hard cases | True calibration signal |
| Feels principled; isn't | Actually works |

**Discriminator:** confidence must be measured, not declared.

**Trap:** "Ask the model for confidence, route low-confidence to human" — fails silently because the model is most confident when most wrong on the traps.

---

## Domain 5 — Context Management & Reliability

### Pair 5.1 — Progressive summarization vs persistent case facts
| Summarize everything each turn | Extract facts into persistent "case facts" block + summarize narrative |
|---|---|
| Loses numbers, dates, order IDs, promise dates (the stuff you can't afford to lose) | Preserves the facts; summarizes the conversation around them |

**Discriminator:** *"Is this a value that has to be exact?"* Yes → pin it in case facts. No → summarize OK.

**Trap:** "Summarize to keep context small" — as a single lever, it's wrong on long support sessions.

---

### Pair 5.2 — Sentiment trigger vs categorical trigger for escalation
| Sentiment-based | Categorical |
|---|---|
| "Customer is upset → escalate" | "Customer explicitly demanded", "policy gap detected", "unable to progress" |
| Signal on the wrong axis | Signal on the right axis |

**Discriminator:** escalation is about **case complexity**, not emotional state.

**Trap:** "Route angry customers to a human" — misses polite customers with unsolvable cases, escalates solvable angry ones.

---

### Pair 5.3 — Silent failure vs structured error
| Return `[]` on timeout | `{isError: true, errorCategory: "timeout", isRetryable: true, message: "..."}` |
|---|---|
| Caller can't tell "no matches" from "I failed" | Caller can retry, escalate, or explain the real failure |

**Discriminator:** the caller needs enough information to **decide what to do**.

**Trap:** "`[]` is fine, caller sees empty" — fails under outage; agent lies to user.

---

### Pair 5.4 — Multiple matches → guess vs ask
| Heuristic pick of "most plausible" | Ask for more identifying info |
|---|---|
| Destroys data integrity (wrong account / order / patient) | Small friction now, beats wrong action later |

**Discriminator:** *"Could picking wrong here cause real harm?"* Yes → ask.

**Trap:** "Keep the conversation moving" — wrong if the next step commits to the wrong record.

---

### Pair 5.5 — Pick one source vs preserve-both on conflict
| Silently pick "most plausible" source | Preserve both, attribute each, note conflict, include `publication_date` |
|---|---|
| Discards disagreement signal (often the most important info) | Keeps the signal; reader can weigh recency |

**Discriminator:** the conflict itself is load-bearing information.

**Trap:** "A clean answer is more useful" — not when it hides that the sources disagree.

---

### Pair 5.6 — Aggregate accuracy vs stratified accuracy
| One headline number (e.g., 98%) | Accuracy by document type × field |
|---|---|
| Hides catastrophic failure modes on rare types | Surfaces 40%-accurate document types buried inside 98% aggregate |

**Discriminator:** you need to see *where* the system fails, not just *how often*.

**Trap:** "Report accuracy" — vague; exam expects stratified.

---

### Pair 5.7 — "Increase context window" vs structural fixes
| Bigger window | `/compact`, fork + seed, scratchpad file, fresh session |
|---|---|
| Attention quality doesn't scale with window size | Structural levers that actually work |
| **Lost-in-the-middle** persists at any size | |

**Discriminator:** stale session is a structure problem, not a capacity problem.

**Trap:** "Upgrade to bigger window" — doesn't fix stale context.

---

## How to run this drill

- **Twice during the program:** once at end of W11 (before Practice Exam 1), once at end of W12 (before the real exam).
- **Per pair:** 30 seconds max. If you can't state the discriminator cleanly in 30s, the pair is a weak spot → add a flashcard to `W12/notes/weak_spots.md` with `⭐` prefix.
- **Don't read top-to-bottom passively.** Shuffle order on second pass. Cover columns and self-test.

## What to do when two exam answers both sound right

1. Name the two concepts.
2. Find the **discriminator** (this file is your catalog).
3. Apply it to the scenario in the question.
4. If both pass the discriminator: re-read the question for the *specific mechanism* the question is testing (hook timing? tool_choice mode? scope layer?). The question usually signals which axis it's on.
