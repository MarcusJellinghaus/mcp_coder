# Step 2 — GIT / GITHUB / GITHUB SECURITY sections from mcp-workspace

Read [summary.md](summary.md) first. Requires step 1 (one `Row` class). One commit.

## LLM prompt

> Implement step 2 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_2.md`.
> First retarget the test fixtures and the two kept wiring tests to the new names (they
> fail), then switch `verify.py` to the mcp-workspace section formatters and
> `github_security_rows`, delete the local git/GitHub/security code and the tests that
> moved upstream, and move `pyyaml` to the test extra. GIT, GITHUB and GITHUB SECURITY
> output must stay byte-identical. Run pylint, pytest (`-n auto`, fast unit markers),
> mypy, ruff, lint-imports, tach, vulture, deptry; format; commit.

## Precondition

`mcp_workspace.cli.verify_formatting` exports `format_git_section`, `format_github_section`,
`format_github_security_section`, and `mcp_workspace.github_operations` exports
`github_security_rows`. If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- Modify (src): `src/mcp_coder/mcp_workspace.py`, `src/mcp_coder/mcp_workspace_github.py`,
  `cli/commands/verify.py`, `cli/commands/verify_formatting.py`, `cli/commands/verify_sections.py`
- Modify (tests): `tests/cli/commands/conftest.py`, `test_verify_format_section_basic.py`,
  `test_verify_github_security_section.py`, `test_verify_label_map.py`
- Delete (tests): `tests/cli/commands/test_verify_sections_security.py`,
  `tests/cli/commands/test_verify_github_security_probe.py`
- Modify (config): `pyproject.toml`, `vulture_whitelist.py`

## WHAT

### Shims

`src/mcp_coder/mcp_workspace.py` — add (and list in `__all__`):

```python
from mcp_workspace.cli.verify_formatting import (
    format_git_section, format_github_section, format_github_security_section,
)
```

`src/mcp_coder/mcp_workspace_github.py` — add `github_security_rows` to the
`mcp_workspace.github_operations` import and `__all__` (Verification group).
Remove `verify_github_security` from the import and from `__all__`: its only `src` caller
(`verify_sections._print_github_security_section`) is deleted in this step and the conftest
patch moves to `github_security_rows`.

### `verify.py`

```python
from ...mcp_workspace import format_git_section, format_github_section, format_github_security_section
from ...mcp_workspace_github import github_security_rows, verify_github

out.section("GIT", format_git_section(git_result, symbols))
out.section("GITHUB", format_github_section(github_result, symbols))
out.section("GITHUB SECURITY", format_github_security_section(github_security_rows(project_dir), symbols))
```

Drop the `_print_github_security_section` import. Git/GitHub exit logic unchanged.

### `verify_formatting.py`

- `_LABEL_MAP`: delete the "GitHub section", "GitHub security section" and "Git section"
  entries. Claude, LangChain, MCP adapter, Ollama, MLflow, Jenkins entries stay.
- Delete `_BRANCH_PROTECTION_CHILDREN`.
- `_format_section`: keep only the generic loop (skip `overall_ok` / non-dict entries;
  label via `_LABEL_MAP`; marker from `ok`; `value (error)` when `ok is False`; indent 2;
  `-> install_hint` hint when `ok is False`). Remove `bp_ok`, the branch-protection branch,
  the `[Permissions]` header, `perm_` indent and the `token_configured` hint.

### `verify_sections.py`

Delete `_print_github_security_section`, `_map_security_row`, `_NOT_ACCESSIBLE`,
`_check_dependabot_config`, `_check_codeql_workflow`, `_workflow_uses_codeql`,
`_schedule_interval`, `_CODEQL_ACTION_PREFIX`, `import yaml`, `from collections.abc import Mapping`
if unused, and the `CheckResult` / `verify_github_security` imports. Update the module docstring
if it mentions security.

## HOW

- `pyproject.toml`: remove `"pyyaml>=6.0"` from `dependencies`, add it to the `test` extra
  (`tests/cli/commands/test_define_labels_actions.py` imports `yaml`). Keep `types-PyYAML`.
- `vulture_whitelist.py`: `_._mock_verify_github_security` → `_._mock_github_security_rows`;
  delete `_.security_and_analysis`.

## Tests (write first)

- `tests/cli/commands/conftest.py`: rename `_mock_verify_github_security` →
  `_mock_github_security_rows`, patching `mcp_coder.cli.commands.verify.github_security_rows`
  with all seven keys in display order (`dependabot_config`, `dependabot_alerts`,
  `dependabot_security_updates`, `secret_scanning`, `secret_scanning_push_protection`,
  `codeql_workflow`, `code_scanning_alerts`), each `{"ok": True, "value": ..., "severity": "warning"}`.
- `test_verify_github_security_section.py`: keep only `test_section_is_exit_neutral_when_all_rows_fail`,
  retargeted to the `_mock_github_security_rows` fixture (all seven rows `ok=False`;
  `execute_verify` still returns 0 and prints `=== GITHUB SECURITY`). Delete the other tests
  and unused helpers.
- Keep the `token_source` hint wiring tests in `tests/cli/commands/test_verify.py`
  (`test_token_source_env_renders_second_line`, `test_token_source_config_renders_second_line`)
  unchanged — they now pass through upstream `format_github_section`.
- `test_verify_format_section_basic.py`: delete `TestBranchProtectionNesting`,
  `TestGitHubLabelMappings`, `TestGitLabelMappings`, `TestAutoDeleteBranches`,
  `TestApiBaseUrlRendering`, `TestTokenFingerprintSuffix`, `TestPermissionProbes`; keep
  `TestFormatSection`.
- `test_verify_alignment.py::TestPerFormatterAlignment::test_format_section`: remove the
  `branch_protection_with_strict_mode_no_marker` and `permissions_group` params (that
  behaviour is now tested upstream; ported tests are deleted, not kept twice). The other
  params stay.
- `test_verify_label_map.py::test_renamed_labels`: drop the `signing_consistency` assert.
- Delete `test_verify_sections_security.py` and `test_verify_github_security_probe.py`.
- Search `tests/` for `_print_github_security_section`, `_map_security_row`,
  `_check_dependabot_config`, `_check_codeql_workflow`, `verify_sections.verify_github_security`,
  `_BRANCH_PROTECTION_CHILDREN` and fix any remaining reference.
- Search `src/` and `tests/` for `verify_github_security` (imports and patch-target strings,
  e.g. `mcp_workspace_github.verify_github_security`): nothing may still point to the removed
  shim name.

## ALGORITHM

None — delegation to upstream formatters.

## DATA

`github_security_rows(project_dir) -> dict[str, CheckResult]` (seven keys, warning severity,
exit-neutral). `format_*_section(result, symbols) -> list[Line]`.
