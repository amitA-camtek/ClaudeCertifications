# W05 Study Day — Claude Code Configuration (Domain 3.1–3.3)

## The one thing to internalize

**Every piece of Claude Code config has a *scope* (user / project / subdirectory) and a *trigger* (always on / path-scoped / user-invoked). Pick the wrong scope or the wrong trigger and the question is wrong.**

- Always-on, repo-wide → `<repo>/CLAUDE.md`.
- Always-on, personal, all projects → `~/.claude/CLAUDE.md`.
- Loads only when editing matching files → `.claude/rules/*.md` with `paths:` frontmatter.
- User types `/name` → `.claude/commands/<name>.md` (project) or `~/.claude/commands/<name>.md` (user).
- Multi-step capability, scoped tools, maybe isolated context → `.claude/skills/<name>/SKILL.md` with `allowed-tools` and `context: fork`.

The entire domain is "match the requirement to the right mechanism and the right scope."

## Precedence in one line

**More specific scope wins on conflict.** Subdirectory CLAUDE.md > project CLAUDE.md > user CLAUDE.md. Project command > user command. Project MCP server > user MCP server (same name).

All scopes still *stack* — more-specific doesn't erase less-specific; it overrides where they disagree.

## Rule vs command vs skill — the classic distractor

| Scenario | Right mechanism |
|---|---|
| "Remind the model about testing conventions whenever it edits a test file" | **Rule** — `.claude/rules/testing.md` with `paths: ["**/*.test.ts"]` |
| "Let the team run `/review` to get a consistent code review prompt" | **Command** — `.claude/commands/review.md` |
| "Summarize a PR by running several git/gh commands and returning one line, without cluttering the main session" | **Skill** — `.claude/skills/pr-summary/SKILL.md` with `allowed-tools` and `context: fork` |
| "Tell the model our tech stack and directory layout" | **Root `CLAUDE.md`** — always-on repo context |
| "Personal shortcut for running daily standup notes on your own machine" | **User command** — `~/.claude/commands/standup.md` |

If the distractor says "put the testing convention in root CLAUDE.md" — wrong (bloats every turn). If it says "use a rule to let the user trigger a workflow" — wrong (rules are passive, not invocable). If it says "use a command for a multi-step tool-scoped capability" — wrong (commands don't scope tools or isolate context).

## Anti-patterns that appear as distractors

| Wrong answer | Why it's wrong |
|---|---|
| "Put path-specific rules in root CLAUDE.md" | Loaded on every turn; attention degrades. Use `.claude/rules/*.md` with `paths:`. |
| "Rule file without `paths:` frontmatter" | Loads globally — defeats the whole point of the rules directory. Either add `paths:` or move to root CLAUDE.md. |
| "Use `@import` to save tokens" | `@import` inlines at load time. Tokens are identical. Use rules with `paths:` for conditional loading. |
| "Skill doing multi-step tool-heavy work without `context: fork`" | Pollutes main session with intermediate turns. Use `context: fork`. |
| "Hardcode GitHub token in `.mcp.json` and commit" | Leaks via git. Use `${GITHUB_TOKEN}` env expansion. |
| "Put team-wide rules in `~/.claude/CLAUDE.md`" | User scope isn't shared. Teammates won't get it. |
| "Instructions in CLAUDE.md telling the model to 'use an isolated context'" | Isolation is a runtime mechanism (`context: fork`). Prompt text can't create it. |

Last row echoes W01/W02/W03/W04: **deterministic mechanism beats prompt instruction**. Same trap, different domain.

## Skill SKILL.md frontmatter — memorize the keys

```markdown
---
description: ...            # how the model/user picks this skill
argument-hint: "..."        # UI hint for the argument
allowed-tools: [...]        # scoped tool list — safety + focus
context: fork               # or default; fork = isolated session
model: claude-sonnet-4-6    # optional override
---
```

Know each key and what it controls. `allowed-tools` can use patterns like `"Bash(git diff:*)"` to allow specific commands only.

## MCP at two scopes

- `<repo>/.mcp.json` — team MCP servers, in git.
- `~/.claude.json` — personal MCP servers, your machine only.
- Both coexist in any session. Project wins on name collision.
- `${ENV_VAR}` expansion in both, for secrets.

## 3-bullet recap

- **Scope first, trigger second.** User / project / subdirectory × always-on / path-scoped / invoked. Every config file is one cell of that grid.
- **Rule = passive-by-path; command = user-invoked prompt; skill = multi-step capability with optional fork.** Don't mix them up.
- **Deterministic mechanism beats prompt instruction.** `context: fork`, `paths:` globs, `${ENV_VAR}` expansion, `allowed-tools` — all runtime mechanisms, none expressible as "please do X" in a CLAUDE.md bullet.
