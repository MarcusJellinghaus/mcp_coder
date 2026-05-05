# Step 1 — Render `[Permissions]` subsection from `perm_*` `CheckResult` rows

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_1.md`) before starting. Implement the changes in TDD order: extend the `_GITHUB_KEYS` test invariant first, write the new `TestPermissionProbes` unit tests and the orchestration test, then update `_LABEL_MAP` and `_format_section` until everything passes. Run pylint, pytest (with `-n auto` and the standard `not <integration>` exclusions per CLAUDE.md), and mypy after the implementation. Single commit.

## WHERE

| File | Section |
|---|---|
| `src/mcp_coder/cli/commands/verify.py` | `_LABEL_MAP` (around line 217-247) and `_format_section` (around line 254-295) |
| `tests/cli/commands/test_verify_format_section_basic.py` | `TestGitHubLabelMappings._GITHUB_KEYS` tuple (around line 184-196); append a new `TestPermissionProbes` class at end of file |
| `tests/cli/commands/test_verify_orchestration.py` | Append one new test inside `TestVerifyOrchestration` (alongside `test_github_section_renders_diagnostics` at line 520) |

## WHAT

### `_LABEL_MAP` additions (verify.py)

Append these 6 entries at the end of the GitHub section block (after `"auto_delete_branches"`), preserving upstream insertion order:

```python
"perm_contents_read":       "Contents: Read",
"perm_administration_read": "Administration: Read",
"perm_pull_requests_read":  "Pull requests: Read",
"perm_issues_read":         "Issues: Read",
"perm_workflows_read":      "Actions: Read",
"perm_statuses_read":       "Commit statuses: Read",
```

No other dict entries change.

### `_format_section` changes (verify.py)

Signature unchanged:

```python
def _format_section(title: str, result: dict[str, Any], symbols: dict[str, str]) -> str
```

Add a local `permissions_header_emitted: bool = False` initialized before the loop. Inside the loop, in the **generic-row handler** (i.e. the path reached *after* the `branch_protection` children `continue` block), insert this check **before** computing the symbol/value for the row:

```python
if key.startswith("perm_") and not permissions_header_emitted:
    lines.append("")
    lines.append("  [Permissions]")
    permissions_header_emitted = True
```

Then render the row at `indent=4` for `perm_*` keys instead of the default `indent=2`. Pass through the existing `error` suffix path (`f"{value} ({error})"` when `ok is False and error`) so the upstream-constructed 404-hint URL renders verbatim.

### Test additions

**`tests/cli/commands/test_verify_format_section_basic.py`:**

1. Grow `_GITHUB_KEYS` tuple to 17 entries (append the 6 `perm_*` keys at the end). The existing `test_all_github_keys_in_label_map` then enforces that every new key has a label.

2. New class `TestPermissionProbes` with exactly 2 tests:

```python
class TestPermissionProbes:
    """Tests for [Permissions] subsection rendering (#946)."""

    def _symbols(self) -> dict[str, str]: ...

    @pytest.mark.parametrize("scenario, ...", [
        # all-ok: every perm_* row renders [OK] OK
        # one-missing: perm_workflows_read renders [ERR] with error substring; others [OK]
        # repo-inaccessible: all 6 render [ERR] with "not checked" + "repository not accessible"
    ])
    def test_perm_rows_rendered(self, ...) -> None: ...

    def test_header_appears_once_and_after_auto_delete_branches(self) -> None:
        # output.count("[Permissions]") == 1
        # output.find("Auto-delete branches") < output.find("[Permissions]")
```

**`tests/cli/commands/test_verify_orchestration.py`:**

Inside `TestVerifyOrchestration`, add one new test (model after `test_github_section_renders_diagnostics` at line 520):

```python
def test_github_section_renders_permission_probes(self, ...) -> None:
    """[Permissions] subsection reaches end-to-end rendered output."""
    # Inline a github_with_permissions dict containing the 6 perm_* keys
    # (mix of ok=True and one ok=False), patch verify_github to return it,
    # call execute_verify, assert "[Permissions]" and "Actions: Read" appear.
```

Inline the dict — do **not** add a `_github_ok()` / `_github_fail()` helper. Matches the existing inline pattern at line 534.

## HOW (integration points)

- No new imports in `verify.py` (uses existing `lines.append`, `_format_row`).
- New tests import the same symbols already imported by their respective files (`_format_section`, `_format_row`, `execute_verify`).
- `pytest.mark.parametrize` already imported in `test_verify_format_section_basic.py`.
- No fixtures added; tests use the same `_symbols()` helper convention as neighboring classes.

## ALGORITHM (core logic in `_format_section`)

```
permissions_header_emitted = False
for key, entry in result.items():
    ... existing skip / branch_protection handling ...
    # Generic-row path (reached after branch_protection children `continue`):
    if key.startswith("perm_") and not permissions_header_emitted:
        lines.append("")
        lines.append("  [Permissions]")
        permissions_header_emitted = True
    indent = 4 if key.startswith("perm_") else 2
    ... existing symbol/value/error rendering ...
    lines.append(_format_row(label, symbol, row_value, indent=indent))
```

## DATA

- **`_LABEL_MAP`**: same `dict[str, str]`, +6 entries, no removals.
- **`_format_section` return value**: same `str` shape; rendered output gains a blank line + `"  [Permissions]"` header + 0..6 rows of form `"    <label>          <symbol>  <value>"` at indent 4.
- **No new public symbols, no new module-level constants, no API changes.**

## Definition of done

- `mcp__tools-py__run_pylint_check` passes.
- `mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])` passes.
- `mcp__tools-py__run_mypy_check` passes.
- One commit covering verify.py + both test files.
