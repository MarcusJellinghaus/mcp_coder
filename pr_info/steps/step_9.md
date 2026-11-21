# Step 9 — Messages for a missing mcp-tools-py (Scope 2)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_9.md`).
> Implement Step 9 only: the `_toolkit_class` "not registered" error for
> `mcp-tools-py` gains the install hint, and `verify`'s ENVIRONMENT row shows a
> missing mcp-tools-py as `[WARN] not installed (optional)`. Tests first, then
> code. Run format, pylint, mypy and the fast pytest set. One commit.

## WHERE

- `src/mcp_coder/utils/toolkit_runner.py` — `_toolkit_class`
- `src/mcp_coder/cli/commands/verify_sections.py` — `_print_environment_section`
- Tests:
  - `tests/utils/test_toolkit_runner.py` (registry tests; they import the real
    `_toolkit_class` at module level, so the autouse patch doesn't hide it)
  - `tests/cli/commands/test_verify.py::TestEnvironmentSection` — change the
    pinned `[ERR] not installed` for mcp-tools-py in place (file is near the size limit)

## WHAT

```python
# toolkit_runner.py
_PYTHON_TOOLKIT = "mcp-tools-py"
_PYTHON_EXTRA_HINT = (
    'install or upgrade the python extra: pip install --upgrade "mcp-coder[python]"; '
    "if the entry point is still missing, reinstall the tool env"
)

# verify_sections.py
_OPTIONAL_PACKAGES: frozenset[str] = frozenset({"mcp-tools-py"})
```

## ALGORITHM

```
# _toolkit_class, after the loop finds nothing
message = f"Toolkit '{name}' is not registered in the {ENTRY_POINT_GROUP} entry-point group; registered: {names}"
if name == _PYTHON_TOOLKIT: message += f" — {_PYTHON_EXTRA_HINT}"
raise ValueError(message)

# _print_environment_section, PackageNotFoundError branch
if pkg in _OPTIONAL_PACKAGES: Row(pkg, STATUS_SYMBOLS["warning"], "not installed (optional)")
else:                         Row(pkg, STATUS_SYMBOLS["failure"], "not installed")
```

The hint keys on the configured name not being registered — the one allowed
name switch. It also covers mcp-tools-py installed without the entry point.

## DATA

Error string, e.g. `Toolkit 'mcp-tools-py' is not registered in the
mcp_coder.toolkits entry-point group; registered: command — install or upgrade
the python extra: pip install --upgrade "mcp-coder[python]"; if the entry point
is still missing, reinstall the tool env`.

## Tests (write first)

- `entry_points` patched to return only `command` → `_toolkit_class("mcp-tools-py")`
  raises with `mcp-coder[python]` and "reinstall the tool env" in the message.
- `_toolkit_class("other")` unregistered → no python hint.
- ENVIRONMENT: `version` raising `PackageNotFoundError` for `mcp-tools-py` →
  `[WARN]` row "not installed (optional)"; for `mcp-workspace` → `[ERR]` "not installed".
