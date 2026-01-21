# Step 5: Code Review Refactoring

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Decisions**: `pr_info/steps/Decisions.md` (#10-15)

## LLM Prompt
```
Implement Step 5 from pr_info/steps/summary.md:
Apply code review refactoring changes based on Decisions #10-15.
This includes reorganizing imports in test file, simplifying test fixture,
moving `_build_set_status_epilog()` from main.py to set_status.py,
updating slash command descriptions, and renaming implementation_tasks.
```

## WHERE
- **Files to modify**:
  1. `tests/cli/commands/test_set_status.py` - Import reorganization, fixture simplification
  2. `src/mcp_coder/cli/commands/set_status.py` - Add `build_set_status_epilog()` function
  3. `src/mcp_coder/cli/main.py` - Remove helper function and unused imports
  4. `.claude/commands/implementation_needs_rework.md` - Update description
  5. `.claude/commands/implementation_tasks.md` → `.claude/commands/implementation_new_tasks.md` - Rename file

## WHAT - Changes Required

### 1. Test File Import Reorganization (Decision #10)

**Remove** commented-out import block (lines 40-46):
```python
# Import will be added once module exists
# from mcp_coder.cli.commands.set_status import (
#     compute_new_labels,
#     execute_set_status,
#     get_status_labels_from_config,
#     validate_status_label,
# )
```

**Add** imports at top of file (after other imports):
```python
from mcp_coder.cli.commands.set_status import (
    compute_new_labels,
    execute_set_status,
    get_status_labels_from_config,
    validate_status_label,
)
```

**Remove** per-method imports like:
```python
from mcp_coder.cli.commands.set_status import get_status_labels_from_config
```

### 2. Simplify Test Fixture (Decision #11)

**Replace** the verbose `full_labels_config` fixture (~80 lines) with:
```python
@pytest.fixture
def full_labels_config(labels_config_path: Path) -> Dict[str, Any]:
    """Load labels configuration from actual config file.

    Args:
        labels_config_path: Path to labels.json from conftest fixture

    Returns:
        Dict with 'workflow_labels' matching the structure from config/labels.json
    """
    from mcp_coder.utils.github_operations.label_config import load_labels_config
    return load_labels_config(labels_config_path)
```

### 3. Move Epilog Builder to set_status.py (Decision #12)

**Add** to `src/mcp_coder/cli/commands/set_status.py`:
```python
def build_set_status_epilog() -> str:
    """Build epilog text with available labels from config.
    
    Returns:
        Formatted string with available status labels and examples,
        or fallback message if config cannot be loaded.
    """
    try:
        # Use package bundled config (always available)
        config_path = get_labels_config_path(None)
        labels_config = load_labels_config(config_path)

        lines = ["Available status labels:"]
        for label in labels_config["workflow_labels"]:
            lines.append(f"  {label['name']:30} {label['description']}")
        lines.append("")
        lines.append("Examples:")
        lines.append("  mcp-coder set-status status-05:plan-ready")
        lines.append("  mcp-coder set-status status-08:ready-pr --issue 123")
        return "\n".join(lines)
    except Exception as e:
        # Log at debug level to aid troubleshooting (Decision #9)
        logger.debug(f"Failed to build set-status epilog: {e}")
        return "Run in a project directory to see available status labels."
```

### 4. Update main.py (Decision #12)

**Remove** from `src/mcp_coder/cli/main.py`:
- The `_build_set_status_epilog()` function (lines 27-44)
- The unused imports:
  ```python
  from ..utils.github_operations.label_config import (
      get_labels_config_path,
      load_labels_config,
  )
  ```

**Update** the import for set_status:
```python
from .commands.set_status import build_set_status_epilog, execute_set_status
```

**Update** the subparser to use the new import:
```python
epilog=build_set_status_epilog(),  # Now imported from set_status module
```

### 5. Update `/implementation_needs_rework` Description (Decision #14)

**Update** `.claude/commands/implementation_needs_rework.md`:
```markdown
---
allowed-tools: Bash(mcp-coder set-status:*)
---

# Implementation Needs Rework

Set status to plan-ready after creating new steps (and pushing them) from code review findings.

**Typical workflow:**
1. `/implementation_review` - identifies issues
2. `/discuss` - discuss and decide on changes  
3. `/implementation_new_tasks` - create additional implementation steps
4. `/commit_push` - commit the updated plan
5. **This command** - transition to plan-ready
6. `mcp-coder implement` - process the new steps

**Instructions:**
1. Run the set-status command to update the issue label:
```bash
mcp-coder set-status status-05:plan-ready
```

2. Confirm the status change was successful.

**Effect:** Changes issue status from `status-07:code-review` to `status-05:plan-ready` for rework.
```

### 6. Rename `/implementation_tasks` to `/implementation_new_tasks` (Decision #15)

**Rename** file:
- From: `.claude/commands/implementation_tasks.md`
- To: `.claude/commands/implementation_new_tasks.md`

No content changes needed - just the file rename.

## HOW - Integration Points

The epilog builder function changes from private (`_build_set_status_epilog`) to public (`build_set_status_epilog`) since it's now exported for use by main.py.

## ALGORITHM - No complex logic changes

This is a refactoring step - no algorithmic changes, only code reorganization.

## DATA - No data structure changes

Return values and data structures remain unchanged.

## Verification

After implementation:
1. All existing tests must pass
2. `mcp-coder set-status --help` must display the same output as before
3. No pylint/mypy errors
4. Slash commands are recognized with new names
