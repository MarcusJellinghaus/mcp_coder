# Step 5 — Layer 3: thread session params through the commit path

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step exactly as specified in `pr_info/steps/step_5.md`. TDD: extend the tests first, watch them fail, then implement. Run pylint, pytest (fast-unit exclusion markers, `-n auto`) and mypy via the MCP tools; all must pass. Format with `./tools/format_all.sh` and produce exactly one commit for this step.

## WHERE

- `src/mcp_coder/workflow_utils/commit_operations.py` — `generate_commit_message_with_llm`
- `src/mcp_coder/workflow_steps/commit.py` — `commit_changes`
- Callers of `commit_changes`: `src/mcp_coder/workflows/review/core.py:260`, `src/mcp_coder/workflows/implement/core.py:326`, `src/mcp_coder/workflows/implement/task_processing.py:451`, `src/mcp_coder/workflow_steps/ci.py:247`
- Caller of `generate_commit_message_with_llm`: `src/mcp_coder/workflows/implement/finalisation.py:133`
- `src/mcp_coder/cli/commands/commit.py` — comment refresh only (lines 94–96)
- Tests: `tests/workflow_utils/test_commit_operations.py`, `tests/workflow_steps/test_commit.py`

## WHAT (signatures)

```python
def generate_commit_message_with_llm(
    project_dir: Path,
    provider: str = "claude",
    execution_dir: Optional[str] = None,
    mcp_config: Optional[str] = None,
    settings_file: Optional[str] = None,
) -> Tuple[bool, str, Optional[str]]: ...

def commit_changes(
    project_dir: Path,
    provider: str = "claude",
    *,
    mcp_config: str | None = None,
    execution_dir: str | None = None,
    settings_file: str | None = None,
) -> bool: ...
```

## HOW (integration points)

- `generate_commit_message_with_llm`: forward `mcp_config=mcp_config, settings_file=settings_file` to the existing `prompt_llm(...)` call (it already forwards `execution_dir`). `prompt_llm` already accepts both — pure plumbing. Update the docstring; also update the module comment about the call being "pure-LLM": it now runs scoped/hermetic like main sessions.
- `commit_changes`: pass all three params to `generate_commit_message_with_llm`.
- Callers (all values already in scope — do NOT restructure, do NOT introduce a params dataclass; the issue defers that):
  - `review/core.py:260`: `commit_changes(project_dir, provider, mcp_config=mcp_config, execution_dir=execution_dir, settings_file=settings_file)` (same values passed to `_run_reviewer`; convert to `str` if the local type is `Path`).
  - `implement/core.py:326`: same pattern; `execution_dir` is `Optional[Path]` → `str(execution_dir) if execution_dir else None`.
  - `implement/task_processing.py:451`: pass `mcp_config`, `settings_file`, and the same `cwd`/`execution_dir` value used for the step's main `prompt_llm` call (line 367 uses `execution_dir=cwd`).
  - `ci.py:247`: `mcp_config=config.mcp_config, execution_dir=config.cwd, settings_file=config.settings_file` (verify exact attribute names on the config object).
  - `finalisation.py:133`: add `mcp_config=` and `settings_file=` to the existing call (it already passes `execution_dir`); thread them from `run_finalisation`'s scope (they are available per the issue; verify signature).
- `cli/commands/commit.py`: keep `mcp_config=None` (interactive discovery mode is intentional; layer 1 covers it). Refresh the stale comment at lines 94–96: discovery mode is a deliberate choice for the interactive command, not "not applicable".

## DATA

- No behavior change when the new params are `None` (all defaults) — existing tests must pass unmodified except where they assert call kwargs.

## TESTS (write first)

- `test_commit_operations.py`: `generate_commit_message_with_llm(..., mcp_config="cfg.json", settings_file="s.json", execution_dir="/x")` forwards exactly those kwargs to the mocked `prompt_llm`.
- `test_workflow_steps/test_commit.py`: `commit_changes(..., mcp_config=..., execution_dir=..., settings_file=...)` forwards them to the mocked `generate_commit_message_with_llm`.
- One representative caller test (extend an existing `review/core` or `ci` test's mock assertion). Do NOT add kwarg-assertion tests for every caller — mypy and existing mocks cover the one-line additions.

## Commit

`fix: thread mcp_config/execution_dir/settings_file through workflow commit path (#1090)`
