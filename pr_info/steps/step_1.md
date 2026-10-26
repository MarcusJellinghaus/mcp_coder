# Step 1 — Register `require_pull_request` and show error notes on unverifiable protection rows

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/Decisions.md`, then implement
> `pr_info/steps/step_1.md` exactly. Write the tests first (cases 1, 2, 3, 4, 6, 7 must
> fail; cases 5, 8 are regression guards that already pass), then the
> implementation. Run pylint, pytest (`-n auto`, fast unit-test marker filter from
> CLAUDE.md) and mypy; all must pass. Run `run_format_code`, then make exactly one
> commit.

## WHERE

- `tests/cli/commands/test_verify_format_section_basic.py`
- `src/mcp_coder/cli/commands/verify_formatting.py`

## WHAT

No new functions. Two constant changes and two condition changes in
`_format_section()`; existing tests are extended and three tests are added.

### Tests first (`test_verify_format_section_basic.py`)

Result dicts use the upstream key order: `require_pull_request` directly after
`branch_protection`, then `ci_checks_required`, `strict_mode`, `force_push`,
`branch_deletion`.

1. `TestGitHubLabelMappings._GITHUB_KEYS`: insert `"require_pull_request"` right
   after `"branch_deletion"` (membership check feeding
   `test_all_github_keys_in_label_map`; order irrelevant there).
2. `TestBranchProtectionNesting.test_children_indented_when_parent_ok`
   (shown when parent OK):
   - add `"require_pull_request": {"ok": True, "value": "required"}` right after
     `branch_protection`;
   - add `"Require pull request"` to the `for child_label in (...)` tuple;
   - assert `_format_row("Require pull request", "[OK]", "required", indent=4) in output`.
3. `test_children_suppressed_when_parent_fails` (hidden, parent `ok=False`):
   - add `"require_pull_request": {"ok": False, "value": "unknown", "error": "no protection"}`
     right after `branch_protection`;
   - assert `"Require pull request" not in output` and
     `"require_pull_request" not in output` (without the registration the row
     leaks under its raw key).
4. `test_children_suppressed_when_parent_unverifiable` (hidden, parent `ok=None`):
   - add `"require_pull_request": dict(row)` right after `branch_protection`;
   - assert `"Require pull request" not in output` and
     `"require_pull_request" not in output`;
   - **flip** `assert "Resource not accessible" not in output` to
     `assert _format_row("Branch protection", "[WARN]", f"{value} ({error})", indent=2) in output`
     (parent now shows its error, Decision 3). Keep the other assertions; update the
     docstring to mention the parent error note.
5. `test_strict_mode_no_symbol` (old-style result, key absent): leave its dict
   unchanged; assert `"Require pull request" not in output` and
   `"require_pull_request" not in output`.
6. New `test_unverifiable_child_shows_error`: parent
   `{"ok": True, "value": "main protected"}`, child
   `"require_pull_request": {"ok": None, "value": "not verifiable — HTTP 403", "error": "rulesets not verifiable: HTTP 403"}`.
   Assert
   `_format_row("Require pull request", "[WARN]", "not verifiable — HTTP 403 (rulesets not verifiable: HTTP 403)", indent=4) in output`.
7. New `test_unverifiable_parent_shows_error`: parent
   `{"ok": None, "value": "not verifiable — HTTP 403", "error": "rulesets not verifiable: HTTP 403"}`,
   plus a non-protection row
   `"auto_delete_branches": {"ok": None, "value": "unknown", "error": "repository not accessible"}`.
   Assert
   `_format_row("Branch protection", "[WARN]", "not verifiable — HTTP 403 (rulesets not verifiable: HTTP 403)", indent=2) in output`
   and `"repository not accessible" not in output` (other `ok=None` rows unchanged).
8. New `test_ok_rows_hide_error`: parent
   `{"ok": True, "value": "main protected (ruleset)", "error": "get_protection failed: HTTP 403"}`,
   child `"require_pull_request": {"ok": True, "value": "required", "error": "get_protection failed: HTTP 403"}`.
   Assert `"get_protection failed" not in output`.

### Implementation (`verify_formatting.py`)

- `_LABEL_MAP`: add `"require_pull_request": "Require pull request",` directly after
  `"branch_protection": "Branch protection",` (GitHub section block).
- `_BRANCH_PROTECTION_CHILDREN`: add `"require_pull_request"` to the frozenset.
- `_format_section()`, generic child branch: change `if error and ok is False:` to
  `if error and ok is not True:`.
- `_format_section()`, generic row branch (after the child branch): change
  `if error and ok is False:` to
  `if error and (ok is False or (ok is None and key == "branch_protection")):`.

## HOW

No new imports or decorators. The `strict_mode` special case stays unchanged
(value only, no marker, no error).

## ALGORITHM

```
for key, entry in result:
    if key == "branch_protection": bp_ok = entry.ok
    elif key in _BRANCH_PROTECTION_CHILDREN:
        if bp_ok is not True: skip
        render child(label, marker, value [+ error if ok is not True], indent=4)
        continue
    render row(label, marker, value
               [+ error if ok is False or (ok is None and key == "branch_protection")],
               indent=2/4)
```

## DATA

Row entry shape emitted upstream (same as the other children):
`{"ok": bool | None, "value": str, "error": str (optional), "severity": "warning"}`.
Rendered lines, e.g.:
- `"    Require pull request   [OK]   required"`
- `"    Require pull request   [WARN] not verifiable — HTTP 403 (rulesets not verifiable: HTTP 403)"`

The label is 20 chars, which fits `_LABEL_WIDTH = 22`.

## Commit

`feat(verify): render require_pull_request row and unverifiable error notes (#1294)`
