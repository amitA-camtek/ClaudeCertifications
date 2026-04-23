# Walkthrough — Real-world team monorepo config

Read this after `real_world_team_monorepo_setup.md`. For each scenario below, we trace exactly what Claude Code loads, why, and what the model sees. This is the mental model you want in place before the W05 practice test.

## The setup in one diagram

```
                  ┌────────────────────────┐
                  │     USER SCOPE          │
                  │  ~/.claude/CLAUDE.md    │
                  │  ~/.claude/commands/    │
                  │     standup.md          │
                  │  ~/.claude.json         │
                  └─────────┬──────────────┘
                            │  always in effect
                            ▼
                  ┌────────────────────────┐
                  │   PROJECT SCOPE         │
                  │  <repo>/CLAUDE.md       │
                  │  <repo>/.mcp.json       │
                  │  .claude/commands/      │
                  │     review.md           │
                  │  .claude/skills/        │
                  │     pr-summary/         │
                  │  .claude/rules/         │
                  │     testing.md  ──┐     │
                  │     migrations.md ─┤ path-scoped
                  └─────────┬──────────┴──┘
                            │  active when inside this repo
                            ▼
                  ┌────────────────────────┐
                  │ PATH-SCOPED ACTIVATION  │
                  │ rules + subdirectory    │
                  │ CLAUDE.md fire based    │
                  │ on current file(s)      │
                  └────────────────────────┘
```

Keep this picture in mind through the scenarios.

---

## Scenario 1 — Editing a test file (`src/frontend/components/Button.test.tsx`)

### What Claude Code loads into the system prompt

1. `~/.claude/CLAUDE.md` — user-level preferences (loads on every session, anywhere).
2. `<repo>/CLAUDE.md` — team conventions (loads because we're inside the repo).
3. `.claude/rules/testing.md` — matches `paths: ["**/*.test.ts", "**/*.test.tsx"]`. **Loads.**
4. `.claude/rules/migrations.md` — `paths: ["db/migrations/**/*.sql"]` does NOT match. **Does not load.**

### What is registered but NOT in the prompt

- `/review` (project) and `/standup` (user) commands — known to Claude Code, but their bodies are not in the prompt unless the user actually invokes them.
- `pr-summary` skill — same; its SKILL.md isn't in the prompt until the skill is invoked (and even then, it runs in a forked session, not the main one).
- MCP tools from `github`, `acme-jira`, `personal-notes`, `scratchpad` — registered as available tools (with their descriptions). The tool *descriptions* are in the prompt; the tool *implementations* are not.

### Why this is correct

The model needs the testing conventions because the file is a test. It does **not** need migration rules, which would be noise. This is exactly what the path-scoped rules mechanism is for: relevant context arrives at the right time, irrelevant context stays out.

### If `testing.md` had no `paths:` frontmatter

It would load globally — on every turn, in every directory. The `Button.tsx` component (non-test) would also get the Vitest conventions in its prompt. That's why **"rule with no `paths:`"** is an anti-pattern — it's no better than putting the text in root CLAUDE.md, and it's harder to find.

---

## Scenario 2 — Editing a migration (`src/db/migrations/0042_add_users_email_index.sql`)

### What Claude Code loads

1. `~/.claude/CLAUDE.md`
2. `<repo>/CLAUDE.md`
3. `.claude/rules/migrations.md` — `paths: ["db/migrations/**/*.sql"]` matches. **Loads.**
4. `.claude/rules/testing.md` — does NOT match. **Does not load.**

### What the model now knows

- General repo layout and conventions (from root CLAUDE.md).
- Migrations are forward-only, numbered, transaction-wrapped where possible, idempotent.
- Large-table operations should use concurrent variants.

If the user asks "add an index on `users.email`," the model will produce something like:

```sql
-- 0042_add_users_email_index.sql: speed up email lookup on the users table.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users (email);
```

— because the migration rule told it to use `IF NOT EXISTS`, `CONCURRENTLY`, and a header comment. None of that had to be in root CLAUDE.md.

### The cost-efficiency angle

If we had put this migration guidance in root CLAUDE.md instead, every frontend component edit, every backend refactor, every doc change would pay the token cost of rules that apply to ~1% of files. Over a long session that accumulates. Path-scoped rules are the mechanism to avoid that.

---

## Scenario 3 — Running `/review` inside the repo

### Resolution

1. Claude Code looks up the slash-command name `review`.
2. First place checked: `<repo>/.claude/commands/review.md` — **found**. Use it.
3. User-scope `~/.claude/commands/review.md` is not consulted.

### What happens

The body of `review.md` is sent as a user message in the current session. That message includes the instructions ("Produce a structured review with…"), with `$ARGUMENTS` substituted. The existing session context (CLAUDE.md chain, any rules that are loaded based on files Claude is looking at) continues to apply — `/review` runs *in* the current session, not in a forked one.

### Why project scope wins

The team wants **consistent** behavior from `/review`. If a teammate had their own `~/.claude/commands/review.md` with different instructions, the project version must still win inside this repo. Otherwise "team command" is meaningless. More specific wins — same precedence principle as CLAUDE.md.

### Exam trap

A distractor might say "the user's home directory command should take priority because it's a personal machine." Wrong — project scope is more specific than user scope for slash commands in the same repo.

---

## Scenario 4 — Running `/standup` inside the repo

### Resolution

1. Claude Code looks up `standup`.
2. First place checked: `<repo>/.claude/commands/standup.md` — **not found**.
3. Fall back to `~/.claude/commands/standup.md` — **found**. Use it.

### What happens

User-scope command body is sent as a user message. Works identically to a project command from here on.

### Why this is the right placement for standup

- Standup notes are personal. Teammates don't want the same prompt.
- The command references the author's own git identity (`git config user.email`) and their own open PRs (`--author @me`) — both inherently per-user.

Putting this in `<repo>/.claude/commands/` would be wrong: it would appear for every teammate in the repo, and its behavior (filtering by `git config user.email`) would still only work for the currently-logged-in developer, so it'd be confusing for anyone else.

---

## Scenario 5 — Running `/pr-summary 142` inside the repo

### Resolution

1. Claude Code looks up `pr-summary`. It's not a command, it's a **skill** (`.claude/skills/pr-summary/SKILL.md`).
2. SKILL.md frontmatter says `context: fork`. Claude Code forks a new session.
3. The fork gets:
   - The skill body as its system/instruction input.
   - The argument `142`.
   - The allow-list: `["Read", "Grep", "Bash(git diff:*)", "Bash(git log:*)", "Bash(gh pr view:*)"]`.
   - The MCP tools that were registered in the main session (MCP registration is session-level).
4. The forked session runs its own agentic loop until it produces the one-line release notes and emits `end_turn`.
5. That single final message comes back to the main session as the skill's output.

### What the forked session canNOT see

- The main session's prior user/assistant turns.
- The main session's CLAUDE.md chain (unless the skill author explicitly passed it in — which they didn't here).
- The `.claude/rules/*.md` files that were loaded in the main session.

