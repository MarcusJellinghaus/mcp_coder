# Step 5 — `llm_permissions` and the granted implement / finalisation / CI-fix sessions

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 10 (grant sets
and sessions) and 12. Depends on Step 4 (`prompt_llm(bash_grants=...)`).

## LLM prompt

> Implement Step 5 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_5.md`: add `llm_permissions` / `bash_grants_of` to
> `mcp_coder.utils.toolkit_runner` and pass Bash grants to the implement task
> call, the mypy fix call, finalisation and `_run_ci_fix` (TDD — tests first).
> Rebase is Steps 6–7. Run the code-quality checks from CLAUDE.md and make exactly
> one commit.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py` — two new functions + one module flag.
- `src/mcp_coder/workflows/implement/task_processing.py` — the `prompt_llm`
  calls in `process_single_task` (implement task) and `check_and_fix_mypy`.
- `src/mcp_coder/workflows/implement/finalisation.py` — `run_finalisation`.
- `src/mcp_coder/workflow_steps/ci.py` — `_run_ci_fix` only (not `_run_ci_analysis`).
- Tests: new `tests/utils/test_toolkit_permissions.py`; extend the existing
  tests of the three workflow modules.

## WHAT

```python
_bash_drop_warned = False  # module flag: warn once per process

def llm_permissions(project_dir: Path, provider: str, entry: str | None = None) -> list[str]:
    """Permission strings the LLM session gets from the loaded toolkit."""

def bash_grants_of(permissions: Sequence[str]) -> list[str]:
    """Only the Bash(...) entries."""
```

## ALGORITHM

```
try: loaded = load_toolkit(project_dir)
except ValueError as e: logger.warning("No toolkit grants: %s", e); return []
perms = loaded.info.llm_permissions
if entry is None: pairs = all (action, depth) in perms
else: pairs = [(a, _resolve_depth(loaded.info.actions.get(a, []), d)) for a@d in bindings[entry]] (skip None)
out = dedupe-in-order of perms[a][d] for pairs
if provider != "claude" and any Bash( in out: warn once ("Bash grants dropped for provider X"); drop Bash( entries
return out
```

- Use the same provider default as `prompt_llm`: callers pass their resolved
  provider string; treat `provider or os.environ.get("MCP_CODER_LLM_PROVIDER") or "claude"`.
- Warning text names the provider and says checks are not re-runnable by the LLM.

## HOW (call sites)

Each call site, right before `prompt_llm`:
```python
bash_grants = bash_grants_of(llm_permissions(project_dir, provider))
prompt_llm(..., bash_grants=bash_grants)
```
- `ci.py::_run_ci_fix`: `config.project_dir`, `config.provider`. All CI-fix
  callers (implement, review CI step, `fix_ci`, `check-branch-status`) go
  through `_run_ci_fix`, so no caller changes.
- Plan, review (except its CI fix), PR, commit-message and `_run_ci_analysis`
  sessions are not touched.

## DATA

`list[str]`, e.g. `["mcp__mcp-tools-py__run_mypy_check", ...]` for
`PythonToolkit` (so `bash_grants_of` → `[]`, the CLI command is unchanged), or
`["Bash(npm run lint)", "Bash(npm test)"]` for `command`.

## Tests

`tests/utils/test_toolkit_permissions.py` (patch `_toolkit_class` to a small
fake `Toolkit` or `CommandToolkit` with a `mcp-coder.toml` in `tmp_path`):
- union over all actions/depths, deduplicated, `entry=None`;
- `entry="rebase"` with only `check.quick` declared → the `quick` grants (resolved depth);
- `PythonToolkit` → no `Bash(` entries (`bash_grants_of` empty);
- provider `copilot` / `langchain`: `Bash(` dropped, MCP names kept, warning
  logged once across two calls (reset the flag via `monkeypatch.setattr`);
  no warning when nothing was dropped;
- load failure → `[]` and a warning.

Workflow tests (mock `prompt_llm` and `llm_permissions`):
- implement task, mypy fix, finalisation, `_run_ci_fix` pass `bash_grants`;
- `_run_ci_analysis` does not pass `bash_grants`.
