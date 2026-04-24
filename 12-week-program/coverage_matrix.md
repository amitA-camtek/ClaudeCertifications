# Coverage Matrix — Exam Task Statements → Program Weeks

One-stop traceability: every exam task statement from the official guide, mapped to the specific week(s) + `reference.md` section(s) + exercise(s) that cover it.

Use this to:
- **Spot-check coverage** before Practice Exam 1 — no task statement should be "unfamiliar".
- **Revisit specific weaknesses** — if you missed a question about 4.4 (validation-retry), this matrix tells you exactly where to re-read.
- **Audit the program** — if you ever suspect a gap, check here first.

Legend:
- **Primary week:** where the task statement is taught end-to-end.
- **Reinforced in:** where it recurs in exercises or cross-references.
- **⚠** flags task statements where coverage is thinner than the exam weight suggests — worth extra attention.

---

## Domain 1 — Agentic Architecture & Orchestration (27%, 7 task statements)

| Task | Topic | Primary week | Reference section | Reinforced in |
|---|---|---|---|---|
| 1.1 | Design and implement agentic loops for autonomous task execution | W01 | [W01 reference.md §1–7](W01_Agentic_Loops/reference.md) | W11 Ex 1, W11 Ex 4 coordinator |
| 1.2 | Orchestrate multi-agent systems with coordinator-subagent patterns | W02 | [W02 reference.md §1–2, §9](W02_Multi_Agent_Orchestration/reference.md) | W11 Ex 4 |
| 1.3 | Configure subagent invocation, context passing, and spawning | W02 | [W02 reference.md §3–4](W02_Multi_Agent_Orchestration/reference.md) | W11 Ex 4 |
| 1.4 | Implement multi-step workflows with enforcement and handoff patterns | W03 | [W03 reference.md](W03_Hooks_Workflows_Sessions/reference.md) | W11 Ex 1 (escalation) |
| 1.5 | Apply Agent SDK hooks for tool call interception and data normalization | W03 | [W03 reference.md §11 (anti-patterns)](W03_Hooks_Workflows_Sessions/reference.md) | W11 Ex 1 (refund cap) |
| 1.6 | Design task decomposition strategies for complex workflows | W02, W03 | [W02 reference.md §7–8](W02_Multi_Agent_Orchestration/reference.md) | W11 Ex 4 |
| 1.7 | Manage session state, resumption, and forking | W03 | [W03 reference.md](W03_Hooks_Workflows_Sessions/reference.md) | [adjacent_concepts_drill.md Pair 1.3](W12_Final_Exam_Prep/exercises/adjacent_concepts_drill.md) |

---

## Domain 2 — Tool Design & MCP Integration (18%, 5 task statements)

| Task | Topic | Primary week | Reference section | Reinforced in |
|---|---|---|---|---|
| 2.1 | Design effective tool interfaces with clear descriptions and boundaries | W04 | [W04 reference.md §9](W04_Tool_Design_MCP/reference.md) | W01 §5 (tool definitions), W11 Ex 1 |
| 2.2 | Implement structured error responses for MCP tools | W04 | [W04 reference.md](W04_Tool_Design_MCP/reference.md), [W09 reference.md §11](W09_Context_Management/reference.md) | W11 Ex 1 |
| 2.3 | Distribute tools appropriately across agents and configure tool choice | W04 | [W04 reference.md](W04_Tool_Design_MCP/reference.md), [W01 reference.md §6](W01_Agentic_Loops/reference.md) | W02 §9, W11 Ex 4 |
| 2.4 | Integrate MCP servers into Claude Code and agent workflows | W04 | [W04 reference.md](W04_Tool_Design_MCP/reference.md) | W11 Ex 2 |
| 2.5 | Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively | W04 | [W04 reference.md](W04_Tool_Design_MCP/reference.md) | [W11 scenario_4 walkthrough](W11_Integration_Hands_On/exercises/scenario_4_developer_productivity_walkthrough.md) |

---

## Domain 3 — Claude Code Configuration & Workflows (20%, 6 task statements)

