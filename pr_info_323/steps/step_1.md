# Step 1: Dependencies & Configuration Types

## LLM Prompt

```
Implement Step 1 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Add psutil dependency and create TypedDict definitions.
```

## WHERE

| File | Action |
|------|--------|
| `pyproject.toml` | Modify - add `psutil` dependency |
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Create - TypedDicts and constants |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Create - tests for types |

## WHAT

### pyproject.toml

Add to `dependencies` list:
```toml
"psutil>=5.9.0",
```

### vscodeclaude.py - Type Definitions

```python
"""VSCode Claude session management for interactive workflow stages."""

from typing import TypedDict, Optional, List
from datetime import datetime

class VSCodeClaudeSession(TypedDict):
    """Single session tracking data."""
    folder: str              # Full path to working folder
    repo: str                # "owner/repo" format
    issue_number: int
    status: str              # e.g., "status-07:code-review"
    vscode_pid: Optional[int]
    started_at: str          # ISO 8601
    is_intervention: bool

class VSCodeClaudeSessionStore(TypedDict):
    """Session storage file structure."""
    sessions: List[VSCodeClaudeSession]
    last_updated: str        # ISO 8601

class VSCodeClaudeConfig(TypedDict):
    """Configuration for vscodeclaude feature."""
    workspace_base: str
    max_sessions: int

class RepoVSCodeClaudeConfig(TypedDict, total=False):
    """Per-repo vscodeclaude config (extends existing repo config)."""
    setup_commands_windows: List[str]
    setup_commands_linux: List[str]
```

### vscodeclaude.py - Constants

```python
# Priority order for human_action statuses (later stages first)
VSCODECLAUDE_PRIORITY: List[str] = [
    "status-10:pr-created",
    "status-07:code-review",
    "status-04:plan-review",
    "status-01:created",
]

# Mapping of status to slash commands
HUMAN_ACTION_COMMANDS: dict[str, tuple[str, str]] = {
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

# Default max sessions
DEFAULT_MAX_SESSIONS: int = 3
```

## HOW

### Integration Points

1. `psutil` imported only where needed (lazy import in session checking functions)
2. TypedDicts used for type hints throughout module
3. Constants imported in tests for validation

## ALGORITHM

```
N/A - This step only defines types and constants, no logic.
```

## DATA

### Return Values

TypedDicts provide type safety for:
- Session JSON serialization/deserialization
- Config loading validation
- Function signatures throughout module

### Test Coverage

```python
# test_vscodeclaude.py

class TestTypes:
    """Test type definitions and constants."""
    
    def test_vscodeclaude_priority_order(self):
        """Priority list has correct order (later stages first)."""
        assert VSCODECLAUDE_PRIORITY[0] == "status-10:pr-created"
        assert VSCODECLAUDE_PRIORITY[-1] == "status-01:created"
    
    def test_human_action_commands_coverage(self):
        """All priority statuses have command mappings."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in HUMAN_ACTION_COMMANDS
    
    def test_status_emoji_coverage(self):
        """All priority statuses have emoji mappings."""
        for status in VSCODECLAUDE_PRIORITY:
            assert status in STATUS_EMOJI
    
    def test_default_max_sessions(self):
        """Default max sessions is 3."""
        assert DEFAULT_MAX_SESSIONS == 3


class TestIntegration:
    """Integration tests for end-to-end workflow."""
    
    def test_complete_session_workflow(self, tmp_path, monkeypatch):
        """Test complete session creation and launch workflow."""
        # Will test the full flow from config loading to VSCode launch
        pass
        
    def test_session_cleanup_workflow(self, tmp_path, monkeypatch):
        """Test session stale detection and cleanup workflow."""
        # Will test stale session detection and cleanup
        pass
```

## Verification

```bash
# Install updated dependencies
uv sync

# Run type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py

# Run tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestTypes -v
```
