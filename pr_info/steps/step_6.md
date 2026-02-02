# Step 6: Final Test Cleanup and Verification

## LLM Prompt

```
Implement Step 6 of Issue #359 (see pr_info/steps/summary.md for context).

Task: Final cleanup of test files and verification that all tests pass.

Requirements:
- Remove tests that assert hardcoded constant values
- Update tests that import removed constants
- Ensure all mocks are updated to use _load_labels_config
- Run full test suite and fix any failures
- Verify all acceptance criteria are met
```

## WHERE

| File | Action |
|------|--------|
| `tests/workflows/vscodeclaude/test_types.py` | MODIFY - Remove constant tests |
| `tests/workflows/vscodeclaude/test_issues.py` | VERIFY - Tests should pass |
| `tests/workflows/vscodeclaude/test_workspace.py` | VERIFY - Tests should pass |
| `tests/workflows/vscodeclaude/test_helpers.py` | MODIFY - Remove constant imports |

## WHAT

### test_types.py - Tests to REMOVE

Remove entire `TestTypes` class tests that reference removed constants:
- `test_vscodeclaude_priority_order`
- `test_human_action_commands_coverage`
- `test_status_emoji_coverage`
- `test_vscodeclaude_priority_completeness`
- `test_human_action_commands_structure`
- `test_status_emoji_structure`

Keep:
- `test_default_max_sessions`

Remove from `TestTypeHints`:
- `test_stage_display_names_coverage`

### test_types.py - Tests to KEEP

Keep all `TestTypeHints` tests for TypedDicts:
- `test_vscodeclaude_session_type_structure`
- `test_vscodeclaude_session_store_type_structure`
- `test_vscodeclaude_config_type_structure`
- `test_repo_vscodeclaude_config_type_structure`
- `test_vscodeclaude_session_creation`
- `test_vscodeclaude_session_store_creation`
- `test_vscodeclaude_config_creation`
- `test_repo_vscodeclaude_config_creation`
- `test_repo_vscodeclaude_config_partial`

Keep test added in Step 1:
- `TestLabelsJsonVscodeclaudeMetadata` class

### test_helpers.py - Update Imports

```python
# REMOVE these imports:
from mcp_coder.workflows.vscodeclaude.types import (
    STAGE_DISPLAY_NAMES,
    VSCODECLAUDE_PRIORITY,
)

# Tests should now mock _load_labels_config instead
```

## HOW

### Test Update Strategy

1. **test_types.py**: Delete tests that test removed constants
2. **test_helpers.py**: Remove unused imports, tests already updated in Step 4
3. **test_workspace.py**: Tests already updated in Step 3
4. **test_issues.py**: Tests already updated in Step 2

## FULL CODE CHANGES

### test_types.py - Final State

