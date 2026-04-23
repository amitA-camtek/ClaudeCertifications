# Real-World CI Exercise — GitHub Actions PR review with Claude Code

This exercise is the W06 production pattern: a GitHub Actions workflow that runs `claude -p --output-format json --json-schema review.schema.json` against a PR's diff, parses the structured review, and posts comments / fails the check on blocking findings.

All files are shown inline so the exercise is self-contained.

---

## File 1 — `.github/workflows/claude-pr-review.yml`

```yaml
name: Claude PR Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write   # needed to post review comments
  issues: write          # pr comments go through the issues endpoint

jobs:
  claude-review:
    runs-on: ubuntu-latest
    timeout-minutes: 10   # hard ceiling — pre-merge check must not hang

    steps:
      # ------------------------------------------------------------------
      # 1. Check out the PR head commit so we can diff it against base.
      # ------------------------------------------------------------------
      - name: Checkout PR code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      # ------------------------------------------------------------------
      # 2. Produce the diff we'll hand to Claude. Keep it compact.
      # ------------------------------------------------------------------
      - name: Build diff
        id: diff
        run: |
          git diff \
            ${{ github.event.pull_request.base.sha }} \
            ${{ github.event.pull_request.head.sha }} \
            -- ':!**/*.lock' ':!**/vendor/**' \
            > pr.diff
          echo "diff_bytes=$(wc -c < pr.diff)" >> "$GITHUB_OUTPUT"

      # ------------------------------------------------------------------
      # 3. Install Claude Code CLI.
      # ------------------------------------------------------------------
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code

      # ------------------------------------------------------------------
      # 4. Run the REVIEWER — fresh session, headless, schema-constrained.
      #
      #    IMPORTANT:
      #      - No --resume, no shared session with anything.
      #      - The reviewer sees only the diff + PR title/body.
      #      - Output shape is pinned by review.schema.json.
      # ------------------------------------------------------------------
      - name: Run Claude reviewer
        id: review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PR_TITLE: ${{ github.event.pull_request.title }}
          PR_BODY:  ${{ github.event.pull_request.body }}
        run: |
          cat > prompt.txt <<'EOF'
          You are a senior code reviewer. Review the diff in pr.diff against the PR's
          stated intent (title and body below). Produce a structured review object
          that conforms STRICTLY to review.schema.json.

          Rules:
            - Only include findings tied to the diff content. Do not review unchanged code.
            - Each finding must have a file, line (1-based, from the diff), severity, category, and message.
            - severity: "blocking" reserved for correctness / security bugs. "warn" for smells. "info" for nits.
            - If there are no findings, return an empty issues array and approved=true.

          PR title: ${PR_TITLE}
          PR body:
          ${PR_BODY}

          Diff:
          $(cat pr.diff)
          EOF

          claude -p "$(cat prompt.txt)" \
            --output-format json \
            --json-schema ./review.schema.json \
            > review.json

      # ------------------------------------------------------------------
      # 5. Parse the review JSON and post comments on the PR.
      # ------------------------------------------------------------------
      - name: Post review comments
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
          REPO: ${{ github.repository }}
        run: |
          set -euo pipefail

          BLOCKING=$(jq '[.result.issues[] | select(.severity == "blocking")] | length' review.json)
          TOTAL=$(jq   '.result.issues | length' review.json)
          APPROVED=$(jq -r '.result.approved' review.json)

          echo "total findings: $TOTAL (blocking: $BLOCKING, approved: $APPROVED)"

          # Post one consolidated comment on the PR.
          BODY=$(jq -r '
            "## Claude review\n\n" +
            "- approved: \(.result.approved)\n" +
            "- blocking: \([.result.issues[] | select(.severity == "blocking")] | length)\n" +
            "- total:    \(.result.issues | length)\n\n" +
            ([.result.issues[] |
              "- **[\(.severity)] \(.category)** `\(.file):\(.line)` — \(.message)"
            ] | join("\n"))
          ' review.json)

          gh api \
            --method POST \
            "repos/${REPO}/issues/${PR_NUMBER}/comments" \
            -f body="$BODY"

          # Fail the check if anything is blocking.
          if [ "$BLOCKING" -gt 0 ]; then
            echo "::error::Claude review found $BLOCKING blocking issue(s)."
            exit 1
          fi
```

---

## File 2 — `review.schema.json` (JSON Schema, draft-07)

