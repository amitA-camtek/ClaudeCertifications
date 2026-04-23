# Exam Guide Summary — 5 Domains & 6 Scenarios

Extracted from the Claude Certified Architect – Foundations Certification Exam Guide (v0.1, 2025-02-10) so Week 1's warmup and theory blocks are self-contained.

---

## The 5 Content Domains (with weightings)

| # | Domain | Weight |
|---|---|---|
| 1 | **Agentic Architecture & Orchestration** | 27% |
| 2 | **Tool Design & MCP Integration** | 18% |
| 3 | **Claude Code Configuration & Workflows** | 20% |
| 4 | **Prompt Engineering & Structured Output** | 20% |
| 5 | **Context Management & Reliability** | 15% |

Domain 1 is the largest slice of the exam. This 12-week program is ordered so Domain 1 is covered first (W01–W03), then 2 (W04), 3 (W05–W06), 4 (W07–W08), 5 (W09–W10).

### What each domain contains (task statements)

- **Domain 1 — Agentic Architecture & Orchestration** (7 task statements)
  - 1.1 Design and implement agentic loops for autonomous task execution ← **this week**
  - 1.2 Orchestrate multi-agent systems with coordinator-subagent patterns
  - 1.3 Configure subagent invocation, context passing, and spawning
  - 1.4 Implement multi-step workflows with enforcement and handoff patterns
  - 1.5 Apply Agent SDK hooks for tool call interception and data normalization
  - 1.6 Design task decomposition strategies for complex workflows
  - 1.7 Manage session state, resumption, and forking

- **Domain 2 — Tool Design & MCP Integration** (5 task statements)
  - 2.1 Design effective tool interfaces with clear descriptions and boundaries
  - 2.2 Implement structured error responses for MCP tools
  - 2.3 Distribute tools appropriately across agents and configure tool choice
  - 2.4 Integrate MCP servers into Claude Code and agent workflows
  - 2.5 Select and apply built-in tools (Read, Write, Edit, Bash, Grep, Glob) effectively

- **Domain 3 — Claude Code Configuration & Workflows** (6 task statements)
  - 3.1 Configure CLAUDE.md files with appropriate hierarchy, scoping, and modular organization
  - 3.2 Create and configure custom slash commands and skills
  - 3.3 Apply path-specific rules for conditional convention loading
  - 3.4 Determine when to use plan mode vs direct execution
  - 3.5 Apply iterative refinement techniques for progressive improvement
  - 3.6 Integrate Claude Code into CI/CD pipelines

- **Domain 4 — Prompt Engineering & Structured Output** (6 task statements)
  - 4.1 Design prompts with explicit criteria to improve precision and reduce false positives
  - 4.2 Apply few-shot prompting to improve output consistency and quality
  - 4.3 Enforce structured output using tool use and JSON schemas
  - 4.4 Implement validation, retry, and feedback loops for extraction quality
  - 4.5 Design efficient batch processing strategies
  - 4.6 Design multi-instance and multi-pass review architectures

- **Domain 5 — Context Management & Reliability** (6 task statements)
  - 5.1 Manage conversation context to preserve critical information across long interactions
  - 5.2 Design effective escalation and ambiguity resolution patterns
  - 5.3 Implement error propagation strategies across multi-agent systems
  - 5.4 Manage context effectively in large codebase exploration
  - 5.5 Design human review workflows and confidence calibration
  - 5.6 Preserve information provenance and handle uncertainty in multi-source synthesis

---

## The 6 Exam Scenarios

The exam presents **4 scenarios drawn at random from these 6**. Each scenario frames multiple questions. You need to know all 6 so you're not surprised by whichever 4 show up.

### Scenario 1 — Customer Support Resolution Agent
A Claude Agent SDK agent handling high-ambiguity requests (returns, billing disputes, account issues) via custom MCP tools: `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`. Target: 80%+ first-contact resolution with sound escalation.
- **Primary domains:** 1 (Agentic), 2 (Tool/MCP), 5 (Context/Reliability)

### Scenario 2 — Code Generation with Claude Code
Team using Claude Code for generation, refactoring, debugging, docs. Requires custom slash commands, CLAUDE.md configs, and judgment on plan mode vs direct execution.
- **Primary domains:** 3 (Claude Code), 5 (Context/Reliability)

### Scenario 3 — Multi-Agent Research System
Coordinator agent delegates to specialized subagents: web search, document analysis, synthesis, report generation. Produces comprehensive cited reports.
- **Primary domains:** 1 (Agentic), 2 (Tool/MCP), 5 (Context/Reliability)

### Scenario 4 — Developer Productivity with Claude
Agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate, automate repetitive tasks. Uses built-in tools (Read, Write, Bash, Grep, Glob) + MCP servers.
- **Primary domains:** 2 (Tool/MCP), 3 (Claude Code), 1 (Agentic)

### Scenario 5 — Claude Code for Continuous Integration
Claude Code in CI/CD — automated code review, test generation, PR feedback. Prompts must give actionable feedback and minimize false positives.
- **Primary domains:** 3 (Claude Code), 4 (Prompt Engineering)

### Scenario 6 — Structured Data Extraction
System extracts info from unstructured documents, validates via JSON Schema, maintains high accuracy, handles edge cases, integrates with downstream systems.
- **Primary domains:** 4 (Prompt Engineering), 5 (Context/Reliability)

---

## How to use this for W01

- **Warmup (0:00–0:10):** skim the domain table and scenario list once — know the names, weights, and which domains each scenario primarily tests.
- **Theory (0:10–1:00):** read the task statements under each domain above. You don't need to master them this week — just know what each domain *covers* so later weeks slot in. Week 1 goes deep on 1.1 only (see `reference.md`).
- **Memorize:** the 5 domain names in order, their weights, and the 6 scenario headlines. A common exam trap is misattributing an issue to the wrong domain (e.g., treating a tool-selection failure as a context problem).

---

## Exam format facts worth remembering

- **Multiple choice, single best answer.** 1 correct + 3 distractors. No penalty for guessing.
- **Scaled score 100–1000, passing = 720.** Pass/fail designation.
- **4 of 6 scenarios shown per exam**, picked at random.
- **Target candidate:** solution architect, ~6+ months hands-on with Claude APIs, Agent SDK, Claude Code, MCP.

---

## Fast recap

- 5 domains: Agentic (27) · Tool/MCP (18) · Claude Code (20) · Prompt/Structured (20) · Context/Reliability (15).
- 6 scenarios, 4 shown live: Support agent · Code gen · Multi-agent research · Dev productivity · CI/CD · Structured extraction.
- Week 1 sits inside Domain 1, task 1.1 — the agentic loop itself. Everything else is mapped to later weeks.