```python
"""Test type definitions and constants for VSCode Claude session management."""

import json
from importlib import resources
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.types import (
    DEFAULT_MAX_SESSIONS,
    RepoVSCodeClaudeConfig,
    VSCodeClaudeConfig,
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
)


class TestTypes:
    """Test type definitions and constants."""

    def test_default_max_sessions(self) -> None:
        """Default max sessions is 3."""
        assert DEFAULT_MAX_SESSIONS == 3


class TestTypeHints:
    """Test TypedDict structure validation."""

    def test_vscodeclaude_session_type_structure(self) -> None:
        """VSCodeClaudeSession has all required fields."""
        annotations = VSCodeClaudeSession.__annotations__
        expected_fields = {
            "folder",
            "repo",
            "issue_number",
            "status",
            "vscode_pid",
            "started_at",
            "is_intervention",
        }
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_session_store_type_structure(self) -> None:
        """VSCodeClaudeSessionStore has all required fields."""
        annotations = VSCodeClaudeSessionStore.__annotations__
        expected_fields = {"sessions", "last_updated"}
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_config_type_structure(self) -> None:
        """VSCodeClaudeConfig has all required fields."""
        annotations = VSCodeClaudeConfig.__annotations__
        expected_fields = {"workspace_base", "max_sessions"}
        assert set(annotations.keys()) == expected_fields

    def test_repo_vscodeclaude_config_type_structure(self) -> None:
        """RepoVSCodeClaudeConfig has all expected fields."""
        annotations = RepoVSCodeClaudeConfig.__annotations__
        expected_fields = {"setup_commands_windows", "setup_commands_linux"}
        assert set(annotations.keys()) == expected_fields

    def test_vscodeclaude_session_creation(self) -> None:
        """Can create a valid VSCodeClaudeSession instance."""
        session: VSCodeClaudeSession = {
            "folder": "/path/to/folder",
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": 1234,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        assert isinstance(session["folder"], str)
        assert isinstance(session["repo"], str)
        assert isinstance(session["issue_number"], int)
        assert isinstance(session["status"], str)
        assert session["vscode_pid"] is None or isinstance(session["vscode_pid"], int)
        assert isinstance(session["started_at"], str)
        assert isinstance(session["is_intervention"], bool)

    def test_vscodeclaude_session_store_creation(self) -> None:
        """Can create a valid VSCodeClaudeSessionStore instance."""
        store: VSCodeClaudeSessionStore = {
            "sessions": [],
            "last_updated": "2024-01-01T00:00:00Z",
        }
        assert isinstance(store["sessions"], list)
        assert isinstance(store["last_updated"], str)

    def test_vscodeclaude_config_creation(self) -> None:
        """Can create a valid VSCodeClaudeConfig instance."""
        config: VSCodeClaudeConfig = {
            "workspace_base": "/path/to/workspace",
            "max_sessions": 5,
        }
        assert isinstance(config["workspace_base"], str)
        assert isinstance(config["max_sessions"], int)

    def test_repo_vscodeclaude_config_creation(self) -> None:
        """Can create a valid RepoVSCodeClaudeConfig instance."""
        config: RepoVSCodeClaudeConfig = {
            "setup_commands_windows": ["cmd1", "cmd2"],
            "setup_commands_linux": ["cmd3", "cmd4"],
        }
        assert isinstance(config["setup_commands_windows"], list)
        assert isinstance(config["setup_commands_linux"], list)

    def test_repo_vscodeclaude_config_partial(self) -> None:
        """Can create a partial RepoVSCodeClaudeConfig instance."""
        config: RepoVSCodeClaudeConfig = {"setup_commands_windows": ["cmd1"]}
        assert "setup_commands_windows" in config
        assert "setup_commands_linux" not in config


class TestLabelsJsonVscodeclaudeMetadata:
    """Test that labels.json has required vscodeclaude metadata."""

    def test_human_action_labels_have_vscodeclaude_metadata(self) -> None:
        """All human_action labels have required vscodeclaude fields."""
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))

        human_action_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label["category"] == "human_action"
        ]

        assert len(human_action_labels) == 4

        required_fields = {
            "emoji",
            "display_name",
            "stage_short",
            "initial_command",
            "followup_command",
        }

        for label in human_action_labels:
            assert "vscodeclaude" in label, f"Missing vscodeclaude in {label['name']}"
            vscodeclaude = label["vscodeclaude"]
            assert (
                set(vscodeclaude.keys()) == required_fields
            ), f"Wrong fields in {label['name']}"

    def test_pr_created_has_null_commands(self) -> None:
        """status-10:pr-created should have null commands."""
        config_resource = resources.files("mcp_coder.config") / "labels.json"
        config_path = Path(str(config_resource))
        labels_config = json.loads(config_path.read_text(encoding="utf-8"))

        pr_created = next(
            label
            for label in labels_config["workflow_labels"]
            if label["name"] == "status-10:pr-created"
        )

        assert pr_created["vscodeclaude"]["initial_command"] is None
        assert pr_created["vscodeclaude"]["followup_command"] is None
```

### test_helpers.py - Update Imports

```python
# REMOVE these imports at top of file:
from mcp_coder.workflows.vscodeclaude.types import (
    STAGE_DISPLAY_NAMES,
    VSCODECLAUDE_PRIORITY,
)

# REMOVE this test:
def test_stage_display_names_coverage(self) -> None:
    """All priority statuses have display names."""
    for status in VSCODECLAUDE_PRIORITY:
        assert status in STAGE_DISPLAY_NAMES
```

## VERIFICATION CHECKLIST

Run these commands to verify implementation:

```bash
# 1. All vscodeclaude tests pass
pytest tests/workflows/vscodeclaude/ -v

# 2. No remaining imports of removed constants
grep -r "VSCODECLAUDE_PRIORITY\|HUMAN_ACTION_COMMANDS\|STATUS_EMOJI\|STAGE_DISPLAY_NAMES" src/
# Should return nothing

# 3. No remaining imports in tests (except mocks)
grep -r "from mcp_coder.workflows.vscodeclaude.types import.*VSCODECLAUDE_PRIORITY" tests/
# Should return nothing

# 4. Module exports work correctly
python -c "from mcp_coder.workflows.vscodeclaude import DEFAULT_MAX_SESSIONS, VSCodeClaudeSession; print('OK')"

# 5. Removed exports fail as expected
python -c "from mcp_coder.workflows.vscodeclaude import VSCODECLAUDE_PRIORITY" 2>&1 | grep -q "ImportError" && echo "OK - correctly raises ImportError"

# 6. Full test suite
pytest tests/ -v --tb=short
```

## ACCEPTANCE CRITERIA VERIFICATION

| Criterion | How to Verify |
|-----------|---------------|
| labels.json contains vscodeclaude object for all 4 human_action labels | `test_human_action_labels_have_vscodeclaude_metadata` passes |
| types.py no longer has hardcoded label lists | `grep "VSCODECLAUDE_PRIORITY" src/mcp_coder/workflows/vscodeclaude/types.py` returns nothing |
| Constants removed from __init__.py exports | Import statements fail for removed constants |
| All vscodeclaude functionality works identically | All existing behavior tests pass |
| Adding a new human_action label only requires updating labels.json | Architecture review - no hardcoded lists remain |
| All existing tests pass (updated) | `pytest tests/workflows/vscodeclaude/ -v` all green |
| No new hardcoded status label strings introduced | Code review of changes |
