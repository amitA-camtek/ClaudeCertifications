# Minimal — CLAUDE.md hierarchy (3 levels + `@import`)

Smallest possible illustration of CLAUDE.md precedence: user-level, project-root, and subdirectory. Plus `@import` in action. No real repo required — read the file listings and walk through the "what loads when" at the bottom.

## The layout

```
~/.claude/
  CLAUDE.md                    # user-level, all projects

<repo>/
  CLAUDE.md                    # project root — team conventions
  .claude/
    shared/
      style.md                 # imported fragment
  src/
    frontend/
      CLAUDE.md                # subdirectory — frontend-specific
```

## File 1 — `~/.claude/CLAUDE.md` (user scope)

```markdown
# Personal preferences (applies to every project on this machine)

- Use 2-space indentation by default.
- Prefer absolute imports over relative when the language supports it.
- When I ask for a commit message, follow Conventional Commits (feat:, fix:, chore:, etc.).
- I work in TypeScript, Python, and Go. Default to TypeScript if a language isn't specified.
```

User scope is for **your** preferences. It follows you to every project. It is **not** shared with teammates — it lives in your home directory, not in any repo.

## File 2 — `<repo>/CLAUDE.md` (project root)

```markdown
# Acme Monorepo — team conventions

This is the `acme-core` monorepo. Node 20 + pnpm workspaces + TypeScript strict mode.

## Directory layout

- `src/backend/`   — Fastify API (Node)
- `src/frontend/`  — React 18 SPA
- `src/shared/`    — types + utility packages consumed by both sides
- `db/migrations/` — SQL migrations (numeric prefix, e.g. `0042_add_users.sql`)

## Team-wide rules

- We use **4-space indentation** across the whole repo. (Yes, this contradicts the author's personal preference — the repo convention wins inside this repo.)
- All PRs require one approving review + passing CI.
- No direct commits to `main`.

@import ./.claude/shared/style.md
```

Key points:
- Overrides the user-level 2-space rule with 4-space for this repo. User config is still present — it's just layered under the project config, which wins on conflict.
- Uses `@import` to inline shared style content. The imported file is resolved at load time and its content becomes part of this CLAUDE.md.
- Describes layout and tech stack — stuff every request in this repo benefits from knowing. Correct choice for root CLAUDE.md.

## File 3 — `<repo>/.claude/shared/style.md` (the imported fragment)

```markdown
# Code style (imported by root CLAUDE.md)

- Prefer named exports; avoid `export default` except for framework conventions that require it.
- File names: `kebab-case.ts` for modules, `PascalCase.tsx` for React components.
- No `any`. If you truly need an escape hatch, use `unknown` + a narrowing check.
- Public functions must have JSDoc; internal functions need it only when non-obvious.
```

This is not a CLAUDE.md — it's a plain Markdown fragment designed to be `@import`-ed. You can import the same fragment from multiple CLAUDE.md files (e.g., the root CLAUDE.md and the frontend CLAUDE.md could both import it).

## File 4 — `<repo>/src/frontend/CLAUDE.md` (subdirectory scope)

```markdown
# Frontend subdirectory — overrides

This folder is our React 18 SPA. The following rules **override** the repo-wide defaults when Claude Code is working on files inside `src/frontend/` (or any subdirectory of it).

## Indentation

- Use **2-space indentation** here. Prettier is configured for 2 in this package, and the rest of the repo uses 4.

## Component conventions

- All components live in `src/frontend/components/`.
- Prefer function components with hooks. No class components.
- Co-locate tests next to components: `Button.tsx` + `Button.test.tsx`.
- Use the project's `Button`, `Input`, `Modal` primitives — do NOT import from MUI or Chakra here.
```

Subdirectory CLAUDE.md files exist to carry narrow, local rules that would be noise at the repo root. They only load when Claude Code is working on files **inside that subtree**.

## Precedence walkthrough — who wins

### Editing `src/backend/server.ts` (outside `src/frontend/`)

Loaded CLAUDE.md chain:
1. `~/.claude/CLAUDE.md` (user)
2. `<repo>/CLAUDE.md` (project root, with `@import` inlined)

The `src/frontend/CLAUDE.md` is **not** loaded — we're not in that subtree.

Indentation conflict resolution:
- User says 2-space.
- Project says 4-space.
- **4-space wins** (project is more specific than user).

### Editing `src/frontend/components/Button.tsx`

Loaded CLAUDE.md chain:
1. `~/.claude/CLAUDE.md` (user)
2. `<repo>/CLAUDE.md` (project root)
3. `<repo>/src/frontend/CLAUDE.md` (subdirectory — we're inside it)

Indentation conflict resolution:
- User says 2-space.
- Project says 4-space.
- Frontend subdirectory says 2-space.
- **2-space wins** (frontend subdirectory is the most specific scope for this file).

Note that this ends up *agreeing* with the user preference — but only because of the subdirectory override. The user-level value wasn't promoted; the subdirectory value was.

### Editing `src/shared/types.ts`

Loaded CLAUDE.md chain:
1. `~/.claude/CLAUDE.md`
2. `<repo>/CLAUDE.md`

`src/shared/` has no CLAUDE.md, so nothing else loads. 4-space from the project wins.

## `@import` mechanics — what's actually in the prompt

When Claude Code assembles the system prompt for a session in `<repo>/`:

- It reads `<repo>/CLAUDE.md`.
- It sees `@import ./.claude/shared/style.md` and inlines that file's contents at that position.
- The final text sent to the model contains the project-level rules **followed by** the style rules from the imported fragment — as if they had been written in one file.

Key consequences:
- **Tokens are not saved** by using `@import`. The content is in the prompt either way.
- **`@import` is unconditional.** It always inlines. If you want "only load this when editing test files," that's a `.claude/rules/testing.md` with `paths:` frontmatter — not an import.
- **Imports can chain.** `shared/style.md` could itself contain `@import ./naming.md`, which gets inlined too.

## What this exercise demonstrates — mapped to exam concepts

| Element | W05 concept exercised |
|---|---|
| Three-level stack: user → project → subdirectory | CLAUDE.md hierarchy |
| User 2-space vs project 4-space, project wins | "More specific scope wins on conflict" |
| Subdirectory CLAUDE.md for `src/frontend/` | Subdirectory scope activates only inside the subtree |
| `@import ./.claude/shared/style.md` | Modular CLAUDE.md composition; unconditional inlining |
| Root CLAUDE.md containing layout + tech stack, not per-file rules | Correct use of root scope — reserve it for always-relevant context |

## Common mistakes this exercise helps you recognize

- Putting the frontend-specific "use 2-space" rule in root CLAUDE.md — wrong, it's irrelevant when editing backend files and would confuse the model.
- Putting the team's 4-space rule in `~/.claude/CLAUDE.md` — wrong, teammates won't get it.
- Expecting `@import` to save tokens — wrong, it's for modularity.
- Expecting user scope to override project scope — wrong, project is more specific.
