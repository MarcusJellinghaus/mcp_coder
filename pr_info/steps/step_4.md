# Step 4: Wire env_setup into `execute_icoder()`, `AppCore`, and TUI

> **Context:** Read `pr_info/steps/summary.md` for full issue context.

## Goal

Connect the new `env_setup` module into the icoder command flow: call it early in `execute_icoder()`, inject `RuntimeInfo` into `AppCore`, emit `session_start` event, and display startup info in the TUI output log.

## WHERE

- **Modify:** `src/mcp_coder/icoder/core/app_core.py`
- **Modify:** `src/mcp_coder/cli/commands/icoder.py`
- **Modify:** `src/mcp_coder/icoder/ui/app.py`
- **Modify:** `tests/icoder/conftest.py`
- **Modify:** `tests/icoder/test_app_core.py`
- **Modify:** `tests/icoder/test_cli_icoder.py` (if needed for env_setup integration)

## WHAT

### 1. `AppCore` — Add `runtime_info` parameter

```python
# In app_core.py
from mcp_coder.icoder.env_setup import RuntimeInfo

class AppCore:
    def __init__(
        self,
        llm_service: LLMService,
        event_log: EventLog,
        registry: CommandRegistry | None = None,
        runtime_info: RuntimeInfo | None = None,  # NEW
    ) -> None:
        ...
        self._runtime_info = runtime_info

    @property
    def runtime_info(self) -> RuntimeInfo | None:
        return self._runtime_info
```

### 2. `execute_icoder()` — Call env_setup early

```python
# In icoder.py, early in execute_icoder():
from ...icoder.env_setup import setup_icoder_environment

runtime_info = setup_icoder_environment(project_dir)
# Use runtime_info.env_vars for RealLLMService (merge with prepare_llm_environment result)
# Pass runtime_info to AppCore constructor
# Emit session_start event after creating event_log
```

#### ALGORITHM for execute_icoder changes

```
runtime_info = setup_icoder_environment(project_dir)
env_vars = runtime_info.env_vars  # use these instead of prepare_llm_environment()
...
app_core = AppCore(llm_service, event_log, runtime_info=runtime_info)
event_log.emit("session_start",
    mcp_coder_version=runtime_info.mcp_coder_version,
    tool_env=runtime_info.tool_env_path,
    project_venv=runtime_info.project_venv_path,
    project_dir=runtime_info.project_dir,
    mcp_servers={s.name: s.version for s in runtime_info.mcp_servers},
)
```

**Note:** `setup_icoder_environment()` now handles what `prepare_llm_environment()` did for icoder. The `prepare_llm_environment()` call can be replaced by using `runtime_info.env_vars` directly. If `setup_icoder_environment()` fails (e.g., missing MCP binaries), log the error and return exit code 1.

### 3. `ICoderApp.on_mount()` — Display startup info

```python
# In app.py on_mount():
def on_mount(self) -> None:
    if self._core.runtime_info:
        info = self._core.runtime_info
        output = self.query_one(OutputLog)
        lines = [
            f"mcp-coder {info.mcp_coder_version}",
            *(f"{s.name} {s.version}" for s in info.mcp_servers),
            f"Tool env:    {info.tool_env_path}",
            f"Project env: {info.project_venv_path}",
            f"Project dir: {info.project_dir}",
        ]
        output.append_text("\n".join(lines), style="dim")
    self.query_one(InputArea).focus()
```

### DATA

- `AppCore` gains optional `runtime_info: RuntimeInfo | None` field + property.
- `session_start` event emitted to `EventLog` with version, paths, and server info.
- TUI output log shows startup info as first entry (dim styled).

## HOW

- `AppCore` import of `RuntimeInfo` uses `TYPE_CHECKING` guard if desired, but since it's a dataclass used at runtime, a direct import is fine.
- `execute_icoder()` replaces the `prepare_llm_environment()` call with `setup_icoder_environment()` — the latter's `env_vars` dict serves the same purpose.
- Error handling: if `setup_icoder_environment()` raises `FileNotFoundError`, log a clear error and return 1.

## Tests (TDD — write first)

### `tests/icoder/conftest.py` updates
- `app_core` fixture: add `runtime_info=None` to constructor call (no behavior change for existing tests).

### `tests/icoder/test_app_core.py` additions
1. **`test_runtime_info_none_by_default`** — Verify `app_core.runtime_info` is `None` when not provided.
2. **`test_runtime_info_injected`** — Create `AppCore` with a `RuntimeInfo` instance, verify property returns it.

### `tests/icoder/test_cli_icoder.py` additions
3. **`test_execute_icoder_calls_env_setup`** — Mock `setup_icoder_environment`, verify it's called with `project_dir`.
4. **`test_execute_icoder_emits_session_start`** — Mock env_setup, verify `session_start` event is emitted to event log.

## Commit

```
feat(icoder): integrate env_setup into icoder command

- AppCore accepts optional RuntimeInfo via constructor injection
- execute_icoder() calls setup_icoder_environment() early
- session_start event emitted to EventLog with runtime info
- TUI shows startup info (versions, paths) as first output log entry
- Replaces prepare_llm_environment() call for icoder path

Part of #724.
```
