# Step 1 — Python core: `claude_settings.py` + wire into `env.py` + tests

> Read `pr_info/steps/summary.md` first, then this step.

## Goal

Establish the single Python source of truth for `MCP_TIMEOUT` and make `prepare_llm_environment()` set the env var (with parent-env override). Mirror the existing `DISABLE_AUTOUPDATER` pattern.

This step satisfies AC #1 and AC #7.

## TDD Order

1. Write the two tests first (they should fail because `MCP_TIMEOUT` is not yet in the dict).
2. Create `claude_settings.py`.
3. Update `env.py` to import the constant and set the env var.
4. Run quality gates — all green.
5. One commit.

## WHERE

| Path | Action |
|---|---|
| `src/mcp_coder/llm/claude_settings.py` | **Create** |
| `src/mcp_coder/llm/env.py` | Modify (1 import + 1 line + minor docstring touch) |
| `tests/llm/test_env.py` | Modify (add 2 tests) |

## WHAT

### `src/mcp_coder/llm/claude_settings.py` (new)

```python
"""Claude environment-variable defaults shared across mcp-coder.

Single source of truth for env vars consumed by the Claude CLI.
"""

MCP_TIMEOUT_MS: str = "30000"
```

That's it. One constant, one-line docstring. No re-exports, no future-proofing.

### `src/mcp_coder/llm/env.py`

Add an import at the top of the imports block:

```python
from mcp_coder.llm.claude_settings import MCP_TIMEOUT_MS
```

Inside `prepare_llm_environment()`, immediately **after** the existing `DISABLE_AUTOUPDATER` line:

```python
env_vars["DISABLE_AUTOUPDATER"] = os.environ.get("DISABLE_AUTOUPDATER", "1")
env_vars["MCP_TIMEOUT"] = os.environ.get("MCP_TIMEOUT", MCP_TIMEOUT_MS)
```

Update the docstring's "Returns" section to mention `MCP_TIMEOUT` alongside `DISABLE_AUTOUPDATER` (one short sentence — match existing density).

### `tests/llm/test_env.py`

Add two tests at the bottom of the file (after the existing `test_prepare_llm_environment_preserves_existing_disable_autoupdater`). Mirror that pair exactly:

```python
def test_prepare_llm_environment_sets_mcp_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that MCP_TIMEOUT defaults to '30000' when not set."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = tmp_path / "runner" / ".venv"
    venv_dir.mkdir(parents=True)

    monkeypatch.setenv("VIRTUAL_ENV", str(venv_dir))
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.delenv("MCP_TIMEOUT", raising=False)

    result = prepare_llm_environment(project_dir)

    assert result["MCP_TIMEOUT"] == "30000"


def test_prepare_llm_environment_preserves_existing_mcp_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that an existing MCP_TIMEOUT value is preserved."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    venv_dir = tmp_path / "runner" / ".venv"
    venv_dir.mkdir(parents=True)

    monkeypatch.setenv("VIRTUAL_ENV", str(venv_dir))
    monkeypatch.delenv("CONDA_PREFIX", raising=False)
    monkeypatch.setenv("MCP_TIMEOUT", "60000")

    result = prepare_llm_environment(project_dir)

    assert result["MCP_TIMEOUT"] == "60000"
```

## HOW (integration points)

- Import path: `from mcp_coder.llm.claude_settings import MCP_TIMEOUT_MS` — sits next to `env.py` in the same package.
- No `__init__.py` change needed — `claude_settings` is internal, not re-exported.
- The new env-var key (`"MCP_TIMEOUT"`) is set on the dict that callers already pass into the Claude subprocess via existing plumbing in `interface.py` / `claude_code_cli.py`. No call-site changes.

## ALGORITHM

```
# inside prepare_llm_environment():
build env_vars with project_dir / venv_dir / venv_path
env_vars["DISABLE_AUTOUPDATER"] = os.environ.get("DISABLE_AUTOUPDATER", "1")  # existing
env_vars["MCP_TIMEOUT"]         = os.environ.get("MCP_TIMEOUT", MCP_TIMEOUT_MS)  # new
return env_vars
```

## DATA

`prepare_llm_environment(project_dir: Path) -> dict[str, str]` now returns a dict with one extra key: `"MCP_TIMEOUT"`. Default value `"30000"`; parent-env value preserved if set.

`MCP_TIMEOUT_MS: str` — module-level constant in `claude_settings.py`.

## Quality gates before committing

1. `./tools/format_all.sh`
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
4. `mcp__tools-py__run_mypy_check`

All must pass.

## Commit message

```
feat(llm): add MCP_TIMEOUT env var to prepare_llm_environment

Introduces src/mcp_coder/llm/claude_settings.py holding MCP_TIMEOUT_MS
("30000"). prepare_llm_environment() now sets MCP_TIMEOUT in the
subprocess env, defaulting to MCP_TIMEOUT_MS but preserving any value
already set in the parent environment. Mirrors the existing
DISABLE_AUTOUPDATER pattern.

Refs #944
```

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1 only — Python core for `MCP_TIMEOUT`. Follow TDD: add the two new tests in `tests/llm/test_env.py` first, confirm they fail, then create `src/mcp_coder/llm/claude_settings.py` and update `src/mcp_coder/llm/env.py` to make them pass. Run `./tools/format_all.sh`, then `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_pytest_check` (with the recommended `-m "not ..."` exclusions), and `mcp__tools-py__run_mypy_check`. All must pass. Make exactly one commit using the message in step_1.md. Do not touch any other files in this step.
