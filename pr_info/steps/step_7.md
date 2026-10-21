# Step 7 — verify: `format_code`, Formatter and leftover-key rows; exit code

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_7.md` only.
> TDD: write the tests first, then the implementation. Run pylint, mypy, pytest (fast unit
> markers, `-n auto`) and lint-imports; all must pass. Format with `run_format_code`, then
> make exactly one commit.

## WHERE

- `src/mcp_coder/cli/commands/verify_sections.py`
- `src/mcp_coder/cli/commands/verify.py`
- `src/mcp_coder/cli/commands/verify_exit_code.py`
- `tests/cli/commands/conftest.py` (autouse patch)
- `tests/cli/commands/test_verify_project_section.py` (**new** — `test_verify.py` is at 737/750)
- `tests/cli/commands/test_verify.py` (`:650-737`, adjust only)
- `tests/cli/commands/test_verify_exit_codes.py`

## WHAT

```python
def _format_code_row(project_dir: Path, symbols: dict[str, str]) -> bool: ...
def _formatter_row(project_dir: Path, symbols: dict[str, str]) -> bool: ...
def _print_project_section(project_dir: Path, symbols: dict[str, str]) -> bool:
    """Returns: False if any row printed [ERR]."""
```

`verify_exit_code._compute_exit_code(..., prompts_ok: bool = True, project_ok: bool = True)`;
docstring "Exit 1 when…" gains "when the project's formatter configuration is invalid";
`Args:` gains `project_ok`. Check: `if not project_ok: return 1` (next to `prompts_ok`).

`verify.py`: `project_ok = _print_project_section(project_dir, symbols)`; pass `project_ok=project_ok`.

## HOW

- Imports in `verify_sections.py`: `resolve_steps` from `...mcp_tools_py`;
  `get_format_code`, `has_legacy_format_code_key` from `...utils.pyproject_config`.
- Stop reading `config.format_code` (keep `check_type_hints` row from `get_implement_config`).
- `[ERR]` uses `symbols["failure"]`; OK uses `symbols["success"]`.
- `tests/cli/commands/conftest.py`: add autouse fixture patching
  `mcp_coder.cli.commands.verify._print_project_section` with a `side_effect` that prints the
  PROJECT header (`print(_pad("PROJECT"))`) and returns `True` (same pattern as `_mock_verify_git`),
  so `execute_verify` tests stay hermetic and section-order tests that search the output for
  `"PROJECT"` (e.g. `tests/cli/commands/test_verify_sections_orchestration.py:423`) keep passing.
  Tests calling `_print_project_section` directly import it from `verify_sections` and are unaffected.

## ALGORITHM

```
_print_project_section(p, symbols):
    print PROJECT header
    if no pyproject.toml:
        print pyproject.toml "not found", Language "(none detected)"
        return _formatter_row(p, symbols)            # [ERR] with resolve_steps' message
    print found / Language / [Python]
    ok = _format_code_row(p, symbols)               # enabled (default) | enabled | disabled | [ERR] msg
    ok = _formatter_row(p, symbols) and ok          # always evaluated: "isort → black" | [ERR] msg
    if has_legacy_format_code_key(p):
        print [ERR] "[tool.mcp-coder.implement] format_code ignored — use [tool.mcp-coder] format_code"; ok = False
    print check_type_hints row (unchanged)
    return ok
```

`_formatter_row`: `try: steps = resolve_steps(p)` → OK row `" → ".join(steps)`;
`except ValueError as e` → `[ERR]` row `str(e)`, return False.

## DATA

Row labels: `format_code`, `Formatter`, `legacy format_code`. `_print_project_section` → `bool`.

## Tests (`test_verify_project_section.py`, real `pyproject.toml` files in `tmp_path`)

- `[tool.black]` only → Formatter row `isort → black`, returns True.
- `[tool.ruff.format]` only → `ruff_imports → ruff_format`.
- Both / neither → Formatter `[ERR]` with resolve message, returns False.
- `format_code = false` → `disabled`, Formatter still evaluated.
- Key absent → `enabled (default)`; `true` → `enabled`; `"false"` → `[ERR]`, returns False.
- Leftover `[tool.mcp-coder.implement] format_code` → `[ERR]` naming `[tool.mcp-coder] format_code`, False.
- No `pyproject.toml` → Formatter `[ERR]`, no `format_code` row, returns False.
- `_compute_exit_code(..., project_ok=False)` → 1 (in `test_verify_exit_codes.py`).
- One `execute_verify` test overriding the conftest patch with `return_value=False` → exit 1.
- Adjust `test_verify.py:650-737` expectations for the new default (`enabled (default)`) and rows;
  keep the file under 750 lines (move tests to the new file if needed).
