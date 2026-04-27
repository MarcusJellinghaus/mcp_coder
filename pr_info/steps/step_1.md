# Step 1 — Render `auto_delete_branches` in GitHub verify section

## Goal

Surface the upstream `auto_delete_branches` check at the top level of the `=== GITHUB ===` verify section by adding a single label-map entry. Lock the behavior in with TDD.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1 exactly as specified, following TDD: write the failing tests first, then add the one-line label-map entry, then run the three mandatory checks (`mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` with `["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`, `mcp__tools-py__run_mypy_check`). Do not modify `_BRANCH_PROTECTION_CHILDREN`, `_format_section` logic, or `_compute_exit_code`. Stage and commit as a single commit after `./tools/format_all.sh` passes.

## WHERE

| File | Action |
|---|---|
| `tests/cli/commands/test_verify_format_section.py` | Modify: extend `_GITHUB_KEYS`; add 2 new test methods. |
| `src/mcp_coder/cli/commands/verify.py` | Modify: add one entry to `_LABEL_MAP`. |

## WHAT

### 1. Test changes (write first, expect failures)

In `tests/cli/commands/test_verify_format_section.py`:

**1a. Extend `TestGitHubLabelMappings._GITHUB_KEYS`:**

Append `"auto_delete_branches"` to the tuple. The existing `test_all_github_keys_in_label_map` will then assert presence in `_LABEL_MAP`.

**1b. Add new test class `TestAutoDeleteBranches`** with two methods:

```python
class TestAutoDeleteBranches:
    """Tests for auto_delete_branches rendering at top level of GITHUB section (#917)."""

    def _symbols(self) -> dict[str, str]:
        return {"success": "[OK]", "failure": "[ERR]", "warning": "[WARN]"}

    @pytest.mark.parametrize(
        "entry, expected_line",
        [
            (
                {"ok": True, "value": "enabled"},
                "  Auto-delete branches [OK] enabled",
            ),
            (
                {"ok": False, "value": "disabled"},
                "  Auto-delete branches [ERR] disabled",
            ),
            (
                {
                    "ok": False,
                    "value": "unknown",
                    "error": "repository not accessible",
                },
                "  Auto-delete branches [ERR] unknown (repository not accessible)",
            ),
        ],
    )
    def test_auto_delete_branches_value_cases(
        self, entry: dict[str, Any], expected_line: str
    ) -> None:
        """Top-level rendering: 2-space indent, symbol from ok, value, optional error suffix."""
        result: dict[str, Any] = {
            "auto_delete_branches": entry,
            "overall_ok": entry["ok"] is True,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert expected_line in output

    def test_renders_when_branch_protection_failed(self) -> None:
        """auto_delete_branches must NOT be suppressed when branch_protection.ok=False."""
        result: dict[str, Any] = {
            "branch_protection": {"ok": False, "value": "main is not protected"},
            "auto_delete_branches": {"ok": True, "value": "enabled"},
            "overall_ok": False,
        }
        output = _format_section("GITHUB", result, self._symbols())
        assert "Auto-delete branches" in output
        assert "[OK] enabled" in output
```

Add `import pytest` if not already present at the top of the test file.

### 2. Implementation change (after tests fail)

In `src/mcp_coder/cli/commands/verify.py`, inside `_LABEL_MAP`, immediately after the `"branch_deletion": "Branch deletion",` line, add:

```python
    "auto_delete_branches": "Auto-delete branches",
```

## HOW (Integration Points)

- **No new imports** in `verify.py`.
- **Test file** may need `import pytest` added (verify before adding).
- **No changes** to `_BRANCH_PROTECTION_CHILDREN` — the new key must NOT be listed there. The default branch in `_format_section` handles top-level rendering automatically.
- **No changes** to `_format_section`, `_compute_exit_code`, or any orchestration logic.

## ALGORITHM

None — this is a data-only change (one dict entry). Existing rendering algorithm in `_format_section` already covers the case:

```
for key, entry in result.items():           # default branch handles new key
    if key not in _BRANCH_PROTECTION_CHILDREN and key != "branch_protection":
        symbol = pick_symbol(entry["ok"])    # [OK] / [ERR] / [WARN]
        line = f"  {label:<20s} {symbol} {value}"
        if error and ok is False: line += f" ({error})"
        lines.append(line)
```

## DATA

- `_LABEL_MAP` gains one `str -> str` entry: `"auto_delete_branches" -> "Auto-delete branches"`.
- No changes to return types of any function.
- Test fixtures use the existing `dict[str, Any]` shape for `result` arguments to `_format_section`.

## Definition of Done

- [ ] Tests written first, observed failing without the label-map entry.
- [ ] One-line addition to `_LABEL_MAP` makes all new tests pass.
- [ ] `mcp__tools-py__run_pylint_check` passes.
- [ ] `mcp__tools-py__run_pytest_check` passes with the standard exclusion args.
- [ ] `mcp__tools-py__run_mypy_check` passes.
- [ ] `./tools/format_all.sh` run before commit.
- [ ] Single commit staged with descriptive message (e.g. `verify: render auto_delete_branches at GitHub section top level`).