| Task | Topic | Primary week | Reference section | Reinforced in |
|---|---|---|---|---|
| 3.1 | Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization | W05 | [W05 reference.md §9](W05_Claude_Code_Config/reference.md) | W11 Ex 2 |
| 3.2 | Create and configure custom slash commands and skills | W05 | [W05 reference.md](W05_Claude_Code_Config/reference.md) | W11 Ex 2, [adjacent_concepts_drill Pair 3.1](W12_Final_Exam_Prep/exercises/adjacent_concepts_drill.md) |
| 3.3 | Apply path-specific rules for conditional convention loading | W05 | [W05 reference.md](W05_Claude_Code_Config/reference.md) | W11 Ex 2 |
| 3.4 | Determine when to use plan mode vs direct execution | W06 | [W06 reference.md §6](W06_Plan_Mode_Iteration_CICD/reference.md) | [scenario_4](W11_Integration_Hands_On/exercises/scenario_4_developer_productivity_walkthrough.md), [scenario_5](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |
| 3.5 | Apply iterative refinement techniques for progressive improvement | W06 | [W06 reference.md](W06_Plan_Mode_Iteration_CICD/reference.md) | — |
| 3.6 | Integrate Claude Code into CI/CD pipelines | W06 | [W06 reference.md §6](W06_Plan_Mode_Iteration_CICD/reference.md) | [scenario_5 walkthrough](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |

---

## Domain 4 — Prompt Engineering & Structured Output (20%, 6 task statements)

| Task | Topic | Primary week | Reference section | Reinforced in |
|---|---|---|---|---|
| 4.1 | Design prompts with explicit criteria to improve precision and reduce false positives | W07 | [W07 reference.md §9](W07_Prompt_Engineering_Structured_Output/reference.md) | [scenario_5 walkthrough §3](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |
| 4.2 | Apply few-shot prompting to improve output consistency and quality | W07 | [W07 reference.md](W07_Prompt_Engineering_Structured_Output/reference.md) | W11 Ex 3 |
| 4.3 | Enforce structured output using tool use and JSON schemas | W07 | [W07 reference.md](W07_Prompt_Engineering_Structured_Output/reference.md) | W11 Ex 3 |
| 4.4 | Implement validation, retry, and feedback loops for extraction quality | W08 | [W08 reference.md §8](W08_Validation_Batch_MultiPass/reference.md) | W11 Ex 3 |
| 4.5 | Design efficient batch processing strategies | W08 | [W08 reference.md](W08_Validation_Batch_MultiPass/reference.md) | [operational_topics §4](W11_Integration_Hands_On/operational_topics.md) |
| 4.6 | Design multi-instance and multi-pass review architectures | W08 | [W08 reference.md §1 (structure/semantics split)](W08_Validation_Batch_MultiPass/reference.md) | [scenario_5 §2](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |

---

## Domain 5 — Context Management & Reliability (15%, 6 task statements)

| Task | Topic | Primary week | Reference section | Reinforced in |
|---|---|---|---|---|
| 5.1 | Manage conversation context to preserve critical information across long interactions | W09 | [W09 reference.md](W09_Context_Management/reference.md) | — |
| 5.2 | Design effective escalation and ambiguity resolution patterns | W09 | [W09 reference.md](W09_Context_Management/reference.md) | W11 Ex 1 |
| 5.3 | Implement error propagation strategies across multi-agent systems | W09 | [W09 reference.md §11](W09_Context_Management/reference.md) | W11 Ex 4, [scenario_5 §5](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |
| 5.4 | Manage context effectively in large codebase exploration | W10 | [W10 reference.md](W10_Advanced_Context_Provenance/reference.md) | [scenario_4 walkthrough](W11_Integration_Hands_On/exercises/scenario_4_developer_productivity_walkthrough.md) |
| 5.5 | Design human review workflows and confidence calibration | W10 | [W10 reference.md §9](W10_Advanced_Context_Provenance/reference.md) | W11 Ex 3 |
| 5.6 | Preserve information provenance and handle uncertainty in multi-source synthesis | W10 | [W10 reference.md](W10_Advanced_Context_Provenance/reference.md) | W11 Ex 4 |

---

## The 6 Exam Scenarios → Coverage

The exam shows **4 of 6** scenarios at random. You need all 6 drilled.

| # | Scenario | Primary domains | Coverage |
|---|---|---|---|
| 1 | Customer Support Resolution Agent | 1, 2, 5 | [W11 Exercise 1](W11_Integration_Hands_On/exercises/exercise_1_multi_tool_agent_with_escalation.py) |
| 2 | Code Generation with Claude Code | 3, 5 | [W11 Exercise 2](W11_Integration_Hands_On/exercises/exercise_2_claude_code_team_workflow.md) |
| 3 | Multi-Agent Research System | 1, 2, 5 | [W11 Exercise 4](W11_Integration_Hands_On/exercises/exercise_4_multi_agent_research_pipeline.py) |
| 4 | Developer Productivity with Claude | 2, 3, 1 | [scenario_4 walkthrough](W11_Integration_Hands_On/exercises/scenario_4_developer_productivity_walkthrough.md) |
| 5 | Claude Code for CI/CD | 3, 4 | [scenario_5 walkthrough](W11_Integration_Hands_On/exercises/scenario_5_ci_cd_walkthrough.md) |
| 6 | Structured Data Extraction | 4, 5 | [W11 Exercise 3](W11_Integration_Hands_On/exercises/exercise_3_structured_extraction_pipeline.py) |

---

## Cross-cutting topics (not in the task-statement list but tested)

These appear in distractors but aren't called out as their own task statement in the guide. Coverage:

| Topic | Coverage |
|---|---|
| Prompt caching (`cache_control`, TTL, breakpoints) | [operational_topics §1](W11_Integration_Hands_On/operational_topics.md) |
| Extended thinking / reasoning mode | [operational_topics §2](W11_Integration_Hands_On/operational_topics.md) |
| Model selection (Opus/Sonnet/Haiku) | [operational_topics §3](W11_Integration_Hands_On/operational_topics.md) |
| Cost / token economics | [operational_topics §4](W11_Integration_Hands_On/operational_topics.md) |
| Prompt-vs-mechanism recurring theme | [W11 integration_notes §2](W11_Integration_Hands_On/integration_notes.md), [W11 anti-pattern block](W11_Integration_Hands_On/week_plan.md) |
| Adjacent-concept discrimination (which-one-of-two-plausible-answers) | [adjacent_concepts_drill](W12_Final_Exam_Prep/exercises/adjacent_concepts_drill.md) |

---

## Self-audit checklist

Before Practice Exam 1, tick every task statement where you can answer **all three** out loud in 30 seconds each:

- [ ] 1.1 stop_reason, message contract, safety fuse
- [ ] 1.2 coordinator vs subagent responsibilities
- [ ] 1.3 Task tool, allowedTools, context isolation
- [ ] 1.4 multi-step handoff patterns
- [ ] 1.5 PreToolUse vs PostToolUse timing
- [ ] 1.6 fixed chain vs adaptive decomposition
- [ ] 1.7 fork_session vs --resume vs fresh
- [ ] 2.1 rich tool descriptions; split vs mega-tool
- [ ] 2.2 isError/errorCategory/isRetryable
- [ ] 2.3 tool_choice auto/any/forced; 4–5 per subagent
- [ ] 2.4 .mcp.json vs ~/.claude.json; ${ENV_VAR}
- [ ] 2.5 Read/Grep/Glob/Bash/Edit — when each is correct
- [ ] 3.1 CLAUDE.md hierarchy, @import scope
- [ ] 3.2 command vs skill vs rule discriminator
- [ ] 3.3 paths: frontmatter glob semantics
- [ ] 3.4 when plan mode earns its overhead
- [ ] 3.5 concrete feedback; TDD; interview pattern
- [ ] 3.6 --output-format json --json-schema; fresh sessions
- [ ] 4.1 categorical criteria, false positive budget
- [ ] 4.2 2–4 edge-case few-shots with reasoning shown
- [ ] 4.3 tool_use + input_schema
- [ ] 4.4 validation-retry with specific error feedback
- [ ] 4.5 batch vs sync boundary; custom_id
- [ ] 4.6 generator-reviewer independence
- [ ] 5.1 case facts block vs summarization
- [ ] 5.2 categorical escalation triggers; NOT sentiment
- [ ] 5.3 structured error envelope (not [] or generic string)
- [ ] 5.4 grep-before-read; incremental context building
- [ ] 5.5 stratified accuracy (doc type × field); empirical calibration
- [ ] 5.6 preserve both on conflict; publication_date
- [ ] caching: cache stable prefixes, 5-min TTL, up to 4 breakpoints
- [ ] thinking: quality-for-cost trade; billed at output rate
- [ ] models: Sonnet default; upgrade/downgrade with evidence
- [ ] cost: batches 50% off + 24h; caching pays at reuse + 1024 tokens

If any box is unchecked a week before the exam, that's your re-read list.
