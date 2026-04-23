# W11 Exercise 2 — Claude Code Team Workflow Configuration

Integrates:

- **W05** — CLAUDE.md hierarchy, path-scoped `.claude/rules/*.md`, slash commands in `.claude/commands/`, skills in `.claude/skills/` with `context: fork` and `allowed-tools`.
- **W04** — MCP server config: team-scoped `.mcp.json` (committed) vs personal `~/.claude.json` (not committed).
- **W06** — plan mode vs direct execution; when each pays off.

This is a simulated team repo. Every file's full content is inline below. If you wanted to, you could copy this tree into a real folder and Claude Code would load it exactly as specified.

---

## 1. The repo layout

```
billing-service/
  CLAUDE.md                          # project root conventions
  .claude/
    CLAUDE.md                        # (alt location, same semantics as root)
    rules/
      tests.md                       # path-scoped to **/*.test.ts
      migrations.md                  # path-scoped to **/migrations/*.sql
    commands/
      review.md                      # project slash command
    skills/
      schema-audit/
        SKILL.md                     # skill with context: fork + allowed-tools
    settings.json                    # (hooks etc. — not in scope for this exercise)
  .mcp.json                          # team MCP servers (checked into git)
  src/
    billing/
      CLAUDE.md                      # subdirectory scope — tighter rules
      charge.ts
  migrations/
    0007_add_invoice_table.sql
  tests/
    charge.test.ts

~/.claude/
  CLAUDE.md                          # user-level personal preferences
  commands/                          # (user slash commands, not shown)
  .claude.json                       # personal MCP servers (NOT committed)
```

Claude Code walks from cwd upward, collects every CLAUDE.md, then layers the user-level file on top. Rules, commands, and skills are loaded from both `~/.claude/…` and `<repo>/.claude/…`. Subdirectory CLAUDE.md files activate only when the cwd is inside that subtree.

---

## 2. `billing-service/CLAUDE.md` — project root

```markdown
# Billing Service

TypeScript Node 20. Postgres 15. Deployed to GCP Cloud Run.

## Stack conventions

- Package manager: pnpm
- Test framework: Vitest (not Jest)
- Lint/format: Biome
- All monetary amounts are integers in minor units (cents). Never floats.
- Timestamps are `Date` objects in UTC. Serialize as ISO strings at API boundaries.

## Directory layout

- `src/billing/` — core billing domain (charges, invoices, refunds)
- `src/api/` — HTTP handlers; thin wrappers, no business logic
- `migrations/` — numbered SQL files, forward-only
- `tests/` — Vitest specs co-located by feature

## Conventions

- Prefer named exports. Default exports only for route handlers.
- Runtime validation at every external boundary with Zod.
- Do NOT add a new npm dependency without opening a discussion in #billing first.
- Before merging: `pnpm typecheck && pnpm test && pnpm biome check`.
```

---

## 3. `.claude/rules/tests.md` — path-scoped rule (tests only)

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.spec.ts"
---

# Test conventions

- Use Vitest's `describe` / `it` / `expect`. Never `test()`.
- Every `it` block tests exactly one behavior. If the description contains "and", split it.
- Use `vi.useFakeTimers()` for any test that depends on `Date.now()`.
- Factory helpers live in `tests/factories/`. Do NOT inline test data that other tests could share.
- Async assertions: prefer `await expect(fn()).rejects.toThrow(X)` over try/catch.
```

**Why path-scoped:** this rule is useless (and noisy) when Claude is editing `src/billing/charge.ts`. The `paths:` frontmatter means it only enters the system prompt when Claude is touching a test file. **Deterministic gating, not a prompt plea.** If you drop the frontmatter and put "only apply to test files" in the rule text, Claude will sometimes apply it to production code — the exam answer prefers the frontmatter.

---

## 4. `.claude/rules/migrations.md` — path-scoped rule (SQL migrations)

```markdown
---
paths:
  - "migrations/*.sql"
---

# Migration conventions

