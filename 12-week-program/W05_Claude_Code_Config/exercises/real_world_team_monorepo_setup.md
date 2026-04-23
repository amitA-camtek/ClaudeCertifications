# Real-world — team monorepo config (rules + commands + skill + MCP)

A fully specified `acme-core` monorepo configuration showing all W05 mechanisms working together: CLAUDE.md hierarchy, path-scoped rules, project + user slash commands, a skill with `context: fork`, and MCP servers at both scopes simultaneously.

Read the file listings in order, then the "what loads when" scenarios at the end. Walkthrough commentary lives in `real_world_team_monorepo_setup_walkthrough.md`.

## Directory layout

```
~/.claude/
  CLAUDE.md
  commands/
    standup.md
  .claude.json                 # user MCP servers

<repo-root>/acme-core/
  CLAUDE.md                    # team conventions
  .mcp.json                    # project MCP servers
  .claude/
    rules/
      testing.md               # paths: ["**/*.test.ts", "**/*.test.tsx"]
      migrations.md            # paths: ["db/migrations/**/*.sql"]
    commands/
      review.md                # project slash command
    skills/
      pr-summary/
        SKILL.md               # context: fork
  src/
    backend/
      server.ts
    frontend/
      components/
        Button.tsx
        Button.test.tsx
    db/
      migrations/
        0042_add_users_email_index.sql
```

---

## File 1 — `<repo>/CLAUDE.md` (team conventions)

```markdown
# Acme Monorepo — team conventions

Node 20 + pnpm workspaces + TypeScript strict mode. Backend is Fastify; frontend is React 18.

## Layout

- `src/backend/`     Fastify API
- `src/frontend/`    React SPA
- `src/shared/`      shared types + utils
- `db/migrations/`   SQL migrations (numeric prefix)

## Conventions

- 4-space indentation across the repo.
- PRs require one approving review + passing CI.
- No direct commits to `main`.
- Commit messages: Conventional Commits (`feat:`, `fix:`, `chore:`, etc.).

## What NOT to put here

Anything file-specific (testing rules, migration rules, component patterns) belongs in
`.claude/rules/*.md` with `paths:` frontmatter, not this file. Keep this file general.
```

Notes:
- Describes repo-wide facts every request benefits from knowing.
- Deliberately does *not* include testing conventions or migration conventions — those live in the path-scoped rules below.

---

## File 2 — `<repo>/.claude/rules/testing.md`

```markdown
---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
description: Testing conventions for all *.test.ts and *.test.tsx files
---

# Testing conventions

- Use **Vitest**. Import from `"vitest"`, not `"@jest/globals"`.
- Every test file has exactly one top-level `describe(...)` block named after the module under test.
- Use `it(...)` (not `test(...)`) for individual cases.
- Snapshot files live under `__snapshots__/`. Do not inline snapshots.
- Use `@testing-library/react` for component tests; never render React trees with `renderer.create`.
- Prefer `expect(fn).toHaveBeenCalledWith(...)` over comparing `.mock.calls` arrays manually.

## Naming

- A test case name reads as a full sentence after "it": `it("returns null when the user is not found")`.
```

This rule loads **only** when at least one file Claude Code is operating on matches `**/*.test.ts` or `**/*.test.tsx`. Editing `src/frontend/components/Button.tsx` alone does NOT load this rule.

---

## File 3 — `<repo>/.claude/rules/migrations.md`

```markdown
---
paths:
  - "db/migrations/**/*.sql"
description: SQL migration conventions
---

# Migration conventions

- Migrations are **forward-only**. Do not edit an existing migration; add a new one.
- File naming: `NNNN_description.sql` where `NNNN` is a zero-padded sequential number.
- Every migration must be idempotent-safe (guard `CREATE INDEX` with `IF NOT EXISTS`, etc.).
- Wrap schema changes in a transaction (`BEGIN; ... COMMIT;`) unless the statement cannot run inside one (e.g., `CREATE INDEX CONCURRENTLY` in Postgres).
- Large-table operations must use concurrent variants and avoid `ACCESS EXCLUSIVE` locks.
- Every migration needs a one-line comment at the top describing the business intent.
```

This rule loads **only** when Claude Code is operating on a file under `db/migrations/` with extension `.sql`.

---

## File 4 — `<repo>/.claude/commands/review.md` (project slash command)

```markdown
---
description: Review the currently staged changes for bugs, style, and rule compliance
argument-hint: "[optional PR number]"
---

Review the currently staged changes. Produce a structured review with:

1. **Bugs** — logic errors, off-by-one, null dereferences, missing error handling.
2. **Style** — violations of conventions declared in this repo's `CLAUDE.md` and any active rules under `.claude/rules/`.
3. **Test coverage** — are the behavior changes covered by tests? If not, list the gaps.
4. **Blockers** — anything that should block merge.

