# Step 4 — `verify` key-warning rows + end-to-end `verify` tests

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md`.
> Steps 1–3 are done (no reader crashes any more). Write the tests first,
> then the code. Run pylint, the fast pytest set (`-n auto`), mypy and ruff;
> all must pass. Run `run_format_code`, then commit tests + code as one commit.

## Precondition

`src/mcp_coder/cli/commands/verify_project_keys.py` has `_classify(file_name, key, value)`
with an `if key == "implement":` branch and a `_PYTHON_ONLY` check. If not
(e.g. #1466 restructured the module), write one line to `pr_info/.blocked.txt` and stop.

## WHERE

- `src/mcp_coder/cli/commands/verify_project_keys.py`
- `tests/cli/commands/test_verify_project_keys.py`
- `tests/cli/commands/test_verify_project_section.py`

## WHAT

`_classify(file_name: str, key: str, value: Any) -> list[KeyWarning]` — two branch changes:

```python
if key == "implement":
    if file_name != "pyproject.toml" or not isinstance(value, dict):
        return [KeyWarning("PROJECT", file_name, f"[{_TOP}.implement] is retired and ignored")]
    ...  # unchanged per-key rows
if key in _PYTHON_ONLY and file_name != "pyproject.toml":
    ...  # unchanged
if key in _PYTHON_ONLY and not isinstance(value, dict):
    return [KeyWarning("PROJECT", file_name, f"[{_TOP}.{key}] is not a table")]
```

## HOW

- `scan_project_keys` is unchanged (its own walk already yields the
  "cannot be parsed" row for a non-table `tool` / `mcp-coder`).
- `prompts` is not in `_PYTHON_ONLY`, so a non-table `prompts` keeps today's behaviour.
- Rows stay exit-neutral (key warnings never feed `ok`).

## DATA

`KeyWarning("PROJECT", "pyproject.toml", "[tool.mcp-coder.install] is not a table")`, etc.

## Tests

`tests/cli/commands/test_verify_project_keys.py`, class `TestScanProjectKeys`:
- parametrized `implement = 1`, `implement = "format_code"`, `implement = ["format_code"]`
  (under `[tool.mcp-coder]` in pyproject.toml) → `warnings == [KeyWarning("PROJECT", "pyproject.toml", "[tool.mcp-coder.implement] is retired and ignored")]`.
- parametrized `install = 1`, `install-from-github = 1` →
  `[KeyWarning("PROJECT", "pyproject.toml", "[tool.mcp-coder.<key>] is not a table")]`.
- `prompts = 1` → no PROJECT warning (pins unchanged behaviour).

`tests/cli/commands/test_verify_project_section.py`, new class `TestNonTableConfigVerify`
(module autouse `_stub_toolkit` applies):
- parametrized `(content, fragment, exit_code)`:
  - `"tool = 1\n"`, `"cannot be parsed"`, 1
  - `"[tool]\nmcp-coder = 1\n"`, `"cannot be parsed"`, 1
  - the three `implement` contents, `"[tool.mcp-coder.implement] is retired and ignored"`, 0
  - `"[tool.mcp-coder]\ninstall = 1\n"`, `"[tool.mcp-coder.install] is not a table"`, 0
  - `"[tool.mcp-coder]\ninstall-from-github = 1\n"`, `"[tool.mcp-coder.install-from-github] is not a table"`, 0
- Body: write `tmp_path / "pyproject.toml"`; run inside `_make_verify_mocks()` and
  `patch("mcp_coder.cli.commands.verify._print_project_section", _print_project_section)`
  (as `TestExecuteVerifyProjectExit` does); `code = execute_verify(_make_args(project_dir=str(tmp_path)))`.
- Asserts: `code == exit_code`; `_squash(fragment) in _squash(out)`;
  `"legacy format_code" not in out`; some line starts with `"=== GIT "`
  (verify continued past PROJECT); for the two `cannot be parsed` cases
  `"[ERR]" in _row(lines, "Toolkit")`.
- If the exit code of the 0-cases differs because of an unrelated row, compare
  against a baseline run on `"[project]\nname = \"x\"\n"` instead of a literal 0.

## Commit message

`fix(verify): report a non-table implement, install or install-from-github in PROJECT`
