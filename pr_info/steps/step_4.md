# Step 4: Startup Wiring — Connect Skills in execute_icoder()

**Context**: See `pr_info/steps/summary.md` for full issue context. Steps 1-3 must be complete.

## Goal

Wire skill loading and registration into the iCoder CLI startup path. The CLI layer explicitly creates the registry, loads skills, registers them, then passes the registry to `AppCore`.

## Prompt

```
Implement Step 4 of issue #720 (see pr_info/steps/summary.md for context).
Steps 1-3 (foundation, models/loader, registration/routing) are complete.

Wire skills into execute_icoder():
1. Create registry explicitly with create_default_registry()
2. Load skills with load_skills(project_dir)
3. Register with register_skill_commands(registry, skills, provider)
4. Pass registry=registry to AppCore
5. Write tests first (TDD), then implement.
6. Run all three code quality checks after changes.
```

## Tests First — `tests/icoder/test_cli_icoder.py`

### WHERE
`tests/icoder/test_cli_icoder.py` — check existing tests, append new test

### WHAT — new test function

```python
def test_execute_icoder_creates_registry_with_skills(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """execute_icoder creates registry, loads skills, and passes to AppCore."""
```

#### ALGORITHM — test pseudocode
```
create a .claude/skills/test_skill/SKILL.md in tmp_path
monkeypatch ICoderApp.run to no-op
monkeypatch setup_icoder_environment to return a RuntimeInfo
monkeypatch resolve_llm_method, parse_llm_method_from_args, resolve_mcp_config_path
monkeypatch find_latest_session to return None
capture the AppCore instance passed to ICoderApp
assert "/test_skill" is in the registry's commands
```

## Implementation — `src/mcp_coder/cli/commands/icoder.py`

### WHERE
`src/mcp_coder/cli/commands/icoder.py` — inside `execute_icoder()`, between provider resolution (~line 66) and AppCore creation (~line 96)

### WHAT
Add skill loading and registration. Pass explicit registry to AppCore.

### HOW — changes

```python
# After provider resolution (line ~66), add imports and skill loading:
from ...icoder.core.command_registry import create_default_registry
from ...icoder.skills import load_skills, register_skill_commands

# Between provider resolution and AppCore creation:
registry = create_default_registry()
skills = load_skills(project_dir)
register_skill_commands(registry, skills, provider)

# Change AppCore creation from:
app_core = AppCore(llm_service, event_log, runtime_info=runtime_info)
# To:
app_core = AppCore(llm_service, event_log, registry=registry, runtime_info=runtime_info)
```

### ALGORITHM — integration pseudocode
```
... (existing: resolve provider, resolve mcp config, find session) ...
registry = create_default_registry()           # NEW
skills = load_skills(project_dir)              # NEW
register_skill_commands(registry, skills, provider)  # NEW
... (existing: create llm_service) ...
app_core = AppCore(..., registry=registry, ...)  # CHANGED: pass explicit registry
```

## Commit Message
```
feat(icoder): wire skill loading into execute_icoder startup
```