If $ARGUMENTS is non-empty, treat it as a GitHub PR number, fetch the PR description with `gh pr view $ARGUMENTS`, and include the PR context in your review.

End with one of: `LGTM`, `LGTM with comments`, `Needs changes`, or `Blocked`.
```

Project scope. Checked into git. Every team member typing `/review` in this repo gets this exact prompt.

---

## File 5 — `~/.claude/commands/standup.md` (user slash command)

```markdown
---
description: Summarize what I worked on since my last standup (personal)
argument-hint: "[days back, default 1]"
---

I need a standup summary. Look at:

1. Git commits I authored in the last $ARGUMENTS days (default: 1). Run `git log --author="$(git config user.email)" --since="$ARGUMENTS days ago" --oneline`.
2. Currently open PRs authored by me: `gh pr list --author @me --state open`.
3. Any TODOs I added or resolved in that window.

Produce a 3-section standup note: **Yesterday / Today / Blockers**. Keep it under 10 bullet points total. Informal voice is fine — this is for my own daily standup.
```

User scope — lives in my home directory, not in any repo. Available in every project I open. The team does not get this; it is personal.

---

## File 6 — `<repo>/.claude/skills/pr-summary/SKILL.md`

```markdown
---
description: Generate a release-notes entry summarizing a pull request's changes
argument-hint: "<PR number>"
allowed-tools:
  - "Read"
  - "Grep"
  - "Bash(git diff:*)"
  - "Bash(git log:*)"
  - "Bash(gh pr view:*)"
context: fork
model: claude-sonnet-4-6
---

# PR Summary skill

You are producing a single release-notes entry for PR #$ARGUMENTS.

## Steps

1. Run `gh pr view $ARGUMENTS --json title,body,baseRefName,headRefName,author` to get PR metadata.
2. Run `git diff origin/<baseRefName>...origin/<headRefName>` to see the actual changes.
3. Classify the change: one of `feat`, `fix`, `docs`, `refactor`, `perf`, `test`, `chore`.
4. Produce a release-notes entry in this exact format:
   `- <type>(<scope>): <imperative summary> (#<PR number>)`
5. Return ONLY that single line. No preamble, no reasoning, no explanation.

## Scope guidance

- If the diff touches `src/backend/` only → scope is `backend`.
- If `src/frontend/` only → `frontend`.
- If `db/migrations/` → `db`.
- If `src/shared/` → `shared`.
- If mixed → pick the dominant area; if truly repo-wide → omit the scope.
```

Frontmatter highlights:
- `allowed-tools`: scoped. No `Write`, no `Edit`. The skill cannot modify files. `Bash(git diff:*)` means "allow `git diff` with any arguments" — other `Bash` commands are NOT allowed.
- `context: fork`: the skill runs in an isolated session. Its tool calls and intermediate reasoning do not enter the main session's history. Only the final one-liner comes back.
- `argument-hint`: UI hint that the skill takes a PR number.
- `model`: pinned to Sonnet for cost/latency — this is a mechanical summarization task, no need for the biggest model.

---

## File 7 — `<repo>/.mcp.json` (project MCP servers)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "acme-jira": {
      "command": "node",
      "args": ["./tools/mcp/jira-server.js"],
      "env": {
        "JIRA_BASE_URL": "https://acme.atlassian.net",
        "JIRA_API_TOKEN": "${JIRA_API_TOKEN}",
        "JIRA_USER_EMAIL": "${JIRA_USER_EMAIL}"
      }
    }
  }
}
```

Team-shared MCP servers:
- `github` — for PR and issue queries (used by `/review` and the `pr-summary` skill).
- `acme-jira` — internal Jira MCP server.

Secrets are **not** hardcoded. `${GITHUB_TOKEN}`, `${JIRA_API_TOKEN}`, `${JIRA_USER_EMAIL}` are read from the developer's environment at load time. This file is safe to commit to git.

---

## File 8 — `~/.claude.json` (user MCP servers)

```json
{
  "mcpServers": {
    "personal-notes": {
      "command": "npx",
      "args": ["-y", "@example/obsidian-mcp"],
      "env": {
        "OBSIDIAN_VAULT_PATH": "/Users/amita/notes"
      }
    },
    "scratchpad": {
      "command": "node",
      "args": ["/Users/amita/.tools/scratchpad-mcp/server.js"]
    }
  }
}
```

User scope — personal productivity MCP servers. Not shared with the team. Live alongside the project's MCP servers simultaneously.

---

## Scenario resolution — what loads when

### Scenario 1 — Editing `src/db/migrations/0042_add_users_email_index.sql`

CLAUDE.md chain loaded:
1. `~/.claude/CLAUDE.md` (user)
2. `<repo>/CLAUDE.md` (project root)
3. No subdirectory CLAUDE.md under `src/db/migrations/` in this setup → nothing additional.

