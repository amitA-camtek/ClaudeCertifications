# Minimal Headless Claude Code — 3 concrete invocations

Exercise for W06 Domain 3.6. Goal: internalize the three headless flags (`-p`, `--output-format json`, `--json-schema`) by reading three realistic invocations and the expected output shape.

All invocations below are non-interactive, single-shot, and machine-parseable. Interactive Claude Code is for humans; CI does not tolerate interactive prompts.

---

## Invocation 1 — plain `-p` (text result only)

Use this only when the caller is a human reading stdout, or when the downstream consumer is `tee` / a log file. **Do not** use this in pipelines that parse the output.

```bash
claude -p "List every TODO comment under ./src as a markdown table with columns (file, line, text)."
```

**Expected stdout** (natural language — NOT safe to parse):

```
| File              | Line | Text                           |
|-------------------|------|--------------------------------|
| src/auth.ts       |   42 | TODO: rotate keys quarterly    |
| src/db/pool.ts    |   17 | TODO: handle transient failures|
| src/cli.ts        |  103 | TODO: --json flag              |
```

Notes:
- Exit code 0 on success, non-zero on failure.
- Output shape is whatever the model decided to write this run. Next run may add a header line, skip one, reword cells. **Never regex this in CI.**

---

## Invocation 2 — `--output-format json` (envelope your script can parse)

Same prompt as above, but now wrapped in a stable JSON envelope. You can `jq` it.

```bash
claude -p "List every TODO comment under ./src. Return a JSON object \
with a 'todos' array of {file, line, text} entries." \
  --output-format json
```

**Expected stdout** (commented inline; in reality stdout is strict JSON):

```jsonc
{
  // Stable envelope fields — set by Claude Code, not the model.
  "session_id": "ses_01HXYZ...",
  "stop_reason": "end_turn",
  "model": "claude-sonnet-4-6",

  // The model's final message, as a STRING (still natural-language-shaped
  // inside — you'd still have to parse a markdown table out of it).
  "result": "{\n  \"todos\": [\n    {\"file\":\"src/auth.ts\",\"line\":42,...}\n  ]\n}"
}
```

Key point: `--output-format json` gives you an envelope you can safely parse, **but the `result` field is still whatever the model chose to write**. If you want the model's content itself to be schema-shaped, you also need `--json-schema` (Invocation 3).

Parse with `jq`:

```bash
claude -p "..." --output-format json | jq -r '.result'
```

---

## Invocation 3 — `--output-format json` + `--json-schema` (shape is a contract)

This is the real CI pattern. The model is constrained to produce a payload conforming to `todos.schema.json`. Syntax correctness is guaranteed by the runtime; semantic correctness (right file, right line) is still the model's job.

`todos.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["todos"],
  "additionalProperties": false,
  "properties": {
    "todos": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["file", "line", "text"],
        "additionalProperties": false,
        "properties": {
          "file": { "type": "string" },
          "line": { "type": "integer", "minimum": 1 },
          "text": { "type": "string" }
        }
      }
    }
  }
}
```

Invocation:

```bash
claude -p "List every TODO comment under ./src. Conform strictly to the schema." \
  --output-format json \
  --json-schema ./todos.schema.json
```

**Expected stdout** (commented inline):

```jsonc
{
  "session_id": "ses_01HABC...",
  "stop_reason": "end_turn",
  "model": "claude-sonnet-4-6",

  // `result` is now a JSON OBJECT, shape-guaranteed to match todos.schema.json.
  // The runtime rejects any attempt by the model to emit off-schema output.
  "result": {
    "todos": [
      { "file": "src/auth.ts",    "line":  42, "text": "TODO: rotate keys quarterly" },
      { "file": "src/db/pool.ts", "line":  17, "text": "TODO: handle transient failures" },
      { "file": "src/cli.ts",     "line": 103, "text": "TODO: --json flag" }
    ]
  }
}
```

Parse cleanly:

```bash
claude -p "..." --output-format json --json-schema ./todos.schema.json \
  | jq '.result.todos[] | "\(.file):\(.line)  \(.text)"'
```

---

## When plan mode is appropriate vs when to go direct

Headless `claude -p` is a **direct-execution** form by default — it runs one shot and exits. You don't literally toggle "plan mode" in CI the way you do in an interactive session. But the decision mindset still applies when you're deciding what prompt to send:

- **Go direct (pipeline-friendly):** tightly-scoped extraction / review / classification tasks where the schema already pins the output. The schema IS the plan.
  - "List TODOs in src/" → direct.
  - "Review this PR diff against review.schema.json" → direct.
  - "Extract metadata fields from these docs" → direct.

- **Use plan mode (interactive, human in the loop):** open-ended, multi-file, or irreversible work where a human must sign off before anything changes.
  - "Migrate all 45 test files from Jest to Vitest" → **plan mode in an interactive session**, not a headless pipeline. A pipeline shouldn't be silently rewriting 45 files.
  - "Refactor the auth module for clarity" → plan mode interactively; the schema for a 45-file refactor doesn't exist.

**Rule of thumb for CI:** if you can write a JSON Schema that defines "done," you can run it headless. If the task output is "a plan a human needs to approve," that's plan mode in an interactive session — it doesn't belong in the pipeline.

---

## Exam takeaways

- `-p` alone → human-readable, do not parse.
- `-p --output-format json` → stable envelope, but `result` content is still free-form unless you also constrain it.
- `-p --output-format json --json-schema <file>` → shape is a contract. This is the only form you put in a CI pipeline.
- Plan mode is for ambiguous / multi-file / irreversible interactive work. Headless pipelines want schema-defined tasks — if you can't write a schema for "done," it's probably not a pipeline task.
