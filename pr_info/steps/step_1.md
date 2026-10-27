# Step 1 — Migrate `verify_mcp_servers` to `execute_command`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` exactly.
> TDD: update the tests in `tests/utils/test_mcp_verification.py` first, then change
> `src/mcp_coder/utils/mcp_verification.py`, then remove the two `ignore_imports` lines in
> `.importlinter`. Run lint-imports, pylint, mypy and the fast pytest suite; all must pass.
> Run the formatter, then make exactly one commit.

## WHERE

- `tests/utils/test_mcp_verification.py` — class `TestVerifyMcpServers`
- `src/mcp_coder/utils/mcp_verification.py` — function `verify_mcp_servers`
- `.importlinter` — contract `[importlinter:contract:subprocess_isolation]`

## Precondition

`verify_mcp_servers` in `mcp_verification.py` still calls `subprocess.run`. If it does not,
write one line to `pr_info/.blocked.txt` and stop.

## WHAT

### Tests (`tests/utils/test_mcp_verification.py`)

- Remove `import subprocess` and `from unittest.mock import MagicMock`.
- Add a small helper on `TestVerifyMcpServers` that patches the runner:

```python
def _patch_runner(
    self, monkeypatch: pytest.MonkeyPatch, result: CommandResult
) -> None:
    monkeypatch.setattr(
        "mcp_coder.utils.mcp_verification.execute_command",
        lambda *_a, **_kw: result,
    )
```

- `test_verify_mcp_servers_success` and `test_verify_mcp_servers_version_capture`: replace the
  `MagicMock` + `monkeypatch.setattr(subprocess, "run", ...)` with
  `self._patch_runner(monkeypatch, CommandResult(return_code=0, stdout="1.0.0\n", stderr=""))`
  (`"2.3.1\n"` for version capture). Assertions unchanged.
- Replace `test_verify_mcp_servers_version_nonzero_raises` and
  `test_verify_mcp_servers_subprocess_oserror_raises` with one parametrized test:

```python
@pytest.mark.parametrize(
    ("result", "match"),
    [
        pytest.param(
            CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                timed_out=True,
                execution_error="Process timed out after 30 seconds",
            ),
            "timed out after 30s",
            id="timeout",
        ),
        pytest.param(
            CommandResult(
                return_code=1,
                stdout="",
                stderr="",
                execution_error="OSError: permission denied",
            ),
            "Failed to invoke",
            id="launch_error",
        ),
        pytest.param(
            CommandResult(return_code=1, stdout="", stderr="error occurred"),
            "exited with code 1",
            id="nonzero_exit",
        ),
    ],
)
def test_verify_mcp_servers_version_failure_raises(
    self,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    result: CommandResult,
    match: str,
) -> None:
    self._create_fake_executables(tmp_path, monkeypatch)
    self._patch_runner(monkeypatch, result)
    with pytest.raises(RuntimeError, match=match):
        verify_mcp_servers(tmp_path)
```

The `timeout` case sets `execution_error` as well, the same as upstream does. If the code checks
`execution_error` first, this case fails.

### Implementation (`src/mcp_coder/utils/mcp_verification.py`)

Signature unchanged: `def verify_mcp_servers(venv_root: str | Path) -> list[MCPServerInfo]`.

- Remove `import subprocess` (`execute_command` is already imported).
- Docstring `Raises` becomes:

```
Raises:
    FileNotFoundError: If a binary is missing.
    RuntimeError: If a binary exists but ``--version`` times out,
        cannot be launched, or exits non-zero.
```

## HOW

- `execute_command` is already imported from `mcp_coder.utils.subprocess_runner` (the shim);
  no new imports.
- Tests patch `mcp_coder.utils.mcp_verification.execute_command`, the same patch target
  `TestParseClaudeMcpList` uses.

## ALGORITHM

```
timeout = 30
for each server name:
    raise FileNotFoundError if exe missing            # unchanged
    result = execute_command([str(exe_path), "--version"], timeout_seconds=timeout)
    if result.timed_out: raise RuntimeError(f"{exe_path} --version timed out after {timeout}s")
    if result.execution_error: raise RuntimeError(f"Failed to invoke {exe_path}: {result.execution_error}")
    if result.return_code != 0: raise RuntimeError(f"{exe_path} --version exited with code {rc}: {stderr.strip()}")
    append MCPServerInfo(name, exe_path, result.stdout.strip())
```

`timeout` is a local variable, so the call and the message share one value.

### `.importlinter`

Delete exactly these two lines from `subprocess_isolation` → `ignore_imports`:

```
    mcp_coder.utils.mcp_verification -> subprocess
    tests.utils.test_mcp_verification -> subprocess
```

## DATA

- Returns `list[MCPServerInfo]` as before.
- Uses `CommandResult` fields: `timed_out: bool`, `execution_error: str | None`,
  `return_code: int`, `stdout: str`, `stderr: str`.

## Checks

- `mcp__mcp-tools-py__run_lint_imports_check` — passes; this also confirms there are no unmatched entries.
- `mcp__mcp-tools-py__run_pylint_check`, `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `-n auto` and the fast-unit marker filter from CLAUDE.md
- `mcp__mcp-tools-py__run_format_code`, then commit, e.g.
  `refactor(utils): run mcp server --version via execute_command`
