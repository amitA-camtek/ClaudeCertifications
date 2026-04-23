# W09 Videos — Paraphrased Notes

> Key points from public Anthropic talks, paraphrased locally so you don't need to leave this folder for exam prep. External links at the bottom are **optional** viewing.

**Week focus:** long-session failure modes, `case_facts` persistent block, position-aware ordering, trimming verbose tool output, valid escalation triggers, structured error propagation.

---

## Talk 1 — "Long context prompting" (Anthropic)

- **Bigger context ≠ better reasoning.** Attention quality degrades with length. Going from 50k → 200k tokens does not linearly improve recall; for many tasks it makes it worse. The *solution* to a long task is almost never "use a bigger window" — it's "split into passes."
- **Lost-in-the-middle is real.** Evidence placed in the middle of a long prompt is retrieved less reliably than evidence at the start or end. Mitigations:
  - Put the most important instructions at the **start** and again (in compressed form) at the **end**.
  - Use section headers (`## Case facts`, `## User message`, `## Instructions`) so the model can navigate.
  - Put critical numbers/IDs at the edges, not buried in a paragraph.
- **Summarization loses numbers, dates, IDs.** Progressive summarization of long sessions is lossy exactly where precision matters. Extract these to a structured `case_facts` block that gets re-injected verbatim every turn.

---

## Talk 2 — `case_facts` and tool-output trimming

- **`case_facts` pattern.** A small, structured block that persists across turns: account IDs, amounts, dates, agreed actions. Re-injected in each user turn. Size: ~100-500 tokens, not 5000.
- **Trim verbose tool output at the boundary.** A tool that returns 40 fields when you need 5 is dumping cognitive load on the model (and your token bill). Trim in the tool wrapper, not in the prompt. Keep the 5 relevant fields; log the rest to disk if you need it later.
- **Anti-pattern:** "summarize the whole conversation every 10 turns." Works until the summary loses the account ID that the user's next question depends on. The summary is the problem; replace it with an extraction.

---

## Talk 3 — Escalation: valid triggers vs distractors

- **Valid escalation triggers:**
  1. **Explicit customer request** — "I want to speak to a manager." Non-negotiable.
  2. **Policy gap** — the customer's request falls outside the agent's authorized actions.
  3. **Inability to progress** — the agent has tried the reasonable paths and is stuck.
- **NOT valid triggers (these are exam distractors):**
  - **Sentiment.** An angry customer with a simple request should still get the simple answer. An anger-triggered escalation is user-hostile *and* unreliable (sarcasm, typing style, language all confuse sentiment).
  - **Self-reported confidence.** "I'm not sure" from the model is miscalibrated — especially on hard cases where it most matters.
  - **Length of conversation.** Long conversation ≠ escalation-worthy.
- **Multiple matches:** if a lookup returns 3 customers matching "John Smith," **ask for a disambiguator** (order number, phone). Don't heuristically guess based on recency or amount. Guessing is how you confirm an action against the wrong account.

---

## Talk 4 — Structured error propagation

- **The goal: the caller can recover.** That means the error contains enough information to choose the next action — retry, fall back, escalate, or surface to the user.
- **Fields to return on error:**
  - `failure_type` — categorical, not a message.
  - `attempted_query` / `attempted_action` — what the tool actually tried.
  - `partial_results` — anything we did get before failing.
  - `alternatives` — what the caller might try next.
- **Anti-patterns:**
  - **Generic "operation failed"** — kills recovery.
  - **Empty result set on timeout marked as success** — silent suppression; caller cannot distinguish "no matches" from "I failed."
  - **Raise and abort the whole workflow** — loses partial progress that was valid.
- **Coordinator decides, subagent reports.** Subagents return structured errors; the coordinator owns the policy decision (retry here vs escalate to user vs fall back).

---

## Exam-relevance one-liners

- "Switch to a bigger context window to avoid losing context" → **attention quality doesn't scale; split passes instead.**
- "Use sentiment analysis to trigger escalation" → **sentiment ≠ complexity; wrong.**
- "Have the model self-report confidence 1-10 and escalate below a threshold" → **LLM self-confidence is miscalibrated; wrong.**
- "Return a generic 'operation failed' on error" → **kills recovery; return structured context.**
- "Guess the account when 3 match" → **ask for an identifier.**

---

## Optional external viewing

- Search — Anthropic long context prompting: https://www.youtube.com/results?search_query=anthropic+long+context+prompting
- Anthropic docs — long context tips: https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/long-context-tips
- Anthropic docs — reduce hallucinations: https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
