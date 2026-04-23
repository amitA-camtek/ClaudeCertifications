# Practice Test 5 — Claude Code Configuration

**Time:** 45 min · **Pass threshold:** 7/10 · **Domain:** 3.1–3.3

## Instructions
Solve all 10 questions before opening `test5_answers.md`. Record your picks in the table at the bottom.

## Questions

### Q1. A teammate reports that Claude Code "isn't following our testing convention" in one of your repos, and behavior seems inconsistent across sessions. You want to diagnose which CLAUDE.md files are actually loaded and in what order for their active session. What is the first diagnostic to reach for?
- A. Re-clone the repo and compare `CLAUDE.md` files by hand.
- B. Run `/memory` inside Claude Code to list every loaded CLAUDE.md plus `@import`ed fragments and their merge order.
- C. Delete `~/.claude/CLAUDE.md` to eliminate user-scope interference, then retry.
- D. Put the testing convention in `.claude/commands/test-convention.md` so the user can invoke it.

### Q2. Your repo's root `CLAUDE.md` says "prefer tabs." A file at `src/frontend/CLAUDE.md` says "this folder uses 2-space indentation (Prettier config)." Your personal `~/.claude/CLAUDE.md` says "use 2-space indentation." Claude Code is editing `src/backend/server.ts`. Which indentation rule applies?
- A. 2-space, because user scope always takes precedence.
- B. 2-space, because the `src/frontend/CLAUDE.md` rule applies repo-wide once defined.
- C. Tabs, because the project root rule is more specific than the user rule, and no subdirectory CLAUDE.md matches `src/backend/`.
- D. Undefined — conflicting rules cancel each other out, so Claude Code falls back to a default.

### Q3. The team wants Claude Code to remind the model about migration conventions every time someone edits a file under `db/migrations/**/*.sql`, regardless of where in the repo the session started. The guidance should load automatically, with no user invocation. Where should this live?
- A. Root `CLAUDE.md` — put the migration rules there so they're always in the prompt.
- B. `~/.claude/CLAUDE.md` — user scope guarantees it loads for every developer.
- C. `.claude/rules/migrations.md` with `paths: ["db/migrations/**/*.sql"]` in frontmatter.
- D. `.claude/commands/migrations.md` so a developer can type `/migrations` before editing.

### Q4. A developer creates `.claude/rules/style.md` in the repo with a body of style guidance, but **no frontmatter at all**. What is the effect?
- A. The rule silently fails to load because `paths:` is required.
- B. The rule loads globally on every turn in this repo — equivalent cost to putting it in root `CLAUDE.md` but harder to find.
- C. The rule loads only when a file named `style.*` is being edited (filename inference).
- D. The rule loads only when the user invokes `/style`.

### Q5. Both `<repo>/.claude/commands/review.md` and `~/.claude/commands/review.md` exist. Inside the repo, a developer types `/review`. Which file's body is sent as the user message?
- A. `~/.claude/commands/review.md`, because user scope loads first.
- B. `<repo>/.claude/commands/review.md`, because project scope is more specific and wins inside the repo.
- C. Both — their bodies are concatenated in alphabetical order.
- D. Neither — the name collision causes Claude Code to refuse to run the command until one is renamed.

### Q6. A `pr-summary` skill reads ~30 files, runs several `grep`s, parses a large diff, and returns a single release-notes line. Today it's defined with `context: default` and the main session keeps getting polluted with dozens of intermediate tool-call turns. What is the correct fix?
- A. Add a bullet to root `CLAUDE.md` telling the model "always fork context when running pr-summary."
- B. Split the skill into 30 separate commands so each invocation is short.
- C. Set `context: fork` in the SKILL.md frontmatter so Claude Code runs the skill in an isolated session and only returns its final message.
- D. Remove `allowed-tools` so the skill can run faster and finish before polluting context.

### Q7. Your team ships a `.mcp.json` that commits the GitHub MCP server configuration so every developer gets the same tooling. Which configuration is correct?
- A. Hardcode each developer's personal access token directly under `env` and `.gitignore` the file.
- B. Use `${GITHUB_TOKEN}` expansion under `env` so each developer sets the variable locally; commit the template.
- C. Put the token in `~/.claude.json` and remove the `env` key from `.mcp.json` entirely — user scope will inject it automatically.
- D. Inline the token into the `args` array instead of `env`, because `args` is not parsed by the MCP client.

### Q8. The team frequently wants a consistent, repeatable PR review workflow. It's a short, single-turn prompt — "Review the currently staged changes for logic bugs, missing error handling, and non-compliance with `.claude/rules/`." Every team member should get the same behavior when they type one thing. Which mechanism fits best?
- A. A `.claude/rules/review.md` rule with no `paths:` frontmatter so it loads globally.
- B. A paragraph appended to root `CLAUDE.md` under a "Review guidance" heading.
- C. A `.claude/commands/review.md` project command, committed to git.
- D. A skill at `.claude/skills/review/SKILL.md` with `context: fork` and a restricted `allowed-tools` list.

### Q9. A team lead writes: *"Keep shared code-style rules in `shared/style.md`. Import them into both `CLAUDE.md` and `src/frontend/CLAUDE.md` via `@import ./.claude/shared/style.md`. This way, the imported content is only inlined conditionally, which also saves tokens."* Which part of that statement is wrong?
- A. Nothing — `@import` is designed for conditional loading and token savings.
- B. You cannot `@import` from a subdirectory CLAUDE.md, only from root.
- C. `@import` unconditionally inlines content at load time; it does not save tokens and does not load conditionally. For conditional loading you need `.claude/rules/*.md` with `paths:`.
- D. The path must be absolute (`/full/path/to/style.md`) — relative paths are not supported.

### Q10. Engineering leadership asks you to set a rule that every Claude Code session across the company gets the instruction "always prefer absolute imports." The rule should apply to every project a developer opens, not just one repo. Each developer installs Claude Code on their own machine. Where should the instruction live?
- A. Each repo's `<repo>/CLAUDE.md`, copied into every project the company owns.
- B. `~/.claude/CLAUDE.md` on each developer's machine (user scope).
- C. `<repo>/.claude/rules/imports.md` with `paths: ["**"]` in every repo.
- D. `<repo>/.claude/commands/imports.md` so developers can invoke `/imports` when they remember.

## Your answers
| Q  | Answer |
|----|--------|
| 1  |        |
| 2  |        |
| 3  |        |
| 4  |        |
| 5  |        |
| 6  |        |
| 7  |        |
| 8  |        |
| 9  |        |
| 10 |        |
