# W05 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** CLAUDE.md hierarchy and merge semantics, `@import`, `.claude/rules/` path-scoped rules, slash commands, Skills, `/memory`.

---

## Talk 1 — "Best practices for CLAUDE.md"

- **Three scopes, merged in a well-defined order:**
  1. **User-scope** `~/.claude/CLAUDE.md` — your personal preferences. Loaded first.
  2. **Project-scope** `.claude/CLAUDE.md` **or** root `CLAUDE.md` in the repo — team conventions. Committed.
  3. **Subdirectory-scope** `CLAUDE.md` inside a subfolder — scoped to when Claude Code is working in that subtree.
- **Merge semantics:** all three are loaded into context, in order, with later content appended. Nothing overrides by file — the model sees the concatenation. If you want a project rule to "win" over a user rule, state it explicitly in the project CLAUDE.md ("In this repo, override user preference X with Y").
- **`/memory` is your diagnostic.** Runs inside Claude Code, prints which CLAUDE.md files loaded, in what order. First stop when "why isn't Claude following my rule?" comes up.
- **`@import`** pulls in another file verbatim. Syntax: `@.claude/rules/testing.md`. Use it to modularize a big CLAUDE.md — one file per concern (testing, style, api-docs) — rather than one 500-line file.

---

## Talk 2 — Rules with `paths:` frontmatter (conditional loading)

- **`.claude/rules/*.md`** is the mechanism for rules that should only apply to specific files.
- **Frontmatter gates loading:**
  ```yaml
  ---
  paths: ["**/*.test.tsx", "**/*.spec.ts"]
  ---
  ```
  The rule file is only loaded when Claude Code is working on a path matching one of the globs. Perfect for "use Vitest, not Jest, in test files" without adding it to the global CLAUDE.md.
- **Distractor alert:** "Put testing conventions in the main CLAUDE.md so Claude always remembers them" — not wrong but wasteful. Scope them.
- **Glob gotchas:** `**/*.test.*` matches all test files; `src/**/*.ts` matches TypeScript under src. Patterns are relative to the repo root.

---

## Talk 3 — Slash commands vs Skills

- **Slash commands (`.claude/commands/<name>.md`)** are saved prompts. Invoked as `/name`. Read once, dropped into the conversation as if the user had typed the prompt body. No tool restriction, no multi-step choreography.
- **Skills (`.claude/skills/<name>/SKILL.md`)** are multi-step capabilities. Frontmatter fields:
  - `description:` — what this skill is for (the model's selection signal).
  - `allowed-tools:` — restrict the skill to a specific tool set. Prevents it from running unrelated tools even if available.
  - `argument-hint:` — one-line hint for users about what arguments the skill expects.
  - `context: fork` — run the skill in a *forked session* so its work doesn't pollute the main conversation.
- **When to use which:**
  - Single-prompt shortcut → slash command.
  - Multi-step procedure with restricted tools → skill.
  - Needs an isolated session → skill with `context: fork`.
- **Scope symmetry with commands:** `~/.claude/commands/` and `~/.claude/skills/` for user-level; `.claude/commands/` and `.claude/skills/` for project-level.

---

## Talk 4 — Scope resolution, worked

Scenario: user `~/.claude/CLAUDE.md` says "use tabs"; project `CLAUDE.md` says "use 2-space indent"; subdirectory `src/legacy/CLAUDE.md` says "preserve existing indentation". You're editing `src/legacy/old.ts`.

- All three files load. The model sees the concatenation.
- Legacy rule is most specific → it wins by recency (it's loaded last) and by explicit specificity.
- **Exam takeaway:** subdirectory rules override project rules override user rules, but *only because later content is appended after earlier*. State the override explicitly in the narrowest scope; don't assume silent overriding.

---

## Optional external viewing

- Search — Claude.md best practices: https://www.youtube.com/results?search_query=claude+code+claude.md+best+practices
- Search — Claude Code skills: https://www.youtube.com/results?search_query=claude+code+skills+tutorial
- Search — Claude Code slash commands: https://www.youtube.com/results?search_query=claude+code+slash+commands
