# Step 3 — `verification.py`: pre-flight MCP server check with actionable diagnostics

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement
> Step 3 only: in `src/mcp_coder/llm/providers/langchain/verification.py`,
> add a pre-flight helper `_preflight_mcp_server` that distinguishes
> unresolved `${VAR}` residue from missing binary, and use it inside
> `_check_servers` before the async launch. Also enrich the launch-error
> fallback with the resolved command path and exception class name.
> Update / add tests in
> `tests/llm/providers/langchain/test_mcp_health_check.py`. Run the
> mandatory MCP tool quality checks.

## WHERE

- `src/mcp_coder/llm/providers/langchain/verification.py` — modify.
- `tests/llm/providers/langchain/test_mcp_health_check.py` — modify.

## WHAT

### New helper

```python
def _preflight_mcp_server(
    name: str,
    cfg: dict[str, object],
) -> dict[str, object] | None:
    """Return a failure result dict if the resolved config has obvious
    issues (unresolved ${VAR} or missing binary), else None.
    """
```

### Behaviour of `_preflight_mcp_server`

1. Scan `cfg["command"]`, each string element of `cfg["args"]`, and each
   string value of `cfg["env"]` for `\$\{[^}]+\}` residue. On first
   match, return:
   ```python
   {
       "ok": False,
       "value": f"unresolved placeholder {match.group(0)} in {field}",
       "error": "UnresolvedPlaceholder",
   }
   ```
   (`field` is one of `"command"`, `"args"`, `"env"`.)

2. Otherwise, `Path(command).exists()` check (only when `command` is a
   non-empty string). If the path does not exist, return:
   ```python
   {
       "ok": False,
       "value": f"binary not found at {command}",
       "error": "FileNotFoundError",
   }
   ```

3. Otherwise return `None` (proceed to live launch).

Known false-positive trade-off: bare executables like `python` or `npx`
that resolve via `PATH` will fail the `Path.exists()` check. Accepted —
the launch-error fallback still reports them cleanly.

### Use in `_check_servers`

Before the existing `try:` block:

```python
for server_name in server_config:
    cfg = server_config[server_name]
    preflight = _preflight_mcp_server(server_name, cfg)
    if preflight is not None:
        results[server_name] = preflight
        continue
    # ... existing client.session(...) block ...
```

### Enriched launch-error fallback

In the existing `except Exception as exc:` clause, change the `"value"`
from `str(exc)` to include the resolved command path and the exception
class name:

```python
results[server_name] = {
    "ok": False,
    "value": (
        f"MCP server {server_name!r} failed to launch: "
        f"{cfg.get('command', '')} ({type(exc).__name__}: {exc})"
    ),
    "error": type(exc).__name__,
}
```

## HOW — integration points

- No new imports beyond `re` (module already imports `Path` from
  `pathlib` indirectly? — add `from pathlib import Path` and
  `import re` if not present).
- `_preflight_mcp_server` is module-private (`_` prefix) and synchronous.
- `_check_servers` remains `async` and keeps its existing signature.
- The returned dict shape matches the existing success-failure contract
  (`{"ok": bool, "value": str, "error": str}`), so
  `_format_mcp_section` in `verify.py` renders without change.

## ALGORITHM — pre-flight scan

```
pattern = re.compile(r"\$\{[^}]+\}")
for field, value in (("command", cmd_str),
                     ("args", each args string),
                     ("env", each env value string)):
    if pattern.search(value):
        return {"ok": False,
                "value": f"unresolved placeholder {match} in {field}",
                "error": "UnresolvedPlaceholder"}
if cmd_str and not Path(cmd_str).exists():
    return {"ok": False,
            "value": f"binary not found at {cmd_str}",
            "error": "FileNotFoundError"}
return None
```

## DATA

- Pre-flight result: `dict[str, object]` with keys `"ok"` (False),
  `"value"` (message), `"error"` (category tag: `"UnresolvedPlaceholder"`
  or `"FileNotFoundError"`).
- Pre-flight success: `None`.
- `verify_mcp_servers` return shape unchanged: `{"servers":
  {name: {"ok": bool, "value": str, "error": str, ...}},
  "overall_ok": bool}`.

## TDD — tests to add / change

In `tests/llm/providers/langchain/test_mcp_health_check.py`:

1. **Update `test_server_failure`** — the existing test uses
   `command="nonexistent"` with `__aenter__` raising `FileNotFoundError`.
   With the new pre-flight, `_check_servers` never reaches the live
   launch because `Path("nonexistent").exists()` is False. Update the
   assertion:
   - `result["servers"]["broken"]["error"] == "FileNotFoundError"` ✓
     (still true).
   - `"binary not found at nonexistent"` **in**
     `result["servers"]["broken"]["value"]`.

2. **Update `test_mixed_servers`** — `bad` entry uses
   `command="nonexistent"`. Assert new `binary not found` message.
   `good` uses `command="python"` which may or may not exist on CI.
   Change the `good` command to point at an existing path (e.g.
   `sys.executable`) so pre-flight passes and the live launch mock fires.

3. **Update `test_timeout_handling`** — command `"python"` may fail
   pre-flight. Change to `sys.executable` to skip pre-flight.

4. **Update `test_server_success`** and
   **`test_server_success_includes_tool_names`** and
   **`test_server_success_includes_tool_descriptions`** — change
   `command="python"` to `sys.executable` (pre-flight gate).

5. **New `test_unresolved_placeholder_in_command`** — configure a server
   with `command="${MCP_CODER_VENV_PATH}\\foo.exe"`. Assert
   `result["servers"][name]["error"] == "UnresolvedPlaceholder"` and
   `"${MCP_CODER_VENV_PATH}"` is in the value message.

6. **New `test_unresolved_placeholder_in_args`** — configure
   `command=sys.executable, args=["--path", "${FOO_UNSET}"]`. Assert
   `UnresolvedPlaceholder` category.

7. **New `test_unresolved_placeholder_in_env`** — configure
   `command=sys.executable, env={"X": "${BAR_UNSET}"}`. Assert
   `UnresolvedPlaceholder` category.

8. **New `test_launch_error_includes_resolved_path_and_class`** —
   pre-flight passes (`command=sys.executable`), live launch raises
   `ConnectionError("boom")`. Assert the reported value contains both
   `sys.executable` and `"ConnectionError"`.

## Done-when

- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_pytest_check` (fast-unit exclusions) green.
- `mcp__tools-py__run_mypy_check` clean.
- Single commit: "Step 3: pre-flight MCP server check with actionable
  diagnostics (#830)".
