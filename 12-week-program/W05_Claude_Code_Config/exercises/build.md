# Build — Claude Code Configuration

**Time:** 40 min · **Goal:** Ship a working project-scope `/pr-summary` slash command plus a `pr-summary` skill with `context: fork` and a scoped tool allow-list, wired into a CLAUDE.md hierarchy that proves precedence.

## What you'll have at the end
- `.claude/commands/pr-summary.md` — project-scope slash command with `argument-hint` + `allowed-tools` frontmatter
- `.claude/skills/pr-summary/SKILL.md` — multi-step skill with `context: fork`, `allowed-tools`, `argument-hint`
- A `CLAUDE.md` at repo root + one subdirectory `CLAUDE.md` that together demonstrate scope precedence
- A `/memory` run showing the expected merge order

## Prereqs
- Claude Code installed, you can open a session inside a scratch repo
- Finished reading [reference.md](../reference.md) §5–§6 (plus §1–§2 from earlier theory)
- Target files: `.claude/commands/pr-summary.md` and `.claude/skills/pr-summary/SKILL.md` (peek at [minimal_claude_md_hierarchy.md](minimal_claude_md_hierarchy.md) if stuck)

## Steps

### 1. Decide scope — project vs user (~3 min)
You want teammates to get the same `/pr-summary` behavior, so both artifacts go under `<repo>/.claude/`, not `~/.claude/`.
- [ ] Create `<repo>/.claude/commands/` and `<repo>/.claude/skills/pr-summary/`
- [ ] Confirm nothing personal (commit style, language default) is going into these files — that belongs in `~/.claude/CLAUDE.md`

**Why:** project scope is shared via git; user scope is your machine only (§1, §5 two-scope table).
**Checkpoint:** `ls .claude/commands .claude/skills/pr-summary` shows two empty target dirs.

### 2. Write the slash command with frontmatter (~8 min)
Create `.claude/commands/pr-summary.md`. Body is the prompt; frontmatter is UI metadata.
- [ ] Add frontmatter: `description:` one-liner, `argument-hint: "<PR number>"`, `allowed-tools: ["Read", "Bash(git diff:*)", "Bash(gh pr view:*)"]`
- [ ] Write a 4–6 line prompt body that uses `$ARGUMENTS` to reference the PR number

**Why:** `argument-hint` surfaces the expected arg in the UI; `allowed-tools` restricts Bash to `git diff` and `gh pr view` patterns so the command can't run arbitrary shell (§5 command anatomy).
**Checkpoint:** open the file — frontmatter is between two `---` lines, the body is pure prompt text, no code fences.

### 3. Write the skill with `context: fork` (~10 min)
Create `.claude/skills/pr-summary/SKILL.md`. Same name as the command is fine — skill is a capability, command is a saved prompt.
- [ ] Frontmatter keys: `description`, `argument-hint: "<PR number>"`, `allowed-tools: ["Read", "Grep", "Bash(git diff:*)", "Bash(gh pr view:*)"]`, `context: fork`
- [ ] Body: numbered steps (view PR, diff base, classify type, emit one-line release-notes entry)

Minimum viable shape:

```
---
description: Summarize a PR into a release-notes entry
argument-hint: "<PR number>"
allowed-tools: ["Read", "Grep", "Bash(git diff:*)", "Bash(gh pr view:*)"]
context: fork
---
```

**Why:** `context: fork` spawns an isolated session so the skill's intermediate tool calls don't pollute your main context (§6 `context: fork`). `allowed-tools` is runtime scoping, not a prompt suggestion (§9 anti-pattern row on "tell the skill to fork in CLAUDE.md").
**Checkpoint:** `SKILL.md` has all five frontmatter keys; file lives at `.claude/skills/pr-summary/SKILL.md` (not directly in `.claude/skills/`).

