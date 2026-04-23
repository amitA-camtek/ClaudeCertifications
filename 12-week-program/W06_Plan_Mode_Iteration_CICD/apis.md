# W06 APIs — Claude APIs for this week

> APIs relevant to **plan mode, iteration, and CI/CD**, with runnable examples and step-by-step run/debug instructions.

---

## APIs covered this week

| API | What it's for | Where used |
|---|---|---|
| **Claude Code CLI headless mode** — `claude -p "prompt"` | One-shot non-interactive run | CI steps |
| **`--output-format json`** | Machine-readable response | Piping to `jq`, parsing in CI |
| **`--permission-mode plan`** | Start in plan mode (plan without executing) | Sanity-check before execution on big changes |
| **`--session-id`** / **`--resume`** | Correlate or resume a CI run | Multi-step CI flows |
| **Messages API `system` param + separate `client` instances** | Context isolation: generator and reviewer are two independent calls | Self-review anti-pattern fix |
| **Message Batches API** (contrast) — `client.messages.batches.create()` | For NON-blocking bulk work; **not** for PR gates | Decide sync-vs-batch in CI |

---

## API snippets

### Headless, JSON output
```bash
claude -p "Summarize the diff on HEAD~1..HEAD in 3 bullets." \
  --output-format json \
  --permission-mode default \
  > out.json
```

### Start in plan mode
```bash
claude -p "Migrate all 45 call sites of deprecated_fn to new_fn." \
  --permission-mode plan \
  --output-format json \
  > plan.json
```
In plan mode Claude builds a plan; nothing executes until you review and approve.

### Two independent Messages-API calls (generator + reviewer)
```python
import anthropic
client = anthropic.Anthropic()

# generator session: produces code
gen = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Write a retry wrapper for httpx..."}],
)
generated_code = gen.content[0].text

# reviewer: DIFFERENT call, fresh messages[], cannot see generator's reasoning
rev = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    system="You are a code reviewer. Be skeptical. List concrete regressions only.",
    messages=[{"role": "user", "content": f"Review this code:\n\n{generated_code}"}],
)
print(rev.content[0].text)
```

---

## Working example — CI script with generator + independent reviewer

Save as `ci_review.py`:

```python
"""
CI pattern: generate a change summary in one session, review in a separate fresh session,
emit a JSON report. Exits non-zero if reviewer flags issues.
"""
import anthropic, json, subprocess, sys

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-5"

def get_diff() -> str:
    result = subprocess.run(["git", "diff", "HEAD~1..HEAD"], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"git diff failed: {result.stderr}")
    return result.stdout or "(no changes)"

def generator(diff: str) -> str:
    """Summarize the diff — this is the 'writer' turn."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a developer summarizing a git diff. "
            "Output: a numbered list of concrete changes with file paths."
        ),
        messages=[{"role": "user", "content": f"Diff:\n```diff\n{diff}\n```"}],
    )
    return resp.content[0].text

def reviewer(diff: str, generator_summary: str) -> dict:
    """Independent reviewer — FRESH messages[], fresh system prompt."""
    review_prompt = (
        f"Generator's summary:\n{generator_summary}\n\n"
        f"Actual diff:\n```diff\n{diff}\n```\n\n"
        "Respond with JSON: "
        '{"issues": [{"severity":"high|med|low","file":"...","desc":"..."}], '
        '"verdict": "ok|needs_changes"}'
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are an independent code reviewer. You have not written this code. "
            "Identify regressions only. Output valid JSON and nothing else."
        ),
        messages=[{"role": "user", "content": review_prompt}],
    )
    text = resp.content[0].text.strip()
    # Strip markdown fences if any
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json\n"):
            text = text[5:]
    return json.loads(text)

def main():
    diff = get_diff()
    print(f"[gen] summarizing {len(diff)} chars of diff...")
    summary = generator(diff)
    print(f"[gen] summary: {summary[:200]}...")

    print("[rev] independent review (fresh session)...")
    review = reviewer(diff, summary)

    report = {
        "summary": summary,
        "review": review,
    }
    with open("ci_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"[rev] verdict: {review.get('verdict')}, issues: {len(review.get('issues', []))}")
    if review.get("verdict") == "needs_changes":
        print("REVIEWER FLAGGED ISSUES — blocking merge:")
        for issue in review.get("issues", []):
            print(f"  [{issue['severity']}] {issue['file']}: {issue['desc']}")
        sys.exit(1)
    print("REVIEW PASSED")

if __name__ == "__main__":
    main()
```

---

## How to run

**Setup:**
```bash
pip install anthropic
```

**Set API key (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Run in a git repo with at least one commit:**
```bash
python ci_review.py
```

**Expected:**
- `ci_report.json` written.
- Exit code 0 if reviewer passes, 1 if flagged.
- Ready to drop into a GitHub Actions step as a blocking check.

---

## How to debug

| Symptom | Likely cause | Fix |
|---|---|---|
| `json.JSONDecodeError` on reviewer output | Reviewer wrapped JSON in ```json``` fences | The `strip fences` block handles common cases; if custom fence, widen the strip logic |
| Reviewer never finds issues | Too lenient system prompt | Tighten: "Be skeptical. Assume the code has bugs until proven otherwise." |
| Reviewer finds *everything* as an issue | Too harsh prompt or no severity gate | Add: "Only flag `high` for data-integrity or security; `low` is style." |
| Generator and reviewer agree suspiciously | Same model, same training — still susceptible to shared blind spots | Use different prompts; add specific checklists to the reviewer |
| Git diff is empty | On the first commit, or wrong range | Use `git log --oneline` to find the right range; handle empty-diff case |
| CI flakes on rate limit | Many PRs in parallel | Add retry-with-backoff around `messages.create`; stagger CI jobs |

**Plan-mode smoke test (standalone):**
```bash
claude -p "List the files in this directory and propose a rename scheme." \
  --permission-mode plan \
  --output-format json | jq .
```
Should return a plan without touching any file.

---

## When to use Message Batches instead (decision table)

| Situation | Sync | Batch |
|---|---|---|
| PR pre-merge review (blocks merge) | ✅ | ❌ no SLA |
| Nightly full-repo scan | ❌ overspend | ✅ 50% off |
| Interactive chat | ✅ | ❌ |
| Backfill 100k records overnight | ❌ | ✅ |
| Multi-turn tool-using agent | ✅ | ❌ single-turn only |

---

## Exam connection

- **Generator + reviewer as separate sessions** is the fix for the "same session writes and reviews" exam distractor. This example shows how in code.
- **Plan mode for a 45-file migration** is a direct exam question type — use `--permission-mode plan`.
- **Sync vs batch**: CI blocking → sync; overnight → batch. The exam tests the SLA/window tradeoff.
