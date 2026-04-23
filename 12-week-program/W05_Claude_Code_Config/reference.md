# W05 Reference — Claude Code Configuration (Domain 3.1–3.3)

Complete, self-contained study material for Week 5. Read this end-to-end. Every concept the exam tests for task statements 3.1, 3.2, and 3.3 is included here.

Prerequisites: W04 (MCP server config — `.mcp.json` vs `~/.claude.json` — is the same file layout pattern that CLAUDE.md, rules, commands, and skills all reuse. If "project scope vs user scope" still feels fuzzy, re-read W04 first).

---

## 1. The mental model — scope, merge, path

Everything in Claude Code's configuration system sits on three axes. Know them cold:

1. **Scope** — who the config belongs to.
   - **User scope:** `~/.claude/…` — your machine, all projects.
   - **Project scope:** `<repo>/.claude/…` or `<repo>/CLAUDE.md` — the team, checked into git.
   - **Subdirectory scope:** `<repo>/some/sub/dir/CLAUDE.md` — applies only when Claude Code is working inside that subtree.

2. **Merge semantics** — two configs at different scopes don't *replace* each other; they **stack**. User-level config is always in effect; project-level config layers on top; subdirectory config layers on top of that. More specific scopes override (not erase) less specific ones when they disagree.

3. **Path filter** — some config (`rules/`, skills' `paths` hint, subdirectory CLAUDE.md) only activates when Claude Code is touching matching files. Others (root CLAUDE.md, user CLAUDE.md, commands, skills, MCP servers) are always in effect for the session.

The entire domain is "where does this piece of config live, and when does it activate." Memorize those two questions.

---

## 2. CLAUDE.md hierarchy

CLAUDE.md files are the primary mechanism for giving Claude Code persistent context about your code and conventions. They're Markdown files that get concatenated into every request's system prompt, in a defined order.

### The three levels

| Level | Location | Loaded when | Purpose |
|---|---|---|---|
| **User** | `~/.claude/CLAUDE.md` | Every Claude Code session, every project | Your personal preferences (commit style, language prefs, "always prefer absolute imports", etc.) |
| **Project root** | `<repo>/CLAUDE.md` **or** `<repo>/.claude/CLAUDE.md` | Any session started inside the repo | Team conventions — tech stack, directory layout, testing framework, code-style rules the whole team shares |
| **Subdirectory** | `<repo>/some/subdir/CLAUDE.md` | Only when Claude Code is operating on files within that subdir (and its descendants) | Narrow, local guidance — e.g., "this folder uses React Server Components; do not import client hooks here" |

Claude Code walks from the current working directory upward, collecting every CLAUDE.md it finds, and then layers the user-level file on top of that chain. All matching files are concatenated into the system prompt.

### Precedence — "more specific overrides more general"

When two levels contradict, the **more specific scope wins** for the file/directory it covers:

- User says: "use 2-space indentation."
- Project root says: "we use 4-space indentation."
- Inside the project, **4-space wins** (project is more specific than user).

- Project root says: "prefer tabs."
- `src/frontend/CLAUDE.md` says: "this folder uses 2-space indentation (Prettier config)."
- Inside `src/frontend/`, **2-space wins**. Elsewhere in the repo, the root rule applies.

"Override" is informal — technically both files are still in the system prompt. The later, more-specific rule is the one the model follows because that's how prompt precedence reads (later, more specific instructions beat earlier, general ones). The practical effect is override.

### What belongs where — and what doesn't

The single most common mistake: **dumping everything into root CLAUDE.md**. Every line in root CLAUDE.md is paid for on every Claude Code turn in that repo — including turns that are nowhere near the code the rule describes. If a rule only matters when editing SQL migrations, it belongs in `.claude/rules/migrations.md` with a `paths:` filter, not root CLAUDE.md.

| Put in root CLAUDE.md | Do NOT put in root CLAUDE.md |
|---|---|
| Tech stack + language versions | Testing-framework-specific rules (→ path rule) |
| Repo directory layout | DB-migration-specific rules (→ path rule) |
| Team-wide code conventions | Step-by-step multi-turn workflows (→ skill) |
| Release / branch naming rules | One-off capabilities invoked on demand (→ command) |
| Links to key internal docs (via `@import`) | Huge reference material (→ import or skill) |

### Diagnosing hierarchy issues with `/memory`

When a teammate reports *"Claude Code isn't following our testing convention"* — or you see inconsistent behavior across sessions — the first diagnostic is:

```
/memory
```

The `/memory` command lists **every CLAUDE.md file currently loaded** for the active session: user-level, project root, any subdirectory files inherited by the cwd, plus all `@import`ed fragments. It shows the exact merge order.

Typical failure modes it catches:

- **"New teammate isn't receiving the instruction"** → Their instruction is in `~/.claude/CLAUDE.md` (user scope, their machine only), not `<repo>/CLAUDE.md` (project scope, shared via git). `/memory` reveals the fix location.
- **"Rule stopped applying after I `cd`'d into a subdirectory"** → A subdirectory CLAUDE.md is overriding the parent. Confirmed by running `/memory` before and after the `cd`.
- **"`@import` isn't resolving"** → The imported path is wrong relative to the importing file; `/memory` shows whether the import resolved and produced content.

**Exam angle:** the exam may describe a "config is inconsistent across sessions" scenario and ask which tool to reach for. The answer is `/memory` — not re-reading CLAUDE.md manually, not re-cloning the repo, not guessing.

---

## 3. `@import` — modular configs

CLAUDE.md supports `@import` to pull another Markdown file's contents inline at load time. Syntax:

```markdown
# Project conventions

Our tech stack is Node 20 + TypeScript + Postgres.

@import ./.claude/shared/style.md
@import ./.claude/shared/testing.md
```

What that does: at load time, Claude Code reads `style.md` and `testing.md` and inlines their content into the CLAUDE.md that referenced them. The imports themselves can contain further `@import`s (transitively resolved).

### When to use `@import`

- **Shared fragments between multiple CLAUDE.md files.** Root and a subdirectory both want the same code-style rules → put them in `shared/style.md`, import from both.
- **Keeping root CLAUDE.md scannable.** A human reader of `CLAUDE.md` can see the outline; detail lives in imported files.
- **Git-managed separation of concerns.** Team-wide rules in one file, narrow rules in another, one owner per file.

### When NOT to use `@import`

- **To conditionally load content.** `@import` is unconditional — it always inlines. If you want conditional loading (only when editing test files), that's a `.claude/rules/*.md` with `paths:` frontmatter, not an import.
- **To hide size.** Imports don't save tokens. Whatever you `@import` is still in the prompt.

---

## 4. Path-scoped rules — `.claude/rules/*.md`

`.claude/rules/` is the mechanism for **passive, path-scoped guidance**. Files here get loaded into the system prompt *only* when Claude Code is operating on files matching the rule's path glob.

### Anatomy

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
---

# Testing conventions

- Use Vitest, not Jest. Import from "vitest", not "@jest/globals".
- Every test file must have exactly one top-level `describe(...)` block.
- Snapshot tests live under `__snapshots__/`. Do not inline snapshots.
```

Frontmatter keys:

| Key | Purpose |
|---|---|
| `paths` | Required. List of glob patterns. Standard globs: `**` (any depth), `*` (single segment), `{a,b}` (alternation). |
| `description` | Optional human-readable summary. Does not affect loading. |

### Loading rules

- Rule file loads when **any** file Claude Code is currently reading/editing matches **any** glob in `paths`.
- A rule with no `paths:` frontmatter (or no frontmatter at all) loads **globally** — almost always a mistake. If it should load globally, put it in root CLAUDE.md instead.
- Multiple rules can load simultaneously. Editing `src/db/migrations/0042.sql` could match both a `migrations.md` rule and a `sql.md` rule; both land in the prompt.

### Rule vs CLAUDE.md — why this exists

A subdirectory CLAUDE.md only fires when you're *in* that subtree. A path rule fires based on the **file pattern**, regardless of where the file lives. Rules handle cross-cutting concerns ("all test files, anywhere in the repo") that don't map to a single directory.

---

## 5. Custom slash commands — `.claude/commands/*.md` vs `~/.claude/commands/*.md`

Slash commands are **user-initiated, reusable prompts**. A file at `.claude/commands/review.md` becomes `/review` inside Claude Code. The file's contents are sent as a user message (with the user's arguments substituted in) when the command is invoked.

### Two scopes

| Scope | Path | Visible where |
|---|---|---|
| **Project command** | `<repo>/.claude/commands/<name>.md` | Only in sessions within this repo. Checked into git. Shared with the team. |
| **User command** | `~/.claude/commands/<name>.md` | In every session on your machine, every project. Personal. |

### Resolution order when names collide

If both `<repo>/.claude/commands/review.md` and `~/.claude/commands/review.md` exist, **the project command wins inside that repo**. Project scope is more specific, same precedence principle as CLAUDE.md.

### Command file anatomy

```markdown
---
description: Review staged changes for bugs and style
argument-hint: "[optional PR number]"
---

Review the currently staged changes. Focus on:
1. Logic bugs and off-by-one errors
2. Missing error handling
3. Non-compliance with rules in `.claude/rules/`

If argument was provided ($ARGUMENTS), treat it as a GitHub PR number and include that PR's description in your review.
```

The frontmatter is metadata for the UI (help text, argument hint). The body is the actual prompt that gets executed.

### When a command is the right tool

- The user **explicitly invokes** a repeatable workflow they don't want to re-type.
- The prompt is **short-to-medium and single-turn** (or runs through the normal agentic loop — no need for isolated context).
- Different team members should get the **same** behavior when they type `/review`.

---

## 6. Skills — `.claude/skills/<name>/SKILL.md`

Skills are **multi-step capabilities**, often with their own scoped toolset and (optionally) an isolated context. Unlike a command — which is essentially a saved prompt — a skill is a mini-agent definition.

### Anatomy

```
.claude/skills/
  pr-summary/
    SKILL.md         # required, the skill entry point
    templates/       # optional supporting files
      summary.md
```

### `SKILL.md` frontmatter

```markdown
---
description: Summarize a pull request's changes into a release-notes entry
argument-hint: "<PR number>"
allowed-tools: ["Read", "Grep", "Bash(git diff:*)", "Bash(gh pr view:*)"]
context: fork
model: claude-sonnet-4-6
---

# PR Summary

You are generating a release-notes entry for PR $ARGUMENTS.

Steps:
1. Run `gh pr view $ARGUMENTS` to get the PR metadata.
2. Run `git diff` against the PR's base branch.
3. Classify the change type (feat/fix/docs/refactor/perf/test/chore).
4. Produce a single-line summary in the repo's release-notes voice.

Return only the final release-notes entry. Do not return reasoning.
```

Frontmatter keys you must know for the exam:

| Key | Purpose |
|---|---|
| `description` | How Claude Code decides when this skill is relevant. Treat like a tool description — specific beats cute. |
| `argument-hint` | One-line hint shown in the UI describing what argument the skill expects. |
| `allowed-tools` | **Scoped** tool list the skill can use. Restricting tools is how you keep skills safe (e.g., no `Write` for a read-only summarizer; restricted Bash patterns like `Bash(git diff:*)`). |
| `context` | `default` (run in the current session's context) or `fork` (run in an isolated context — skill sees only its prompt + argument, not the session history). |
| `model` | Optional model override (e.g., cheap model for a mechanical summarization skill). |

### `context: fork` — what it actually does

When `context: fork`, Claude Code spawns a fresh, isolated session to run the skill. The skill sees its own SKILL.md + the invocation argument + its tool results — nothing else. The skill's final message comes back to the main session as a single message; the intermediate turns are invisible.

This is the **same isolation pattern as a W02 subagent**. If a skill does lots of exploratory tool calls (read 30 files, run several `grep`s, parse a diff) and returns one summary, `context: fork` keeps that exploration out of your main session's history. Without `context: fork`, every one of those intermediate turns lands in your main context and pollutes it.

**Rule of thumb:** multi-step skill with more than a couple of tool calls → `context: fork`. Short skill that needs your current conversation's context → default.

### When a skill is the right tool (vs a command, vs a rule)

| You want… | Use |
|---|---|
| Passive guidance that loads for matching files | `.claude/rules/*.md` |
| A saved prompt the user explicitly invokes with `/name` | `.claude/commands/*.md` |
| A multi-step capability, possibly with scoped tools and isolated context | `.claude/skills/<name>/SKILL.md` |
| Repo-wide conventions every request should see | root `CLAUDE.md` |
| Personal, all-projects conventions | `~/.claude/CLAUDE.md` |

### Exam distinction — rule vs command vs skill

This is a classic distractor block. Burn this in:

- **Rule** = *passive* context loader, *automatic* based on paths. User doesn't invoke anything.
- **Command** = *active* invocation (`/name`). Essentially a saved prompt with arg substitution.
- **Skill** = *active* invocation (or model-initiated via its description), but it's a **capability** — tool-scoped, possibly forked context, multi-step.

If the exam describes "every time someone edits a `.sql` file, remind the model about our migration style" — that's a **rule**. If it says "the user frequently wants a consistent PR summary" — that's a **command** or **skill** depending on whether it's a single prompt or multi-step. If it says "a multi-tool workflow that shouldn't pollute the main context" — **skill with `context: fork`**.

---

## 7. MCP servers — project vs user scope (recap from W04, applied here)

Same scope dichotomy as CLAUDE.md and commands, applied to MCP server registration:

| File | Scope | Shared via |
|---|---|---|
| `<repo>/.mcp.json` | Project | Git — team gets the same team tools |
| `~/.claude.json` | User | Not shared — your personal tools |

**Both can be active simultaneously.** A Claude Code session inside a repo gets the union: user-level MCP servers + project-level MCP servers. If both scopes define a server with the same name, the project-scoped one takes precedence inside that repo.

### `${ENV_VAR}` expansion

Both files support `${VAR_NAME}` expansion — the literal string `${GITHUB_TOKEN}` is replaced with the value of the `GITHUB_TOKEN` environment variable at load time. This is how you keep secrets out of git while still committing `.mcp.json`.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

If `GITHUB_TOKEN` is unset, the server fails to start. Don't write literal secrets into `.mcp.json` — commit the template with `${...}`, document the env vars, let each developer set their own.

---

## 8. Worked scope-resolution scenarios

### Scenario A — Editing `src/components/Button.test.tsx`

Claude Code loads (in this order, roughly):
1. `~/.claude/CLAUDE.md` (your user-level prefs)
2. `<repo>/CLAUDE.md` (team conventions)
3. `<repo>/src/CLAUDE.md`, if it exists
4. `<repo>/src/components/CLAUDE.md`, if it exists
5. Any `.claude/rules/*.md` whose `paths:` glob matches `src/components/Button.test.tsx` — e.g., a testing rule with `paths: ["**/*.test.tsx"]` fires here.

All of the above get concatenated (with the later/more-specific files winning on conflict).

Commands and skills are **not** loaded into the prompt by default — they're registered and made available for invocation. Their definitions don't cost tokens unless invoked.

### Scenario B — Running `/review` inside the repo

Claude Code resolves the name `review`:
1. Looks in `<repo>/.claude/commands/review.md` → found, use it.
2. (If not found there, falls back to `~/.claude/commands/review.md`.)

The command's body becomes a user message in the current session.

### Scenario C — Running `/standup` inside the same repo

No `<repo>/.claude/commands/standup.md` exists, so:
1. Falls back to `~/.claude/commands/standup.md` → found, use it.

User scope fills the gap when project scope doesn't define a command.

### Scenario D — Invoking a `context: fork` skill while editing a migration

1. Current session had `.claude/rules/migrations.md` loaded (path match).
2. User invokes `/pr-summary 142`.
3. Claude Code forks a fresh session with only the skill's SKILL.md + the argument `142` + the skill's `allowed-tools`.
4. The forked session does not see the migrations rule, the main CLAUDE.md chain, or any prior turns.
5. Forked session finishes; its final message returns as the skill's output.

This is the whole point of `context: fork`: isolation at invocation time.

---

## 9. Anti-patterns (these ARE the exam distractors)

| Wrong pattern | Why it's wrong | Correct approach |
|---|---|---|
| Put every rule in root `CLAUDE.md` | Bloats every turn with irrelevant content; attention degrades | Move path-specific rules to `.claude/rules/*.md` with `paths:` |
| Rule file with no `paths:` frontmatter | Loads globally — same cost as putting it in root CLAUDE.md, but harder to find | Add `paths:`, or move to root CLAUDE.md if it truly is global |
| Use a rule for a one-shot user action ("/review the PR") | Rules are passive; user can't "invoke" a rule | That's a **command** (`.claude/commands/review.md`) |
| Use a command for a multi-step tool-scoped capability | Commands are saved prompts; they run in the current session, don't scope tools | That's a **skill** with `allowed-tools` |
| Skill doing heavy exploration without `context: fork` | Every intermediate turn pollutes the main session's history | Set `context: fork` on SKILL.md |
| Put team-wide config in `~/.claude/CLAUDE.md` | User scope isn't shared; the team won't get it | Put in project `CLAUDE.md` or `.claude/CLAUDE.md`, commit to git |
| Put personal prefs in project `CLAUDE.md` | They'll affect teammates | Put in `~/.claude/CLAUDE.md` |
| Hardcode secrets in `.mcp.json` | Leaks via git | Use `${ENV_VAR}` expansion |
| "Add instructions to CLAUDE.md that the skill should always fork" | Prompt guidance can't create isolation — isolation is a runtime mechanism | Set `context: fork` in SKILL.md frontmatter |
| `@import` used to "save tokens" | `@import` inlines content at load time; tokens are identical | Use rules with `paths:` if you want conditional loading |
| Two rules both set `paths: ["**"]` | That's two global rules; nothing is path-scoped | If they're truly global, merge into one file; if not, narrow the globs |

The fourth and fifth rows are the classic **rule vs command vs skill** distinction — expect at least one exam question on this.

---

## 10. Plan-mode and CI/CD preview (these live in W06)

Not deep in this week's scope, but you should know they exist:

- **Plan mode** — Claude Code proposes a plan before taking destructive actions. Configurable default. Covered in W06.
- **CI/CD / headless mode** — `-p` / `--print`, `--output-format json`, `--json-schema`. Session context isolation matters here (don't let the same session that generated code also review it — self-review retains bias). Covered in W06.

If the exam mixes a W05 config question with a W06 plan-mode or CI question, use the scope/merge mental model from this reference as the foundation, then apply W06 specifics.

---

## 11. What this week's exam questions will probe

Based on the exam guide task statements 3.1–3.3, expect questions that:

- Describe a config problem ("this rule loads on every turn, even when irrelevant") and ask for the correct mechanism.
- Give two candidate locations for a piece of config and ask which scope is right.
- Present a broken skill (no `allowed-tools`, or `context: default` when it should be `fork`) and ask what to change.
- Ask you to distinguish **rule** from **command** from **skill** from **CLAUDE.md entry** given a scenario.
- Test precedence: "user CLAUDE.md says X, project CLAUDE.md says Y, which wins inside the repo?"
- Present `.mcp.json` with literal secrets vs `${ENV_VAR}` and ask for the right pattern.
- Subtle one: "team reports every developer gets different behavior from Claude Code." → some rule is in user scope that should be in project scope. Or secrets are in user config instead of env-expanded project config.

---

## 12. Fast recap

- **Three scopes:** user (`~/.claude/…`), project (`<repo>/.claude/…` or `<repo>/CLAUDE.md`), subdirectory (nested `CLAUDE.md`). More specific wins on conflict; all scopes stack.
- **CLAUDE.md** = always-on context, concatenated in order. Don't put path-specific rules in root.
- **`@import`** inlines at load time — modularity, not conditional loading.
- **`.claude/rules/*.md` with `paths:` frontmatter** = path-scoped, *automatic*, *passive* guidance.
- **`.claude/commands/*.md`** = user-invoked saved prompt. Project scope wins over user scope on name collision.
- **`.claude/skills/<name>/SKILL.md`** = multi-step capability, with `description` / `argument-hint` / `allowed-tools` / `context` / optional `model`. Use `context: fork` for multi-step work to avoid polluting the main session.
- **Rule vs command vs skill:** passive-by-path vs active-invoked-prompt vs active-capability-with-scoped-tools.
- **MCP at both scopes simultaneously** (`.mcp.json` + `~/.claude.json`); `${ENV_VAR}` expansion keeps secrets out of git.
- **Deterministic mechanism beats prompt instruction** (theme continues from W01–W04): `context: fork` is runtime isolation, not something you can ask for in a CLAUDE.md bullet.

When you can explain each of those eight bullets out loud in ~20 seconds, you're ready for the W05 test.
