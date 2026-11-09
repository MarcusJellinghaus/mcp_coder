# Step 5 — Rebase: `[test_filter]` rename and allowlist from `llm_permissions`

See `pr_info/steps/summary.md` ("Rebase allowlist").

## LLM prompt

> Implement Step 5 of `pr_info/steps/summary.md` as described in `pr_info/steps/step_5.md`.
> Write/update the tests first. An explicit `--settings` override must still replace the
> generated settings entirely. Run pylint, mypy and pytest; all must pass. The step is done
> when the all-prompts scan test (see Tests) passes.

## WHERE

- `src/mcp_coder/prompts/prompts.md` ("Rebase Regression Fix" description + template)
- `src/mcp_coder/workflows/rebase_prompt.py` (regex, `_marker_filter_text` docstring)
- `src/mcp_coder/workflows/rebase.py` (replacement key)
- `src/mcp_coder/workflows/rebase_permissions.py`
- `src/mcp_coder/workflows/rebase_automated.py` (`rebase_with_llm_fallback`)
- `src/mcp_coder/cli/commands/rebase.py` (`execute_rebase`, `_resolve_rebase_settings` docstring)
- Tests: `tests/workflows/rebase/test_rebase_permissions.py`, `test_llm_steps.py`,
  `test_prompt.py`, `test_workflow_regression.py`; `tests/cli/commands/test_rebase.py`.

## WHAT — prompt rename

- Template: `[pytest_marker_filter]` → `[test_filter]`; placeholder list in the description
  updated.
- Description: drop "modeled on the Mypy Fix Prompt"; e.g. "The regression-fix prompt for
  the Python-driven rebase: Python inlines the concrete failure keys and the check output,
  ..." ("Python-driven"/"Python program" refer to mcp-coder itself and stay).
- `rebase_prompt._REGRESSION_PLACEHOLDERS`: `pytest_marker_filter` → `test_filter`.
- `rebase.py`: key `"pytest_marker_filter"` → `"test_filter"`.

## WHAT — permissions

```python
_WORKSPACE_TOOLS: tuple[str, ...] = (
    "mcp__mcp-workspace__git",
    "mcp__mcp-workspace__get_base_branch",
    "mcp__mcp-workspace__read_file",
    "mcp__mcp-workspace__save_file",
    "mcp__mcp-workspace__edit_file",
    "mcp__mcp-workspace__append_file",
    "mcp__mcp-workspace__delete_this_file",
    "mcp__mcp-workspace__list_directory",
    "mcp__mcp-workspace__search_files",
)

def rebase_settings(project_dir: Path, entry: str) -> dict[str, Any]: ...

@contextmanager
def rebase_settings_file(
    project_dir: Path, entry: str, override: str | None = None
) -> Iterator[str]: ...
```

`REBASE_LLM_PERMISSIONS` is removed (replaced by `rebase_settings`).

## HOW

- `rebase_settings` imports `bash_grants_of`, `llm_permissions` from
  `mcp_coder.utils.toolkit_runner`; provider hard-coded `"claude"` (Copilot ignores
  `settings_file`).
- `cli/commands/rebase.py`: `rebase_settings_file(project_dir, "rebase", explicit_settings)`.
- `rebase_automated.py`: `rebase_settings_file(project_dir, "rebase_automated",
  settings_override)` (covers `fix_conflict/core.py` and `review/steps.py`, which go
  through `rebase_with_llm_fallback`).
- Module docstring: describe the generated allowlist (fixed `mcp-workspace` tools + the
  binding's non-Bash grants; Bash grants reach fix turns via `--allowedTools`, conflict turns
  get none; no `run_format_code` because `run_formatters` runs after each fix turn); remove
  "unchanged (#1197)".

## ALGORITHM

```
perms = llm_permissions(project_dir, "claude", entry)
extra = [p for p in perms if p not in bash_grants_of(perms)]
allow = list(_WORKSPACE_TOOLS) + [p for p in extra if p not in _WORKSPACE_TOOLS]
servers = ["mcp-workspace"] + sorted({p.split("__")[1] for p in extra if p.startswith("mcp__")} - {"mcp-workspace"})
return {"permissions": {"allow": allow}, "enableAllProjectMcpServers": True, "enabledMcpjsonServers": servers}
```

`rebase_settings_file`: override given → yield it unchanged; else dump
`rebase_settings(project_dir, entry)` to a temp JSON file, yield, delete (as today).

## DATA

Settings dict shape unchanged:
`{"permissions": {"allow": [...]}, "enableAllProjectMcpServers": True, "enabledMcpjsonServers": [...]}`.

## Tests

- `test_rebase_permissions.py`:
  - Python-style toolkit (patched `llm_permissions` returning
    `mcp__mcp-tools-py__run_pylint_check` etc.) → those in `allow`, `run_format_code` absent,
    `enabledMcpjsonServers == ["mcp-workspace", "mcp-tools-py"]`;
  - `command`-style toolkit (only `Bash(...)` grants) → no `Bash(` and no `mcp-tools-py`
    in `allow`, servers `["mcp-workspace"]` (rewrite of `test_allow_list_has_no_bash_grants`);
  - `entry` is forwarded to `llm_permissions` with provider `"claude"`;
  - `TestRebaseSettingsFile`: new signature; override yielded unchanged and
    `llm_permissions` not needed; temp file deleted afterwards.
- `tests/cli/commands/test_rebase.py`
  (`test_execute_rebase_passes_args_and_returns_exit_code`): compare against
  `rebase_settings(project_dir, "rebase")` (patched) instead of `REBASE_LLM_PERMISSIONS`.
- `test_llm_steps.py`, `test_prompt.py`, `test_workflow_regression.py`: rename
  `pytest_marker_filter` → `test_filter`.
- All-prompts scan (Done-when guard, in `tests/prompts/`): parametrized over every
  `src/mcp_coder/prompts/*.md` file; fails if a file contains `pylint`, `mypy`, `pytest`
  or `mcp__mcp-tools-py__`, or matches `python project` case-insensitively. Written in this
  step because it can pass only after the `[test_filter]` rename.
