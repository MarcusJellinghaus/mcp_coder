# Step 1: Fix `_parse_groups()` to Capture All Lines Between Groups

## Context
See [summary.md](./summary.md) for full architectural overview.

`_parse_groups()` only captures `##[error]` lines after `##[endgroup]`. All other command output is dropped. The fix removes the `##[error]`-only guard so all lines between groups are attached to the preceding group.

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement step 1: fix _parse_groups() in src/mcp_coder/checks/ci_log_parser.py
to capture all lines between ##[endgroup] and the next ##[group] marker,
not just ##[error] lines.

Update the docstring to reflect the new behavior.
Run pylint, mypy, and pytest to confirm all checks pass.
```

---

## WHERE

| Item | Path |
|------|------|
| Fix location | `src/mcp_coder/checks/ci_log_parser.py` — `_parse_groups()` |

No new files in this step.

---

## WHAT

### Current code (lines 61-65)

```python
elif groups:
    # Lines after ##[endgroup] – capture ##[error] lines
    if line.startswith("##[error]"):
        label, lines_so_far = groups[-1]
        groups[-1] = (label, lines_so_far + [line])
```

### Target code

```python
elif groups:
    # Lines after ##[endgroup] – attach to preceding group
    label, lines_so_far = groups[-1]
    groups[-1] = (label, lines_so_far + [line])
```

### Docstring updates

1. Update the `_parse_groups()` docstring to state that **all** lines after `##[endgroup]` (not just `##[error]`) are attached to the preceding group.
2. Update the `_extract_failed_step_log()` docstring (line 87): change "Lines starting with `##[error]` immediately after `##[endgroup]` are included" to reflect that **all** lines after `##[endgroup]` are now included.

---

## DONE WHEN

- [ ] `_parse_groups()` captures all lines between `##[endgroup]` and next marker
- [ ] Both docstrings updated (`_parse_groups` and `_extract_failed_step_log`)
- [ ] `pylint`, `mypy`, `pytest` all pass (existing tests still green)
