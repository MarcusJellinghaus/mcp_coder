# Step 5: Clean Up types.py and __init__.py

## LLM Prompt

```
Implement Step 5 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Remove the 4 hardcoded constants from types.py and their exports from __init__.py.

Requirements:
- Remove from types.py: VSCODECLAUDE_PRIORITY, HUMAN_ACTION_COMMANDS, STATUS_EMOJI, STAGE_DISPLAY_NAMES
- Keep in types.py: TypedDicts and DEFAULT_MAX_SESSIONS, DEFAULT_PROMPT_TIMEOUT
- Remove from __init__.py exports: the 4 constants
- Keep in __init__.py exports: TypedDicts and numeric defaults
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/workflows/vscodeclaude/types.py` | MODIFY - Remove 4 constants |
| `src/mcp_coder/workflows/vscodeclaude/__init__.py` | MODIFY - Remove 4 constant exports |

## WHAT

### types.py - Remove

```python
# REMOVE ALL OF THESE:

# Priority order for human_action statuses (later stages first)
VSCODECLAUDE_PRIORITY: list[str] = [
    "status-10:pr-created",
    "status-07:code-review",
    "status-04:plan-review",
    "status-01:created",
]

# Mapping of status to slash commands
HUMAN_ACTION_COMMANDS: dict[str, tuple[str | None, str | None]] = {
    # status: (initial_command, followup_command)
    "status-01:created": ("/issue_analyse", "/discuss"),
    "status-04:plan-review": ("/plan_review", "/discuss"),
    "status-07:code-review": ("/implementation_review", "/discuss"),
    "status-10:pr-created": (None, None),  # Show PR URL only
}

# Status emoji mapping for banners
STATUS_EMOJI: dict[str, str] = {
    "status-01:created": "📝",
    "status-04:plan-review": "📋",
    "status-07:code-review": "🔍",
    "status-10:pr-created": "🎉",
}

# Stage display name mapping
STAGE_DISPLAY_NAMES: dict[str, str] = {
    "status-01:created": "ISSUE ANALYSIS",
    "status-04:plan-review": "PLAN REVIEW",
    "status-07:code-review": "CODE REVIEW",
    "status-10:pr-created": "PR CREATED",
}
```

### types.py - Keep

```python
# KEEP ALL OF THESE:

class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""
    ...

class VSCodeClaudeSessionStore(TypedDict):
    """Session storage file structure."""
    ...

class VSCodeClaudeConfig(TypedDict):
    """Configuration for vscodeclaude feature."""
    ...

class RepoVSCodeClaudeConfig(TypedDict, total=False):
    """Per-repo vscodeclaude config."""
    ...

# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3

# Default timeout for mcp-coder prompt calls
DEFAULT_PROMPT_TIMEOUT: int = 300
```

### __init__.py - Remove from exports

```python
# REMOVE these imports and __all__ entries:
VSCODECLAUDE_PRIORITY,
HUMAN_ACTION_COMMANDS,
STATUS_EMOJI,
STAGE_DISPLAY_NAMES,
```

### __init__.py - Keep

```python
# KEEP these:
from .types import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_PROMPT_TIMEOUT,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)

# And in __all__:
"VSCodeClaudeSession",
"VSCodeClaudeSessionStore",
"VSCodeClaudeConfig",
"RepoVSCodeClaudeConfig",
"DEFAULT_MAX_SESSIONS",
"DEFAULT_PROMPT_TIMEOUT",
```

## HOW

### Integration Points
- After Steps 2-4, no code should import these constants anymore
- This step is a clean removal

### Verification Before Removal
Run grep to ensure no remaining imports:
```bash
grep -r "VSCODECLAUDE_PRIORITY\|HUMAN_ACTION_COMMANDS\|STATUS_EMOJI\|STAGE_DISPLAY_NAMES" src/
```

## DATA

### types.py Final State

```python
"""Type definitions and constants for vscodeclaude feature."""

from typing import TypedDict


class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""

    folder: str  # Full path to working folder
    repo: str  # "owner/repo" format
    issue_number: int
    status: str  # e.g., "status-07:code-review"
    vscode_pid: int | None
    started_at: str  # ISO 8601
    is_intervention: bool


class VSCodeClaudeSessionStore(TypedDict):
    """Session storage file structure."""

    sessions: list[VSCodeClaudeSession]
    last_updated: str  # ISO 8601


class VSCodeClaudeConfig(TypedDict):
    """Configuration for vscodeclaude feature."""

    workspace_base: str
    max_sessions: int


class RepoVSCodeClaudeConfig(TypedDict, total=False):
    """Per-repo vscodeclaude config (extends existing repo config)."""

    setup_commands_windows: list[str]
    setup_commands_linux: list[str]


# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3

# Default timeout for mcp-coder prompt calls in startup scripts (seconds)
DEFAULT_PROMPT_TIMEOUT: int = 300  # 5 minutes
```

### __init__.py Types Section Final State

```python
# Types and constants
from .types import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_PROMPT_TIMEOUT,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)
```

### __init__.py __all__ Section - Types Portion

```python
__all__ = [
    # Types
    "VSCodeClaudeSession",
    "VSCodeClaudeSessionStore",
    "VSCodeClaudeConfig",
    "RepoVSCodeClaudeConfig",
    # Constants (only numeric defaults remain)
    "DEFAULT_MAX_SESSIONS",
    "DEFAULT_PROMPT_TIMEOUT",
    # ... rest of exports unchanged
]
```

## TEST IMPLEMENTATION

No new tests needed - just verify existing tests pass after removal.

### Verification Tests

```python
# In test_types.py - REMOVE these tests that reference removed constants:

def test_vscodeclaude_priority_order(self) -> None:
    """Priority list has correct order (later stages first)."""
    # REMOVE

def test_human_action_commands_coverage(self) -> None:
    """All priority statuses have command mappings."""
    # REMOVE

def test_status_emoji_coverage(self) -> None:
    """All priority statuses have emoji mappings."""
    # REMOVE

def test_vscodeclaude_priority_completeness(self) -> None:
    """All expected statuses are in the priority list."""
    # REMOVE

def test_human_action_commands_structure(self) -> None:
    """Human action commands have correct structure."""
    # REMOVE

def test_status_emoji_structure(self) -> None:
    """Status emoji mappings have correct structure."""
    # REMOVE

def test_stage_display_names_coverage(self) -> None:
    """All priority statuses have display names."""
    # REMOVE
```

## VERIFICATION

After implementation:
1. Verify constants are gone: `grep -r "VSCODECLAUDE_PRIORITY" src/` should return nothing
2. Run all tests: `pytest tests/workflows/vscodeclaude/ -v`
3. Verify imports work: `python -c "from mcp_coder.workflows.vscodeclaude import DEFAULT_MAX_SESSIONS; print(DEFAULT_MAX_SESSIONS)"`
4. Verify removed exports fail: `python -c "from mcp_coder.workflows.vscodeclaude import VSCODECLAUDE_PRIORITY"` should raise ImportError
