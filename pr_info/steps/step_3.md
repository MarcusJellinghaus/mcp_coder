# Step 3 — Environment Section

## Goal

Add a new `=== ENVIRONMENT ===` section at the top of verify output. Shows Python runtime info + 4 package versions. Plain `label: value` rows (no status symbols); exception: `[ERR] not installed` for missing packages.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3 as a single commit: add `_print_environment_section()` in `src/mcp_coder/cli/commands/verify.py` and call it at the top of `execute_verify` (before config). Write tests first using `capsys` for the environment section output. Run pylint, pytest, mypy.

## WHERE

- **Modify:** `src/mcp_coder/cli/commands/verify.py`
- **Modify tests:** `tests/cli/commands/test_verify.py` — add `TestEnvironmentSection` class

## WHAT

```python
def _print_environment_section() -> None:
    """Print the ENVIRONMENT section (Python info + 4 package versions).

    Uses `sys`, `os.environ`, `importlib.metadata`. Writes directly to stdout
    via `print` to match the style of inline sections in `execute_verify`.
    """
```

Integrated call in `execute_verify`:
```python
def execute_verify(args: argparse.Namespace) -> int:
    logger.info("Executing verify command")
    symbols = STATUS_SYMBOLS
    _print_environment_section()     # NEW: first section
    # ... existing code continues
```

## HOW

- Import at top: `import sys`, `from importlib.metadata import PackageNotFoundError, version`.
- Define a module-level constant in `verify.py` (near the top, alongside `STATUS_SYMBOLS`):
  ```python
  _ENVIRONMENT_PACKAGES: tuple[str, ...] = (
      "mcp-coder",
      "mcp-coder-utils",
      "mcp-tools-py",
      "mcp-workspace",
  )
  ```
  The `_print_environment_section()` helper iterates over `_ENVIRONMENT_PACKAGES` instead of an inline hardcoded list (for testability and maintenance).
- Virtualenv: `sys.prefix` when `sys.prefix != sys.base_prefix`, else `"(none)"`.
- PYTHONPATH: `os.environ.get("PYTHONPATH", "(not set)")` — if empty string, use `"(not set)"`.
- Python version: `f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"`.

## ALGORITHM

```
print(_pad("ENVIRONMENT"))
print_row("Python version", python_version_str)
print_row("Executable", sys.executable)
print_row("Virtualenv", sys.prefix if sys.prefix != sys.base_prefix else "(none)")
print_row("PYTHONPATH", os.environ.get("PYTHONPATH") or "(not set)")
print()  # blank line between python info and versions
for pkg in _ENVIRONMENT_PACKAGES:
    try: val = version(pkg)
    except PackageNotFoundError: val = "[ERR] not installed"
    print_row(pkg, val)
```

Row format: `f"  {label:<20s} {value}"` — no status symbols on OK rows (Decision 12).

## DATA

- No return value — prints directly.
- Field values: all `str`.

## Tests to Add

```python
class TestEnvironmentSection:
    def test_section_header_present(self, capsys) -> None:
        _print_environment_section()
        assert "=== ENVIRONMENT" in capsys.readouterr().out

    def test_python_version_row(self, capsys) -> None:
        _print_environment_section()
        out = capsys.readouterr().out
        assert "Python version" in out
        assert f"{sys.version_info.major}.{sys.version_info.minor}" in out

    def test_pythonpath_not_set_when_missing(self, capsys, monkeypatch) -> None:
        monkeypatch.delenv("PYTHONPATH", raising=False)
        _print_environment_section()
        assert "(not set)" in capsys.readouterr().out

    def test_missing_package_shows_err_not_installed(self, capsys, monkeypatch) -> None:
        from importlib.metadata import PackageNotFoundError
        def fake_version(pkg: str) -> str:
            if pkg == "mcp-tools-py":
                raise PackageNotFoundError(pkg)
            return "1.2.3"
        monkeypatch.setattr("mcp_coder.cli.commands.verify.version", fake_version)
        _print_environment_section()
        assert "[ERR] not installed" in capsys.readouterr().out

    def test_virtualenv_none_when_not_in_venv(self, capsys, monkeypatch) -> None:
        monkeypatch.setattr(sys, "prefix", "/usr")
        monkeypatch.setattr(sys, "base_prefix", "/usr")
        _print_environment_section()
        assert "(none)" in capsys.readouterr().out
```

## Verification

All three checks must pass.
