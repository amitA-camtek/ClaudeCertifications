# W04 — Tool Design & MCP

**Domain:** Foundations · 2.1–2.5
**Budget:** 2 days × 2.5 h = 5 h

## Study Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:10 | Warmup | Review W03 weak spots |
| 0:10–0:55 | Theory | Read [reference.md](reference.md) §1–2 — descriptions are the selector; input/output formats, positive + negative boundaries; split vs consolidate for near-similar tools |
| 0:55–1:40 | Theory | Read [reference.md](reference.md) §3 — structured errors (`isError`, `errorCategory`, `isRetryable`, `message`); retry branches on `isRetryable`, not string parsing |
| 1:40–2:20 | Theory+Sketch | Read [reference.md](reference.md) §4–5 — 4–5 tools per agent max, scoped access per role, `tool_choice` modes; sketch tool set for sample agent |
| 2:20–2:30 | Summary | 3-bullet recap → `notes/study_day.md` |

## Practice Day (2.5 h)

| Time | Block | Task |
|---|---|---|
| 0:00–0:30 | Polish | Wire a local MCP server using `.mcp.json` |
| 0:30–1:00 | Theory | Read [reference.md](reference.md) §6–8 — `.mcp.json` (project, committed) vs `~/.claude.json` (user, personal), `${ENV_VAR}` expansion for secrets, MCP tools vs resources, built-in tool selection (Read/Grep/Glob/Edit/Write/Bash) |
| 1:00–1:45 | Test | **Practice Test 4** — 10 Q on tool design & MCP |
| 1:45–2:20 | Review | Wrong answers → `practice_test/test4_review.md` |
| 2:20–2:30 | Weak spots | Update `notes/weak_spots.md` |

**Deliverables:** MCP config sample in `exercises/`, test-4 review, updated weak spots.
