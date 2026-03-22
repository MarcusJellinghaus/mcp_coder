# Step 3: Update `workspace.py` + `test_workspace.py`

> **Context**: Read `pr_info/steps/summary.md` for the full design. This step rewrites the script generation logic and its tests.

## TDD: Update tests first, then implementation

### 3a. Update `tests/workflows/vscodeclaude/test_workspace.py`

**WHERE**: `tests/workflows/vscodeclaude/test_workspace.py`

**WHAT**: Update mock configs and test assertions for the new schema.

#### Update `MOCK_VSCODECLAUDE_CONFIGS`

Replace the old mock config dict with `commands` lists:

```python
MOCK_VSCODECLAUDE_CONFIGS: dict[str, dict[str, Any]] = {
    "status-01:created": {
        "emoji": "📝",
        "display_name": "ISSUE ANALYSIS",
        "stage_short": "new",
        "commands": ["/issue_analyse", "/discuss"],
    },
    "status-04:plan-review": {
        "emoji": "📋",
        "display_name": "PLAN REVIEW",
        "stage_short": "plan",
        "commands": ["/plan_review", "/discuss"],
    },
    "status-07:code-review": {
        "emoji": "🔍",
        "display_name": "CODE REVIEW",
        "stage_short": "review",
        "commands": ["/implementation_review_supervisor"],
    },
    "status-10:pr-created": {
        "emoji": "🎉",
        "display_name": "PR CREATED",
        "stage_short": "pr",
    },
}
```

#### Update existing tests

1. **`test_creates_script_with_mcp_coder_prompt`** (uses status-01:created, multi-command):
   - Keep assertion `"mcp-coder prompt" in content`
   - Keep assertion `"--output-format session-id" in content`
   - Change assertion `"--session-id %SESSION_ID%" in content` → `not in content` (status-01 has no middle commands — the /discuss is now interactive resume, not automated resume)
   - Add assertion `"claude --resume %SESSION_ID%" in content` (last command interactive)
   - Add assertion `"/discuss" in content`

2. **`test_creates_script_with_claude_resume`** (uses status-07:code-review, single-command):
   - Change from asserting `"claude --resume %SESSION_ID%" in content` to asserting `"claude \"/implementation_review_supervisor" in content` (now interactive-only, no resume)
   - Add assertion `"mcp-coder prompt" not in content` (single command = no automated step)
   - Add assertion `"Step 1" not in content` (no step labels for single-command)

3. **`test_uses_correct_initial_command_for_status`** (uses status-01:created):
   - Keep assertion `"/issue_analyse 123" in content` — this should still appear in the automated section

4. **`test_includes_discussion_section_when_followup_command_set`**:
   - Rename to `test_multi_command_has_automated_and_interactive_sections`
   - Assert: `"mcp-coder prompt" in content` (first command automated)
   - Assert: `"claude --resume %SESSION_ID%" in content` (last command interactive)
   - Assert: `"/discuss" in content`
   - Assert: `"Step 1" in content` (multi-command has step labels)
   - Remove assertion for `"Step 2: Automated Discussion"` (discussion is now interactive, not automated)

5. **`test_omits_discussion_section_when_followup_command_null`**:
   - Rename to `test_single_command_uses_interactive_only`
   - Assert: `"mcp-coder prompt" not in content` (no automated step)
   - Assert: `"claude \"/implementation_review_supervisor 123\"" in content` (interactive-only with issue number)
   - Assert: `"Step 1" not in content` and `"Step 2" not in content` (no step labels)
   - Remove old `"claude --resume %SESSION_ID%" in content` assertion

6. **`test_three_command_flow_has_automated_resume_middle`** (new test, uses custom 3-command mock config):
   - Mock a config with `"commands": ["/step_one", "/step_two", "/step_three"]`
   - Assert: `"mcp-coder prompt" in content` and `"--output-format session-id" in content` (first command automated)
   - Assert: `"--session-id %SESSION_ID%" in content` (middle command uses automated resume)
   - Assert: `"claude --resume %SESSION_ID%" in content` and `"/step_three" in content` (last command interactive)
   - Assert: `"Step 1" in content` and `"Step 2" in content` and `"Step 3" in content`