### 4. Place CLAUDE.md at the right scope (~7 min)
Demonstrate the precedence chain.
- [ ] Root `<repo>/CLAUDE.md`: tech stack + directory layout + team-wide rule (e.g., "4-space indentation")
- [ ] Subdirectory `<repo>/src/frontend/CLAUDE.md`: one narrow override (e.g., "2-space here")
- [ ] Do NOT duplicate the frontend override into root CLAUDE.md

**Why:** root CLAUDE.md costs tokens on every turn; path-specific content belongs in a subdirectory CLAUDE.md or a `.claude/rules/*.md` with `paths:` (§2 "what belongs where" table, §9 row 1).
**Checkpoint:** root CLAUDE.md has no frontend-only rule; `src/frontend/CLAUDE.md` has the override.

### 5. Invoke and verify precedence with `/memory` (~7 min)
Start a session inside the repo.
- [ ] Run `/memory` — confirm user CLAUDE.md + project CLAUDE.md are listed; subdirectory CLAUDE.md is absent
- [ ] `cd src/frontend`, restart the session, run `/memory` again — subdirectory CLAUDE.md now appears below project root
- [ ] Run `/pr-summary 42` — command body executes with `$ARGUMENTS=42`

**Why:** `/memory` is the canonical diagnostic for hierarchy issues; command resolution prefers project scope over user scope on name collision (§2 `/memory`, §5 resolution order).
**Checkpoint:** `/memory` output matches Scenario A from §8; `/pr-summary` runs without errors.

### 6. Trigger the skill and confirm fork isolation (~5 min)
From the main session, invoke the skill (by name or via its description).
- [ ] Observe: the skill's intermediate tool calls do not appear as turns in your main session — only its final message comes back
- [ ] Try a `Write` inside the skill — it should be refused because `Write` is not in `allowed-tools`

**Why:** `context: fork` is runtime isolation (§6, Scenario D in §8); `allowed-tools` is enforced at the harness level, not by politeness (§6 frontmatter table).
**Checkpoint:** main-session history has one "skill output" message, not 5–10 exploration turns.

## Verify
Run `/pr-summary 42` and invoke the skill. Expected:
- Command: runs in current session, substitutes `$ARGUMENTS`, respects its `allowed-tools`
- Skill: runs in a forked context, returns a single summary message, `Write` attempt is denied
- `/memory` shows root + user CLAUDE.md (and subdirectory CLAUDE.md only when cwd is inside `src/frontend/`)

**Common mistakes:**
- Putting the skill file directly at `.claude/skills/pr-summary.md` instead of `.claude/skills/pr-summary/SKILL.md` (§6 anatomy)
- Omitting `context: fork` on a multi-tool skill — main context gets polluted (§6 rule of thumb, §9 row 5)
- Writing "please fork your context" into the SKILL.md body instead of setting the frontmatter key (§9 "instructions to fork" row)
- Putting the frontend 2-space rule in root CLAUDE.md (§2 "what belongs where", §9 row 1)
- Leaving `allowed-tools` off the skill, then being surprised it can `Write` (§6 frontmatter table)

## Stretch — Polish block (30 min on Practice Day)
From the Polish row: add `SKILL.md` with frontmatter `context: fork`, `allowed-tools`, `argument-hint`. Use this block to harden and extend what you built.
- [ ] Tighten `allowed-tools` — swap `Bash(git diff:*)` for the narrowest pattern that still works (e.g., `Bash(git diff --stat:*)` if you only need stats)
- [ ] Tune the `description` field — skills are model-selected by description, so be specific, not cute (§6 frontmatter table)
- [ ] Add a `model:` key if the skill is mechanical (e.g., cheaper model) — optional but exam-relevant (§6)
- [ ] Add a `templates/summary.md` file under the skill dir and reference it from SKILL.md body
- [ ] Re-run `/memory` after each change; confirm nothing leaked into root CLAUDE.md

## If stuck
Compare with [minimal_claude_md_hierarchy.md](minimal_claude_md_hierarchy.md). Read → close → rewrite.