This is the contract. The reviewer's output is shape-guaranteed to match.

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "PR review",
  "type": "object",
  "required": ["approved", "issues"],
  "additionalProperties": false,
  "properties": {
    "approved": {
      "type": "boolean",
      "description": "true iff there are no blocking issues and the reviewer is satisfied."
    },
    "summary": {
      "type": "string",
      "description": "One-paragraph overall impression. 40-120 words."
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["file", "line", "severity", "category", "message"],
        "additionalProperties": false,
        "properties": {
          "file": {
            "type": "string",
            "description": "Path relative to repo root, as seen in the diff."
          },
          "line": {
            "type": "integer",
            "minimum": 1,
            "description": "1-based line number in the post-change file."
          },
          "severity": {
            "type": "string",
            "enum": ["blocking", "warn", "info"],
            "description": "blocking = correctness/security bug; warn = smell; info = nit."
          },
          "category": {
            "type": "string",
            "enum": [
              "correctness",
              "security",
              "performance",
              "style",
              "testing",
              "docs",
              "other"
            ]
          },
          "message": {
            "type": "string",
            "description": "Concrete, actionable. Reference the specific symbol or line behavior."
          },
          "suggestion": {
            "type": ["string", "null"],
            "description": "Optional concrete code or change suggestion."
          }
        }
      }
    }
  }
}
```

### Example `result` that conforms to the schema

```json
{
  "approved": false,
  "summary": "Adds a retry wrapper around the payment call. The retry is unbounded on transient errors and will mask persistent failures as flakes. One blocking issue.",
  "issues": [
    {
      "file": "src/payments.ts",
      "line": 88,
      "severity": "blocking",
      "category": "correctness",
      "message": "Retry loop has no max-attempts cap; a persistent 500 will loop forever and block the event queue.",
      "suggestion": "Cap at 3 attempts and surface the final error to the caller."
    },
    {
      "file": "src/payments.ts",
      "line": 102,
      "severity": "warn",
      "category": "testing",
      "message": "No test covers the retry path. Add a test with a mocked transient failure followed by success."
    }
  ]
}
```

---

## File 3 — Note: reviewer session is independent of generator session

This is the W06 lesson the exam hammers. Pulling it out into its own section so it's impossible to miss.

### The principle

**The session that generated the code must NOT be the same session that reviews it.** Self-review retains the generator's reasoning bias — the reviewer "already knows" why each choice was made and will rationalize its own output instead of catching flaws.

### How this manifests in the pipeline above

The workflow shown in File 1 is doing this correctly for two reasons:

1. **The generator is GitHub + the PR author** — not Claude in a prior step. So there's no shared Claude session to leak into the reviewer. (In a pipeline where an earlier step uses Claude to *write* code — e.g., auto-fix a lint violation — the same rule applies: that writer session is separate from the reviewer session.)

2. **No `--resume` flag anywhere.** Every `claude -p` invocation in CI starts a fresh session. The reviewer receives only the artifacts:
   - the diff (`pr.diff`)
   - the PR title and body
   - the schema

   It does NOT receive: prior reasoning traces, scratchpads from earlier Claude invocations, the generator's self-assessment.

### The wrong version (do not do this)

Imagine an earlier CI step that used Claude to auto-generate part of the code. A tempting but wrong pattern:

```yaml
# WRONG — reviewer resumes the writer's session
- name: Auto-fix lint violations
  run: |
    claude -p "Fix lint violations in src/" --session-id writer-${{ github.run_id }}

- name: Review
  run: |
    claude -p "Now review the changes you just made" \
      --resume writer-${{ github.run_id }}   # <-- shares bias, inherits context
```

The reviewer here inherits everything the writer session accumulated: its reasoning, its justifications, its blind spots. It will sign off on its own work.

### The right version

```yaml
# RIGHT — reviewer runs in a fresh session with only the artifacts
- name: Auto-fix lint violations
  run: |
    claude -p "Fix lint violations in src/. Write a summary of changes to ./writer.out." \
      --session-id writer-${{ github.run_id }}

- name: Review
  run: |
    # NO --resume. Reviewer sees the diff and the schema. Nothing else.
    git diff HEAD~1 HEAD > pr.diff
    claude -p "$(cat prompt.txt)" \
      --output-format json \
      --json-schema ./review.schema.json \
      > review.json
```

### Why this is the same idea as W02

In W02 you learned that a **subagent runs in an isolated context** so its exploration trace doesn't pollute the coordinator. Pre-merge review is the same pattern, split across two CLI invocations instead of two subagents: the reviewer is essentially a QA subagent whose isolation is enforced by *not sharing the session*.

### Exam rule of thumb

If a CI scenario shows the reviewer using `--resume` of a prior Claude session, or shows "the same session reviews what it generated" — **that's the wrong answer**. The fix is always: separate session for review, reviewer sees artifacts only.