**DATA**: `MOCK_VSCODECLAUDE_CONFIGS` dict shape changes. No new test classes needed.

### 3b. Update `src/mcp_coder/workflows/vscodeclaude/workspace.py`

**WHERE**: `src/mcp_coder/workflows/vscodeclaude/workspace.py` — function `create_startup_script()`

**WHAT**: Rewrite the normal-mode (non-intervention) branch to use `commands` list.

#### Import changes

Replace:
```python
from .templates import (
    AUTOMATED_SECTION_WINDOWS,
    DISCUSSION_SECTION_WINDOWS,
    INTERACTIVE_SECTION_WINDOWS,
    INTERVENTION_SCRIPT_WINDOWS,
    STARTUP_SCRIPT_WINDOWS,
    VENV_SECTION_WINDOWS,
)
```

With:
```python
from .templates import (
    AUTOMATED_RESUME_SECTION_WINDOWS,
    AUTOMATED_SECTION_WINDOWS,
    INTERACTIVE_ONLY_SECTION_WINDOWS,
    INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS,
    INTERVENTION_SCRIPT_WINDOWS,
    STARTUP_SCRIPT_WINDOWS,
    VENV_SECTION_WINDOWS,
)
```

#### Config reading change

Replace:
```python
initial_cmd = config["initial_command"] if config else None
followup_cmd = config["followup_command"] if config else None
```

With:
```python
commands = config.get("commands", []) if config else []
```

#### Script generation logic (normal mode)

**ALGORITHM**:
```python
commands = config.get("commands", []) if config else []
if len(commands) == 1:
    # Single command: interactive only, no step labels
    command_sections = INTERACTIVE_ONLY_SECTION_WINDOWS.format(
        command=commands[0], issue_number=issue_number,
    )
elif len(commands) > 1:
    sections = []
    for i, cmd in enumerate(commands):
        step_number = i + 1
        is_last = (i == len(commands) - 1)
        if i == 0:
            sections.append(AUTOMATED_SECTION_WINDOWS.format(
                command=cmd, issue_number=issue_number,
                timeout=timeout, step_number=step_number,
            ))
        elif not is_last:
            sections.append(AUTOMATED_RESUME_SECTION_WINDOWS.format(
                command=cmd, timeout=timeout, step_number=step_number,
            ))
        if is_last:
            sections.append(INTERACTIVE_RESUME_WITH_COMMAND_WINDOWS.format(
                command=cmd, step_number=step_number,
            ))
    command_sections = "\n".join(sections)
else:
    command_sections = ""

script_content = STARTUP_SCRIPT_WINDOWS.format(
    ..., command_sections=command_sections,
)
```

#### Update docstring

Update the `create_startup_script()` docstring to describe the new behavior:
- Remove references to `initial_command`/`followup_command`
- Describe single-command vs multi-command flows
- Note that `timeout` is unused for single-command flows (Decision #5)

#### Input validation

Add validation at the start of the normal-mode branch (Decision #6):
```python
if commands and (not isinstance(commands, list) or not all(isinstance(c, str) for c in commands)):
    raise ValueError(f"Invalid commands config for status '{status}': expected list of strings, got {commands!r}")
```

**HOW**: The function signature is unchanged. Only the internal logic of the non-intervention Windows branch changes.

#### New edge-case tests in `test_workspace.py` (Decision #6)

1. **`test_empty_commands_generates_bare_script`**: Config with `"commands": []` — script has venv section but no command sections, no step labels.
2. **`test_invalid_commands_type_raises_error`**: Config with `"commands": "/single_string"` — raises `ValueError`.
3. **`test_invalid_commands_element_raises_error`**: Config with `"commands": ["/valid", 123]` — raises `ValueError`.

### Verification

Run workspace tests:
```
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-k", "test_workspace"])
```
