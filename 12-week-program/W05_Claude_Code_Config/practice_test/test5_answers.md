# Practice Test 5 — Answer Key & Explanations

## Quick key
| Q | Answer |
|---|--------|
| 1 | B |
| 2 | C |
| 3 | C |
| 4 | B |
| 5 | B |
| 6 | C |
| 7 | B |
| 8 | C |
| 9 | C |
| 10 | B |

## Detailed explanations

### Q1 — Answer: B

**Why B is correct:** `/memory` lists every CLAUDE.md file currently loaded for the active session — user-level, project root, inherited subdirectory files, and all `@import`ed fragments — and shows the exact merge order. §2 ("Diagnosing hierarchy issues with `/memory`") explicitly names this as the first diagnostic for "config is inconsistent across sessions."

**Why the others are wrong:**
- A. Re-cloning doesn't reveal what's actually loaded at runtime — the user's `~/.claude/CLAUDE.md` and any subdirectory files are outside the repo.
- C. Deleting user-scope config is destructive and blind; it removes information before diagnosing the problem.
- D. A command is user-invoked; it doesn't explain *why* a passive convention is already being ignored, and wouldn't diagnose the loaded set.

**Reference:** §2 of reference.md

### Q2 — Answer: C

**Why C is correct:** Per §2 precedence rules, more specific scope wins on conflict. Project root is more specific than user scope, so "prefer tabs" overrides the user-level "2-space" rule. The `src/frontend/CLAUDE.md` file only applies *inside that subtree*; editing `src/backend/server.ts` does not load it.

**Why the others are wrong:**
- A. User scope is the *least* specific; it loses to project and subdirectory scopes on conflict.
- B. A subdirectory CLAUDE.md applies only when Claude Code is working inside that subtree and its descendants — not repo-wide.
- D. Conflicts don't cancel; the more-specific rule wins, period.

**Reference:** §2 (Precedence) of reference.md

### Q3 — Answer: C

**Why C is correct:** §4 defines `.claude/rules/*.md` with `paths:` as the mechanism for **passive, path-scoped, automatic** guidance. Rules fire based on file pattern regardless of where the session started, which is exactly the requirement. §9 also lists this as the correct pattern versus "dumping everything into root CLAUDE.md."

**Why the others are wrong:**
- A. Root CLAUDE.md loads on every turn in the repo — even turns nowhere near migrations. That's the classic bloat anti-pattern (§2, §9).
- B. User scope isn't shared via git; teammates wouldn't get the guidance, and it would still load globally on their machine.
- D. A command is user-invoked; the scenario requires automatic loading whenever migrations are touched.

**Reference:** §4 and §9 of reference.md

### Q4 — Answer: B

**Why B is correct:** §4 states a rule with no `paths:` frontmatter (or no frontmatter at all) loads **globally** — almost always a mistake. §9 echoes this: it has the same cost as putting the content in root CLAUDE.md but is harder to find.

**Why the others are wrong:**
- A. The rule does load — it just loads everywhere, which is the problem.
- C. There is no filename-based inference; loading is driven by the `paths:` glob list, not the file's own name.
- D. Rules are passive, not user-invoked. Slash-command invocation comes from `.claude/commands/`.

**Reference:** §4 (Loading rules) and §9 of reference.md

### Q5 — Answer: B

**Why B is correct:** §5 ("Resolution order when names collide") states that when both a project and a user command exist with the same name, the project command wins inside that repo — same "more specific scope wins" precedence principle as CLAUDE.md.

**Why the others are wrong:**
- A. User scope is *less* specific; it loses to project scope inside the repo.
- C. Commands are not concatenated — exactly one file's body is sent as the user message.
- D. Name collisions are resolved by precedence, not by refusal.

**Reference:** §5 (Resolution order when names collide) of reference.md

### Q6 — Answer: C

**Why C is correct:** §6 ("`context: fork` — what it actually does") explains that setting `context: fork` spawns a fresh, isolated session; only the skill's final message returns to the main session, and intermediate turns stay invisible. The rule of thumb is "multi-step skill with more than a couple of tool calls → `context: fork`."

**Why the others are wrong:**
- A. §9 lists this exact anti-pattern: "prompt guidance can't create isolation — isolation is a runtime mechanism." You have to set `context: fork` in frontmatter.
- B. Commands run in the current session and don't scope tools; splitting the work into commands doesn't isolate context.
- D. Removing `allowed-tools` broadens the tool surface — it doesn't isolate context, and it makes the skill less safe.

**Reference:** §6 and §9 of reference.md

### Q7 — Answer: B

**Why B is correct:** §7 shows exactly this pattern: commit `.mcp.json` with `"env": { "GITHUB_TOKEN": "${GITHUB_TOKEN}" }`. `${VAR}` expansion happens at load time so each developer sets their own variable locally, keeping secrets out of git while still sharing the server definition.

**Why the others are wrong:**
- A. Hardcoding secrets and then gitignoring the file defeats the purpose of `.mcp.json` (team-shared configuration) and is listed as an anti-pattern in §9.
- C. User-scope `~/.claude.json` doesn't "inject" values into project `.mcp.json`; the two files are separate registrations that the session unions.
- D. `args` is parsed and passed to the subprocess exactly like `env`; hiding a secret there still leaks it via git.

**Reference:** §7 and §9 of reference.md

### Q8 — Answer: C

**Why C is correct:** §5 defines a command as a user-initiated, reusable saved prompt, ideal when the prompt is "short-to-medium and single-turn" and "different team members should get the same behavior when they type `/review`." A committed `.claude/commands/review.md` is exactly that.

**Why the others are wrong:**
- A. A rule with no `paths:` is a global-load anti-pattern (§4, §9); it also can't be explicitly invoked — rules are passive.
- B. Adding the guidance to root CLAUDE.md makes it always-on, paying the token cost every turn even when no review is happening (§2, §9).
- D. A skill is heavier machinery for a short single-turn prompt; the exam distinction (§6) reserves skills for multi-step, tool-scoped capabilities.

**Reference:** §5 and §6 of reference.md

### Q9 — Answer: C

**Why C is correct:** §3 ("When NOT to use `@import`") is explicit: `@import` is unconditional — it always inlines — and imports don't save tokens. For conditional loading you use `.claude/rules/*.md` with `paths:` frontmatter. §9 lists "`@import` used to save tokens" as an anti-pattern.

**Why the others are wrong:**
- A. The conditional-loading and token-saving claims are both false.
- B. `@import` works from any CLAUDE.md, including subdirectory files; §3 explicitly suggests using it from both root and subdir.
- D. §3's example uses a relative path (`./.claude/shared/style.md`); relative paths are supported.

**Reference:** §3 and §9 of reference.md

### Q10 — Answer: B

**Why B is correct:** §2 describes user scope (`~/.claude/CLAUDE.md`) as "your personal preferences… always prefer absolute imports" — exactly this kind of all-projects guidance. §5 and §12 reinforce that user scope applies in every session on that machine, every project. Since each developer installs locally, the rule lives in each developer's `~/.claude/CLAUDE.md`.

**Why the others are wrong:**
- A. Copying into every repo duplicates the rule, drifts over time, and bloats every repo's root CLAUDE.md with a cross-cutting personal-style directive (§9 "dumping everything into root CLAUDE.md").
- C. A rule with `paths: ["**"]` is effectively global (§9 anti-pattern "two rules both set `paths: ['**']`"); it also has to be re-copied into every repo, same maintenance problem as A.
- D. A command is user-invoked; if developers forget to type `/imports`, the instruction isn't applied. The requirement is automatic, always-on.

**Reference:** §2 and §9 of reference.md
