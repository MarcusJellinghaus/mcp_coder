# Step 1: Tests for nested branch protection rendering

**Reference:** [summary.md](summary.md)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this step file. Add tests to `tests/cli/commands/test_verify_format_section.py` for branch protection nested rendering in `_format_section`. Tests should cover: (1) children render at 4-space indent when parent ok=True, (2) children are suppressed when parent ok=False, (3) strict_mode renders without a status symbol, (4) non-GitHub sections remain unaffected. All tests should initially fail (TDD red phase). Run pylint, pytest, and mypy checks after — tests are expected to fail at this stage.

## WHERE

- `tests/cli/commands/test_verify_format_section.py` — add a new `TestBranchProtectionNesting` class

## WHAT

New test class with these test methods:

| Method | Purpose |
|--------|---------|
| `test_children_indented_when_parent_ok` | Children render at 4-space indent under parent |
| `test_children_suppressed_when_parent_fails` | Only parent line appears when `ok=False` |
| `test_strict_mode_no_symbol` | `strict_mode` renders value only — no `[OK]`/`[ERR]`/`[WARN]` |
| `test_non_github_section_unaffected` | Claude section entries remain flat at 2-space indent |

## HOW

- Import `_format_section` (already imported in the file)
- Each test builds a `result` dict mimicking `verify_github()` output shape
- Call `_format_section("GITHUB", result, symbols)` and assert on the output string

## DATA

Test input — parent OK with children:
```python
result = {
    "branch_protection": {"ok": True, "value": "main protected"},
    "ci_checks_required": {"ok": True, "value": "8 checks configured"},
    "strict_mode": {"ok": True, "value": "enabled"},
    "force_push": {"ok": True, "value": "disabled"},
    "branch_deletion": {"ok": True, "value": "disabled"},
    "overall_ok": True,
}
```

Test input — parent failed:
```python
result = {
    "branch_protection": {"ok": False, "value": "main is not protected"},
    "ci_checks_required": {"ok": False, "value": "unknown", "error": "no protection"},
    "strict_mode": {"ok": False, "value": "unknown", "error": "no protection"},
    "force_push": {"ok": False, "value": "unknown", "error": "no protection"},
    "branch_deletion": {"ok": False, "value": "unknown", "error": "no protection"},
    "overall_ok": False,
}
```

Expected output assertions (parent OK):
- `"  Branch protection    [OK] main protected"` — 2-space indent (parent)
- `"    CI checks required [OK] 8 checks configured"` — 4-space indent (child)
- `"    Strict mode          enabled"` — 4-space, no symbol
- `"    Force push         [OK] disabled"` — 4-space indent (child)
- `"    Branch deletion    [OK] disabled"` — 4-space indent (child)

Expected output assertions (parent failed):
- Parent line present
- None of `ci_checks_required`, `strict_mode`, `force_push`, `branch_deletion` appear in output

## Commit

```
test: add tests for branch protection nested rendering (#899)
```