Rules loaded:
- `.claude/rules/migrations.md` — `paths: ["db/migrations/**/*.sql"]` matches. **Loads.**
- `.claude/rules/testing.md` — `paths: ["**/*.test.ts", "**/*.test.tsx"]` does NOT match (this is a `.sql` file). **Does not load.**

Commands available but not in prompt: `/review` (project), `/standup` (user).
Skills available but not in prompt: `pr-summary`.
MCP servers active: `github`, `acme-jira`, `personal-notes`, `scratchpad` (project + user, union).

Net: the model sees project CLAUDE.md + user CLAUDE.md + migrations rule. It knows the repo is forward-only migrations and that this specific migration needs a transaction, idempotency, and concurrent indexes where applicable.

### Scenario 2 — Editing `src/frontend/components/Button.test.tsx`

CLAUDE.md chain:
1. `~/.claude/CLAUDE.md`
2. `<repo>/CLAUDE.md`
3. (No `src/CLAUDE.md` in this setup.)
4. (No `src/frontend/CLAUDE.md` in *this* exercise — we kept it minimal here.)

Rules loaded:
- `.claude/rules/testing.md` — `paths: ["**/*.test.ts", "**/*.test.tsx"]` matches `Button.test.tsx`. **Loads.**
- `.claude/rules/migrations.md` — does not match. **Does not load.**

The testing rule brings in Vitest conventions, describe/it structure, snapshot rules, etc. — exactly when relevant, and only then.

### Scenario 3 — User types `/review` inside the repo

Resolution order:
1. Look in `<repo>/.claude/commands/review.md` → **found**. Use it.

User-scope `~/.claude/commands/review.md` is not consulted (it doesn't exist here anyway, but even if it did, the project command would win inside this repo).

### Scenario 4 — User types `/standup` inside the repo

Resolution order:
1. Look in `<repo>/.claude/commands/standup.md` → **not found**.
2. Fall back to `~/.claude/commands/standup.md` → **found**. Use it.

User scope fills the gap. The teammates don't have this command — if teammate X types `/standup` inside the same repo, they'd either get their own user-level standup command or "no such command."

### Scenario 5 — User invokes `/pr-summary 142`

Claude Code sees that `pr-summary` is a skill (not a command) and that its frontmatter declares `context: fork`. It:
1. Forks a fresh, isolated session.
2. Passes into that session: the skill's SKILL.md body + argument `142` + the `allowed-tools` whitelist.
3. The forked session does NOT see the main session's CLAUDE.md chain, rules, or prior turns. It only sees what was explicitly handed in.
4. The forked session makes a handful of `git` / `gh` / `Read` / `Grep` calls (all whitelisted).
5. It produces the one-line release-notes entry and exits.
6. That one line comes back to the main session as the skill's result. The intermediate tool calls and reasoning never enter the main context.

This is why `context: fork` matters for this skill: without it, every `git diff` output (potentially thousands of lines) would end up in the main session's history.

---

## What this exercise demonstrates — mapped to exam concepts

| Element | W05 concept exercised |
|---|---|
| Root CLAUDE.md with tech stack + layout, deliberately excluding file-specific rules | Correct use of root scope |
| `.claude/rules/testing.md` with `paths` frontmatter | Path-scoped passive guidance |
| `.claude/rules/migrations.md` with a narrower glob | Multiple independent rule files, each scoped |
| `.claude/commands/review.md` (project) | Project slash command, shared via git |
| `~/.claude/commands/standup.md` (user) | User slash command, personal, all projects |
| `/review` resolved from project scope; `/standup` falls through to user | Project > user precedence for commands |
| `SKILL.md` with `description`, `argument-hint`, `allowed-tools`, `context: fork`, `model` | All five frontmatter keys you need for the exam |
| `allowed-tools: ["Bash(git diff:*)", …]` | Scoped Bash allow-list pattern |
| `context: fork` for a multi-step tool-heavy skill | Isolation — preventing main-session context pollution |
| `.mcp.json` with `${GITHUB_TOKEN}` expansion | Secrets via env vars, not literals |
| `.mcp.json` + `~/.claude.json` both active | Project and user MCP coexistence |
| Editing a migration loads only `migrations.md`, not `testing.md` | Rules fire only on path match |

## Common mistakes this exercise helps you recognize

- Putting the Vitest conventions in root CLAUDE.md — wrong; they'd be noise when editing backend server code. Use the path-scoped rule.
- Making `/review` a rule — wrong; rules aren't invokable. User wants to trigger it on demand → command.
- Making `pr-summary` a command instead of a skill — wrong; multi-step tool-scoped capability with isolation needs a skill.
- Hardcoding `GITHUB_TOKEN` in `.mcp.json` — wrong; use `${GITHUB_TOKEN}` expansion.
- Putting `standup.md` in `<repo>/.claude/commands/` — wrong; teammates don't want it, and it's personal. Use `~/.claude/commands/`.
- Omitting `context: fork` from `pr-summary` — wrong; the skill does heavy tool-call exploration that would flood the main session.