- Forward-only. No `DROP COLUMN` or `DROP TABLE` in the same migration as a deploy.
- Every migration must be reversible via a new forward migration, not by editing this one.
- Name files `NNNN_short_description.sql`. N is zero-padded, monotonically increasing.
- Wrap destructive changes in a `BEGIN; … COMMIT;` transaction.
- Add a NOT NULL column in TWO steps: add-nullable + backfill, then a later migration for NOT NULL.
- Never use `SELECT *` inside a migration.
```

Same pattern: frontmatter-gated, only loads for `migrations/*.sql`. Two rules coexist in `.claude/rules/` without interfering because their globs don't overlap.

---

## 5. `src/billing/CLAUDE.md` — subdirectory scope

```markdown
# Billing domain (subdirectory scope)

Everything in `src/billing/` handles money. Stricter rules than the rest of the repo.

- Never catch errors from `charge.ts` without re-throwing a domain-typed error.
- No `console.log` in this directory — use the structured logger from `src/lib/log.ts`.
- All exported functions must have an explicit return type annotation.
- Any math on amounts goes through `src/billing/money.ts` helpers (never `a + b` on raw numbers).
```

This loads **only** when Claude Code is working inside `src/billing/` (or below). Outside that subtree, the stricter rules don't apply. **More specific scope overrides less specific.** If the root CLAUDE.md says "prefer explicit return types on exports," the subdir CLAUDE.md can make it mandatory; both stack, with the subdir version being stricter in its scope.

---

## 6. `.claude/commands/review.md` — project slash command

```markdown
---
description: Review the pending changes on this branch for billing-service standards
argument-hint: "[optional specific file path]"
---

# Review pending changes

You are reviewing the diff on the current branch against `main`.

Steps:
1. Run `git diff main...HEAD` (read only).
2. For each changed file, check:
   - Does it follow the rules in CLAUDE.md and any applicable `.claude/rules/*.md`?
   - Are monetary amounts integers in minor units?
   - Are external-boundary inputs Zod-validated?
   - Is there test coverage for the change?
3. Produce a terse review grouped by severity: blocker / suggest / nit.
4. Do NOT modify any files. Read-only.

If $ARGUMENTS is provided, scope the review to that path only.
```

Slash commands are **parameterized prompts**. The user types `/review` (or `/review src/billing/charge.ts`) and this file's body gets sent as the prompt. The model runs the normal agentic loop with the repo's full tool set. Not isolated. Not forked.

---

## 7. `.claude/skills/schema-audit/SKILL.md` — skill with `context: fork` + `allowed-tools`

```markdown
---
name: schema-audit
description: Audit Postgres schema against the Zod models; list drift. Read-only.
context: fork
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(psql:*)
argument-hint: "[optional schema name]"
---

# Schema audit

Compare the live Postgres schema to the Zod models declared in `src/billing/models/`.

Procedure:
1. `Grep` for all `z.object(` usages in `src/billing/models/`.
2. Read each matched file; extract the model name and field list.
3. Run `psql -c "\d+ <table>"` for the corresponding table.
4. Report fields present in one but not the other, and type mismatches (bigint vs number, etc.).

Output format:
```
TABLE: <name>
  DB extra:   <fields>
  Zod extra:  <fields>
  Mismatches: <field: db_type vs zod_type>
```

Do NOT modify any files. This is audit-only.
```

Key points:

- **`context: fork`** — the skill runs in a forked subagent context. When it returns, the main session's context is untouched; the 40 tool calls this skill makes don't bloat your working chat. (Same principle as `fork_session` from W02/W03.)
- **`allowed-tools`** — explicitly restricts the skill to read-only tools. Even if the skill's prompt accidentally tells it to edit a file, the harness will refuse. **Deterministic enforcement.** A prompt rule like "do not modify files" would be probabilistic.
- Contrast with the slash command: command = inline prompt in the main session; skill = forked scope with tool restrictions. Use a skill when the task is heavy (many tool calls) and self-contained; use a command when it's a light directive you want to feel like a shortcut.

---

## 8. `.mcp.json` — team MCP servers (committed)

```json
{
  "mcpServers": {
    "billing-db": {
      "command": "node",
      "args": ["./tools/mcp-billing-db/dist/server.js"],
      "env": {
        "PGHOST": "${PGHOST}",
        "PGUSER": "${PGUSER}",
        "PGPASSWORD": "${PGPASSWORD}",
        "PGDATABASE": "billing_readonly"
      }
    },
    "stripe-test": {
      "command": "node",
      "args": ["./tools/mcp-stripe-test/dist/server.js"],
      "env": {
        "STRIPE_SECRET": "${STRIPE_TEST_SECRET}"
      }
    }
  }
}
```

**What this is:** MCP servers everyone on the team needs — read-only DB access to the billing database, test-mode Stripe. Committed to git so every teammate gets them automatically after cloning.

**What it is NOT:** a place for credentials. The `${PGPASSWORD}` syntax expands from the teammate's own environment — the repo only declares the wiring, not the secrets.

---

## 9. `~/.claude/.claude.json` — personal MCP servers (NOT committed)

```json
{
  "mcpServers": {
    "linear-me": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-linear"],
      "env": {
        "LINEAR_API_KEY": "${LINEAR_API_KEY}"
      }
    },
    "my-notes": {
      "command": "node",
      "args": ["/Users/noa/code/my-notes-mcp/dist/server.js"]
    }
  }
}
```

Personal servers. Linear access and a local notes server — nobody else needs these, and nobody else would be able to run them anyway (they reference paths on this developer's machine). Personal MCP config **must** be in `~/.claude/.claude.json`, never in the repo's `.mcp.json`.

**Exam distractor pattern:** "Add the developer's Linear MCP server to `.mcp.json` so it's version-controlled." — wrong. That leaks personal credentials/paths into the team repo. User-scope config exists exactly for this.

### What Claude Code sees in a session

When Claude Code starts a session in this repo on Noa's machine, the **union** of both configs is live:

- `billing-db` (team)
- `stripe-test` (team)
- `linear-me` (personal)
- `my-notes` (personal)

On a teammate's machine, only `billing-db` and `stripe-test` are live. Exactly the intended scoping.

---

## 10. The same task, three ways — when does plan mode pay off?

Claude Code can run in two modes:

- **Direct execution** — the agent makes edits as it goes, no up-front plan.
- **Plan mode** — the agent produces a written plan first, you (human) approve/edit, then it executes the plan.

Plan mode is cheap to skip but expensive to skip *wrong*. Rule of thumb: **the cost of plan mode is one extra review turn; the benefit is bounded blast radius on large or ambiguous changes**.

### Task A — "Fix the typo in the error message on line 42 of `charge.ts`"

- **Mode:** direct execution.
- **Why:** the change is 1 line in 1 known file. Blast radius is ~zero. A plan mode turn is pure overhead; you'd spend more time reading the plan than reading the diff.
- **Wrong answer on exam:** "always use plan mode for production code." Overkill.

### Task B — "Migrate 45 call sites from the old `charge()` API to the new `chargeV2()` API"

- **Mode:** plan mode, mandatory.
- **Why:** 45 files. An ambiguous call pattern. Edge cases around optional params. Without a plan, direct execution will commit half the migration before discovering a shape Claude hadn't accounted for, and you'll be untangling mixed state. With plan mode: agent lists the 45 files, the call signature per file, the expected transformation, the tests to run after. You approve once, it executes cleanly. (If it still messes up, you caught the class of error in the plan review, not in 45 scattered diffs.)
- This is **exactly** the scenario `fork_session` can also help with — fork the session, run the migration in the fork, if it's clean merge the changes, if not throw away the fork. But the first-line tool is still plan mode.

### Task C — "Add a feature: customers can split a single payment across two cards"

- **Mode:** plan mode, strongly preferred.
- **Why:** open-ended. The *design space* is bigger than the *code change*. Plan mode forces the agent to articulate: DB schema changes? API shape? Stripe Connect vs multi-capture? Refund semantics when one of the two cards is charged back? That plan is the artifact you review — not the code. Once the plan is agreed, the code is mechanical and direct execution is fine for the execution half.
- If you skip plan mode here, the agent will pick a design on its own and you'll discover it by reading the PR. Too late.

### Summary table

| Task | Files touched | Ambiguity | Mode | Why |
|---|---|---|---|---|
| Typo fix | 1 | none | direct | Plan overhead > value |
| 45-file migration | 45 | low-medium (mechanical but edge cases) | plan | Catch class-of-errors in the plan review |
| Open-ended feature | many | high | plan | The plan IS the design review |

Put crudely: **plan mode pays off when the cost of being wrong ∗ probability of being wrong > the cost of one review turn.**

---

## 11. What this exercise tests (exam mapping)

| Sub-exercise | Task statement |
|---|---|
| Project CLAUDE.md + subdir CLAUDE.md | 3.1 — CLAUDE.md hierarchy, merge semantics |
| Two `.claude/rules/*.md` with different `paths:` | 3.2 — path-scoped rules |
| `.claude/commands/review.md` | 3.3 — slash commands |
| Skill with `context: fork` + `allowed-tools` | 3.3 — skill frontmatter; also 1.4 (deterministic tool scoping) |
| `.mcp.json` vs `~/.claude.json` | 2.4 — project vs user MCP config |
| Same task in 3 modes | 3.4 — plan mode decision |

---

## 12. Fast recap — the common exam traps in this area

| Wrong choice | Right choice |
|---|---|
| Put "only apply in test files" in the rule body | Put it in `paths:` frontmatter |
| Personal MCP server in `.mcp.json` | Personal MCP server in `~/.claude/.claude.json` |
| Skill without `allowed-tools` | Skill with an explicit `allowed-tools` list |
| Skill without `context: fork` for a heavy multi-tool audit | `context: fork` so main session stays clean |
| Plan mode for a one-line typo fix | Direct execution |
| Direct execution for a 45-file migration | Plan mode |
| One CLAUDE.md at root with conflicting directory rules jumbled together | Subdirectory CLAUDE.md where the rule is actually specific |
| Putting team CI credentials inline in `.mcp.json` | `${ENV_VAR}` expansion so secrets come from each machine's env |
