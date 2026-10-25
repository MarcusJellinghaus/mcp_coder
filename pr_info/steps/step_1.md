# Step 1 — Register `require_pull_request` in the verify formatter

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> Write the tests first (cases 1–2 must fail; cases 3–5 are regression guards that
> already pass), then the implementation. Run pylint,
> pytest (`-n auto`, fast unit-test marker filter from CLAUDE.md) and mypy; all must
> pass. Run `run_format_code`, then make exactly one commit.

## WHERE

- `tests/cli/commands/test_verify_format_section_basic.py`
- `src/mcp_coder/cli/commands/verify_formatting.py`

## WHAT

No new functions. Two constant changes, and some existing tests are extended.

### Tests first (`test_verify_format_section_basic.py`)

Cases 1–2 must fail before the implementation. Cases 3–5 are regression guards:
they already pass before the change (an unregistered key prints raw as
`require_pull_request`, so `"Require pull request"` is absent anyway) and must keep
passing after it.

1. `TestGitHubLabelMappings._GITHUB_KEYS`: insert `"require_pull_request"` right
   after `"branch_deletion"` (feeds `test_all_github_keys_in_label_map`).
2. `TestBranchProtectionNesting.test_children_indented_when_parent_ok`
   (shown when parent OK):
   - add `"require_pull_request": {"ok": True, "value": "required"}` to the result
     dict, after `branch_deletion`;
   - add `"Require pull request"` to the `for child_label in (...)` tuple;
   - assert `_format_row("Require pull request", "[OK]", "required", indent=4) in output`.
3. `test_children_suppressed_when_parent_fails` (hidden, parent `ok=False`):
   - add `"require_pull_request": {"ok": False, "value": "unknown", "error": "no protection"}`;
   - assert `"Require pull request" not in output`.
4. `test_children_suppressed_when_parent_unverifiable` (hidden, parent `ok=None`):
   - add `"require_pull_request": dict(row)`;
   - assert `"Require pull request" not in output`.
5. `test_strict_mode_no_symbol` (old-style result, key absent): leave its dict
   unchanged; assert `"Require pull request" not in output` and
   `"require_pull_request" not in output`.

### Implementation (`verify_formatting.py`)

- `_LABEL_MAP`: add `"require_pull_request": "Require pull request",` directly after
  `"branch_deletion": "Branch deletion",` (GitHub section block).
- `_BRANCH_PROTECTION_CHILDREN`: add `"require_pull_request"` to the frozenset.

## HOW

No new imports or decorators. `_format_section()` picks up the key via the existing
`elif key in _BRANCH_PROTECTION_CHILDREN:` branch (generic child rendering, not the
`strict_mode` special case).

## ALGORITHM

Existing logic, unchanged:

```
for key, entry in result:
    if key == "branch_protection": bp_ok = entry.ok
    elif key in _BRANCH_PROTECTION_CHILDREN:
        if bp_ok is not True: skip
        render row(label, marker from ok, value [+ error if ok False], indent=4)
```

## DATA

Row entry shape emitted upstream (same as the other children):
`{"ok": bool | None, "value": str, "error": str | None, "severity": "warning"}`.
Rendered line: `"    Require pull request   [OK]   required"` (via `_format_row`).
The label is 20 chars, which fits `_LABEL_WIDTH = 22`.

## Commit

`feat(verify): render require_pull_request branch protection row (#1294)`
