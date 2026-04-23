# W05 APIs — Claude APIs for this week

> "APIs" this week = the **Claude Code configuration surface** (CLAUDE.md, rules, commands, skills, `/memory`). Not network APIs — configuration files the harness reads. All examples are runnable as-is.

---

## Configuration surfaces covered this week

| Surface | Scope | Purpose |
|---|---|---|
| `~/.claude/CLAUDE.md` | User | Personal preferences across all projects |
| `CLAUDE.md` or `.claude/CLAUDE.md` | Project (committed) | Team conventions |
| `<subdir>/CLAUDE.md` | Subdirectory | Narrow rules for a subtree |
| `.claude/rules/*.md` with `paths:` frontmatter | Conditional | Rules that load only for specific file patterns |
| `.claude/commands/<name>.md` | Project or user | Saved slash-command prompts |
| `.claude/skills/<name>/SKILL.md` | Project or user | Multi-step capabilities with `allowed-tools`, `context: fork` |
| `@import <path>` | Inside any CLAUDE.md | Modular include |
| `/memory` | Runtime | Diagnostic — which CLAUDE.md files loaded, in what order |

---

## Working example — a complete project config

Build this directory tree at a test project root:

```
my-project/
├── CLAUDE.md
├── .claude/
│   ├── CLAUDE.md
│   ├── rules/
│   │   └── tests.md
│   ├── commands/
│   │   └── review.md
│   └── skills/
│       └── audit-deps/
│           └── SKILL.md
└── src/
    └── legacy/
        └── CLAUDE.md
```

### 1. Root `CLAUDE.md` (project-wide)

```markdown
# Project: my-project

## Conventions
- Python 3.11+, type-hint all public functions.
- Use `ruff` for formatting (invoked via `just fmt`).
- Tests use `pytest` with fixtures in `tests/conftest.py`.

@.claude/rules/tests.md
```

Note the `@.claude/rules/tests.md` pulls in the testing rules verbatim.

### 2. `.claude/rules/tests.md` (path-scoped rule)

```markdown
---
paths: ["**/*_test.py", "tests/**/*.py"]
---

# Testing rules (applies only to test files)

- Use `pytest` parametrize, not `unittest.TestCase`.
- Each test function gets one `assert`; split otherwise.
- Mock `httpx.AsyncClient`, never the `requests` library (that was removed in Q2).
```

### 3. `.claude/commands/review.md` (slash command)

```markdown
---
description: Review the current git diff for regressions and suggest fixes.
argument-hint: [optional branch name, default HEAD]
---

Please review the git diff on branch $1 (or HEAD if empty).

For each changed file:
1. Identify the primary change.
2. Flag any of these regressions: missing null checks, untested error paths, dropped logging.
3. Suggest a one-line fix for each flag.
4. End with a summary: "OK to merge" or "Needs changes (N issues)".
```

Invoke inside Claude Code: `/review` or `/review feature-x`.

### 4. `.claude/skills/audit-deps/SKILL.md` (skill with forked context)

```markdown
---
description: Audit dependency freshness and CVE status. Runs in a forked session to avoid polluting the main conversation.
allowed-tools: [Read, Bash, Grep]
context: fork
argument-hint: [optional package-manager: pip|npm|cargo, default auto-detect]
---

You are a dependency auditor.

Steps:
1. Detect the package manager from the repo (requirements.txt, package.json, Cargo.toml).
2. Run the relevant list command (Bash): `pip list --outdated` / `npm outdated` / `cargo outdated`.
3. For each outdated package, use Read + Grep to check whether the new version would break anything.
4. Output a markdown table: package | current | latest | severity (high/med/low) | action.

Do NOT modify any files. Report only.
```

### 5. `src/legacy/CLAUDE.md` (subdirectory override)

```markdown
# Legacy subtree

Old code lives here. Overrides for this subtree:

- Ignore the "type-hint all public functions" project rule — this code predates typing.
- Preserve existing indentation (mix of tabs and spaces).
- New code should not be added here; ask before doing so.
```

---

## How to run and verify

**1. Create the tree** above inside a test project directory.

**2. Launch Claude Code** from the project root:
```bash
claude
```

**3. Verify CLAUDE.md loading** — inside Claude Code, run:
```
/memory
```

You should see something like:
```
Loaded CLAUDE.md files (in order):
  ~/.claude/CLAUDE.md
  CLAUDE.md
  .claude/CLAUDE.md          (if present)
```

Plus, when you `cd` into `src/legacy/` and run `/memory` again, the subdirectory CLAUDE.md should appear last.

**4. Verify rule scoping** — open a test file (e.g. `tests/test_foo.py`) and ask Claude to edit it. Claude should apply the `pytest`-parametrize rule. Open a non-test file; the rule should not apply.

**5. Test the slash command:**
```
/review
```
Should run the review prompt against current diff.

**6. Test the skill:**
```
/audit-deps
```
(or however your Claude Code version invokes skills — some versions use `@audit-deps`). Verify the skill runs in a *forked* session — its conversation shouldn't appear in your main transcript.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| `/memory` shows missing file | Wrong path / name / case | CLAUDE.md is case-sensitive on some filesystems; must be at project root or `.claude/` |
| Rule doesn't apply | `paths:` glob wrong | Test with a glob checker; `**/*.test.py` matches at any depth; `*.test.py` matches only top level |
| Slash command not found | File name is not `name.md` under `.claude/commands/` | File name maps to command name |
| Skill has no effect | Missing `description:` | Description is the model's selection signal — required |
| Skill pollutes main session | Missing `context: fork` | Add `context: fork` to the frontmatter |
| `@import` doesn't resolve | Path resolution is from the file containing the `@import`, not the project root | Use paths relative to the importing file |
| Subdirectory CLAUDE.md not picked up | Running Claude Code from wrong directory | `cd` into the subdirectory or pass `--cwd` |

**Force a reload after editing config:**
Restart Claude Code — config loads at session start.

**Show full loaded context:**
```
/memory --verbose
```
(Availability depends on Claude Code version; check `claude --help`.)

---

## Exam connection

- The exam tests **scope resolution**: subdirectory > project > user, by *recency* in the loaded concatenation.
- `paths:` frontmatter is a direct exam topic — questions give a glob and ask whether the rule fires on a specific file.
- Slash command vs skill: slash command = saved prompt; skill = multi-step + `allowed-tools` + optional `context: fork`. The exam tests knowing which to pick for a given scenario.
- `/memory` as the diagnostic is a commonly-right answer to "Claude isn't following my rule — what do you do first?"
