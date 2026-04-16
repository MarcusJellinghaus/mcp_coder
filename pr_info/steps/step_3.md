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
) -> tuple[bool, str | None]:
    """Return (ok, message). ok=True and message=None means proceed to
    live launch. ok=False and message=<actionable text> means short-circuit
    with the message. `name` is used in the message so the caller can
    build the result dict without re-threading the server name.
    """
```

### Behaviour of `_preflight_mcp_server`

1. Scan `cfg["command"]`, each string element of `cfg["args"]`, and each
   string value of `cfg["env"]` for `\$\{[^}]+\}` residue. On first
   match, return:
   ```python
   return (False,
           f"unresolved placeholder {m.group(0)} in {name}.{field}")
   ```
   (`field` is one of `"command"`, `"args"`, `"env"`; `name` is the
   server name — this is why the helper takes `name` as a parameter.)

2. Otherwise, `shutil.which(command)` check (only when `command` is a
   non-empty string). `shutil.which` covers both absolute paths and
   bare executables resolved via `PATH` (e.g. `python`, `npx`), so
   there are **no** false-positives. If `shutil.which` returns `None`,
   return:
   ```python
   return (False,
           f"binary not found at {resolved_command} (server {name})")
   ```

3. Otherwise return `(True, None)` (proceed to live launch).

### Use in `_check_servers`

Before the existing `try:` block:

```python
for server_name in server_config:
    cfg = server_config[server_name]
    ok, msg = _preflight_mcp_server(server_name, cfg)
    if not ok:
        # msg already names the server + the unresolved placeholder /
        # missing binary; derive a category tag from its prefix.
        category = ("UnresolvedPlaceholder"
                    if msg.startswith("unresolved placeholder")
                    else "FileNotFoundError")
        results[server_name] = {"ok": False, "value": msg,
                                "error": category}
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

- Add at module top (only the ones not already imported):
  - `import re`
  - `import shutil`
  - `from pathlib import Path` — only if something else in the module
    still uses `Path`. Pre-flight no longer needs `Path` (it uses
    `shutil.which`), so if no other consumer remains, drop the import.
- `_preflight_mcp_server` is module-private (`_` prefix) and synchronous.
- `_check_servers` remains `async` and keeps its existing signature.
- The returned dict shape (built by the caller from the helper's
  `(ok, msg)` tuple) matches the existing success-failure contract
  (`{"ok": bool, "value": str, "error": str}`), so
  `_format_mcp_section` in `verify.py` renders without change.

## ALGORITHM — pre-flight scan

```
pattern = re.compile(r"\$\{[^}]+\}")
for field, value in (("command", cmd_str),
                     ("args", each args string),
                     ("env", each env value string)):
    m = pattern.search(value)
    if m:
        return (False,
                f"unresolved placeholder {m.group(0)} in {name}.{field}")
if cmd_str and shutil.which(cmd_str) is None:
    return (False,
            f"binary not found at {cmd_str} (server {name})")
return (True, None)
```

## DATA

- Pre-flight return: `tuple[bool, str | None]`. `(True, None)` means
  proceed; `(False, <message>)` means short-circuit.
- Caller (`_check_servers`) wraps the failure tuple into the existing
  result dict shape (`{"ok": False, "value": msg, "error": category}`
  where category is `"UnresolvedPlaceholder"` or `"FileNotFoundError"`).
- `verify_mcp_servers` return shape unchanged: `{"servers":
  {name: {"ok": bool, "value": str, "error": str, ...}},
  "overall_ok": bool}`.

## TDD — tests to add / change

In `tests/llm/providers/langchain/test_mcp_health_check.py`:

1. **Update `test_server_failure`** — the existing test uses
   `command="nonexistent"` with `__aenter__` raising `FileNotFoundError`.
   With the new pre-flight, `_check_servers` never reaches the live
   launch because `shutil.which("nonexistent")` returns `None`. Update
   the assertion:
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

9. **New `test_launch_error_filenotfound_after_preflight_passes`** —
   pre-flight passes (resolved command is present, e.g.
   `sys.executable`), but the async `client.session(...)` still raises
   `FileNotFoundError`. Assert the verify row's value contains the
   resolved command path **and** the class name
   `"FileNotFoundError"` (not just `str(exc)`), confirming the
   enriched launch-error fallback fires even when pre-flight was
   green.

## Done-when

- `mcp__tools-py__run_pylint_check` clean.
- `mcp__tools-py__run_pytest_check` (fast-unit exclusions) green.
- `mcp__tools-py__run_mypy_check` clean.
- Single commit: "Step 3: pre-flight MCP server check with actionable
  diagnostics (#830)".