### What this buys

The skill probably makes 5–10 tool calls (`gh pr view`, multiple `git diff`, a few `Read`s to check conventions). Each of those returns possibly thousands of characters of output. Without `context: fork`, all of that would accumulate in the main session's message history. With `context: fork`, only the final summary line returns.

This is the **same isolation pattern as a W02 subagent**. If you already understand hub-and-spoke, you understand `context: fork`: the main session is the coordinator, the skill's forked session is a subagent.

### Exam trap

A distractor might say "add an instruction to SKILL.md body that it should not quote tool outputs in its final answer, to keep the output small." That doesn't solve the real problem — the intermediate turns (tool calls and tool results) are in the session history regardless of the final answer. **Only `context: fork` provides runtime isolation.** Prompt instruction ≠ runtime mechanism. (Same theme from W01–W04.)

---

## Combined view — MCP at both scopes simultaneously

While all five scenarios above were running, the MCP server topology looked like this:

```
 Active MCP servers during any session in <repo>:
  ┌──────────────────────────────────────────┐
  │  FROM PROJECT ~/acme-core/.mcp.json       │
  │   • github       (${GITHUB_TOKEN})         │
  │   • acme-jira    (${JIRA_API_TOKEN})       │
  ├──────────────────────────────────────────┤
  │  FROM USER ~/.claude.json                  │
  │   • personal-notes                         │
  │   • scratchpad                             │
  └──────────────────────────────────────────┘
```

All four MCP servers are live. If a teammate without `personal-notes` or `scratchpad` runs the same session, they'd see only the two project servers — because user scope isn't shared.

**Name collision note:** if someone's user `.claude.json` defined a server also named `github`, the project `.mcp.json`'s `github` would win inside this repo. The user-level one would shadow silently — a good reason to namespace personal MCP server names (e.g., `personal-github`).

---

