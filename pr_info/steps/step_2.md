# Step 2 — Readable **Decisions** field (`format_verdict`)

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **this step only** (`pr_info/steps/step_2.md`).
> TDD: write the tests first, then the code. Run pylint, the fast pytest set and mypy; all
> must pass. Run the formatter before committing. One commit.

## WHERE

- `src/mcp_coder/workflows/review/verdict.py` — new `format_verdict`
- `src/mcp_coder/workflows/review/core.py` — replace every `decisions=str(verdict)`
- `tests/workflows/review/test_verdict.py` — unit tests
- `tests/workflows/review/test_review_log.py` — `write_round_log` integration tests

## WHAT

```python
def format_verdict(verdict: Verdict) -> str:
    """Render a verdict as formatter-stable markdown for the round log.

    The decision on one line; for ``tasks``, a blank line and one ``-`` item per
    task, continuation lines indented by two spaces and blank lines inside a task
    dropped. The escalate reason is left out (``write_round_log`` writes it).
    """
```

## HOW

- `core.py`: import `format_verdict` from `.verdict` next to `Verdict`; replace all ten
  `decisions=str(verdict)` with `decisions=format_verdict(verdict)` (line-neutral).

## ALGORITHM

```
lines = [verdict.decision]
if verdict.tasks: lines.append("")
for task in verdict.tasks:
    parts = [p.strip() for p in task.splitlines() if p.strip()]
    lines.append(f"- {parts[0]}"); lines.extend(f"  {p}" for p in parts[1:])
return "\n".join(lines)
```

## DATA

- `Verdict("dismiss")` → `"dismiss"`
- `Verdict("tasks", ["a", "b\n\nc"])` → `"tasks\n\n- a\n- b\n  c"`
- `Verdict("escalate", escalate_reason="r")` → `"escalate"`

## Tests (write first)

`test_verdict.py`: the three DATA examples above (exact strings), including the
multi-line task with an inner blank line.

`test_review_log.py` (use the existing `_assert_formatter_stable` and `_read` helpers):
- `write_round_log(..., decisions=format_verdict(Verdict("tasks", ["a", "b"])))` → log has
  `**Decisions**:\n\ntasks\n\n- a\n- b\n`, no `Verdict(`, and is formatter-stable.
- escalate verdict with reason `"x"` written with `escalate_reason="x"` → `"x"` appears
  exactly once in the log.
- a multi-line task `"b\nc"` → `"- b\n  c"` in the log.
