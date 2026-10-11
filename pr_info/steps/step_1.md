# Step 1 — Suppress branch-protection children when the parent is unverifiable

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` using TDD:
> write the test first, confirm that it fails, then make the one-line fix. Run pylint,
> pytest (fast unit tests, `-n auto`) and mypy, run the formatter, and commit.

## WHERE

- `tests/cli/commands/test_verify_format_section_basic.py`, class `TestBranchProtectionNesting`
- `src/mcp_coder/cli/commands/verify_formatting.py`, `_format_section` (around line 211)

## WHAT

### Test (write first)

`TestBranchProtectionNesting.test_children_suppressed_when_parent_unverifiable(self) -> None`.
This is the 403 case.

Also prefix the docstrings of the two existing tests with their status codes (no logic change):
- `test_children_indented_when_parent_ok`: "200: Children render …"
- `test_children_suppressed_when_parent_fails`: "404: Only parent line appears …"

### Implementation

In `_format_section`:

```python
elif key in _BRANCH_PROTECTION_CHILDREN:
    if bp_ok is not True:
        continue  # suppress children when parent failed or is unverifiable
```

## DATA — 403 test payload (upstream's real shape)

```python
value = "not verifiable — token lacks Administration: Read"
error = "get_protection failed: HTTP 403: Resource not accessible by personal access token"
row = {"ok": None, "value": value, "error": error, "severity": "warning"}
result = {
    "branch_protection": dict(row),
    "ci_checks_required": dict(row),
    "strict_mode": dict(row),
    "force_push": dict(row),
    "branch_deletion": dict(row),
    "overall_ok": True,
}
```

## ALGORITHM — test assertions

```
output = _format_section("GITHUB", result, symbols)
parent line contains "[WARN]" and "not verifiable"
"[ERR]" not in output; "not configured" not in output; "Resource not accessible" not in output
"CI checks required", "Strict mode", "Force push", "Branch deletion" not in output
```

## Commit

`fix(verify): suppress branch-protection children when parent is unverifiable`