## Variations to try — deliberately break things and reason through

### Variation A — Conflicting user-level rule

Add to `~/.claude/CLAUDE.md`:

```markdown
- Use 2-space indentation everywhere.
```

Then edit `src/backend/server.ts`. What happens?

- User says 2-space.
- Project `CLAUDE.md` says 4-space.
- **Project wins.** The model writes 4-space.

This is how you test the "more specific scope wins" rule empirically. Put contradictory values at different scopes, observe which the model follows.

### Variation B — Swap `context: fork` for default

Change SKILL.md frontmatter:

```yaml
context: default
```

Run `/pr-summary 142`. What changes?

- The skill no longer forks. It runs in the main session.
- Every `git diff`, every `gh pr view`, every `Read` lands in the main session's message history.
- The main session's context balloons. If you subsequently ask an unrelated question in the same session, the model's attention is now distracted by all those diff lines.

This is the concrete effect of forgetting `context: fork` on a multi-step skill. Exam questions about "preventing main-session context pollution" want `context: fork` as the answer.

### Variation C — Remove `paths:` from `testing.md`

Delete the frontmatter block. Now the file loads on every turn.

Edit `src/backend/server.ts` (not a test). What changes?

- The testing rule loads anyway, even though we're not touching a test file.
- Every backend edit now also carries "use Vitest, one describe block per file, `@testing-library/react`…" — irrelevant and wasteful.

This is why "rule without `paths:`" is an anti-pattern. If the rule is truly global, it belongs in `CLAUDE.md`. If it's path-specific, give it `paths:`. A rule with no paths is the worst of both worlds: scattered across `.claude/rules/` (hard to find) AND loaded globally (costly).

### Variation D — Hardcode a secret in `.mcp.json`

Replace `"GITHUB_TOKEN": "${GITHUB_TOKEN}"` with a literal token value, then commit.

What breaks:
- Every teammate now pushes to prod with the committing developer's token.
- The token is in git history forever (scrubbing is painful).
- A public repo leaks instantly; a private repo leaks as soon as anyone clones it to a compromised machine.

The fix is always `${ENV_VAR}` expansion. Document the required env vars in the README, not in the config file.

### Variation E — Put `standup.md` in project scope

Move `~/.claude/commands/standup.md` to `<repo>/.claude/commands/standup.md` and commit.

What breaks:
- Every teammate now has `/standup` available in their clone of this repo.
- Their `/standup` uses the author's email filter (`git config user.email`) — which, for them, returns their own email, so it "works" but only by accident.
- The command is tied to one repo instead of following the author to every project.

User-scope commands follow the **user**; project-scope commands are for the **team**. Don't invert them.

### Variation F — Two rules with overlapping `paths`

Add `.claude/rules/typescript.md` with `paths: ["**/*.ts", "**/*.tsx"]`. Now editing `Button.test.tsx` matches both `testing.md` and `typescript.md`.

What happens:
- **Both rules load.** Rules aren't mutually exclusive — any rule whose paths match fires.
- Their content is concatenated into the system prompt.
- If the two rules **contradict** (e.g., testing says "use `it()`", typescript says "use `test()`"), the later/more specific one generally wins, but you should avoid that situation by splitting rules cleanly.

Multiple rules loading is normal and fine — as long as they don't contradict.

---

## Exam-critical takeaways

1. **Path-scoped rules fire on path match, not directory location.** A `db/migrations/**/*.sql` rule fires anywhere in the repo as long as the file path matches the glob.

2. **Project scope beats user scope** for CLAUDE.md conflicts, command name collisions, and MCP server name collisions — all inside the project.

3. **`context: fork` is runtime isolation** for skills. No amount of prompt engineering in SKILL.md replaces it. Multi-step tool-heavy skills without fork pollute the main session.

4. **`${ENV_VAR}` expansion in MCP config** is how you commit config to git without committing secrets. Never hardcode tokens.

5. **Four Claude Code mechanisms, four jobs:**
   - `CLAUDE.md` = always-on context, scope-graded.
   - `.claude/rules/*.md` = passive guidance, path-scoped.
   - `.claude/commands/*.md` = user-invoked saved prompt, scope-graded.
   - `.claude/skills/<name>/SKILL.md` = multi-step capability, scoped tools, optional forked context.

   Mixing them up (rule-for-a-command, command-for-a-skill) is a recurring distractor.

6. **Rules without `paths:`** and **skills without `context: fork`** are the two config files the exam will most often put in front of you and ask you to fix.
