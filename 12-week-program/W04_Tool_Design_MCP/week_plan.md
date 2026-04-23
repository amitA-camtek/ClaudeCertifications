# W04 — Tool Design & MCP

**Domain:** Foundations · 2.1–2.5
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W03 weak spots |
| 0:10–0:55 | Theory | Tool description best practices: input formats, examples, edge cases |
| 0:55–1:40 | Theory | Structured error responses: `isError`, `errorCategory`, `isRetryable` |
| 1:40–2:20 | Theory+Sketch | Tool distribution rule (4–5 tools/agent), scoped tool access; sketch tool set for sample agent |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Wire a local MCP server using `.mcp.json` |
| 0:30–1:00 | Theory | MCP config: `.mcp.json` (project) vs `~/.claude.json` (user); built-ins (Read, Write, Edit, Bash, Grep, Glob) — when to use each |
| 1:00–1:45 | Test | **Practice Test 4** — 10 Q on tool design & MCP |
| 1:45–2:20 | Review | Wrong answers → `practice_test/test4_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** MCP config sample in `exercises/`, test-4 review, updated weak spots.
