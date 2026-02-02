# Step 6: Update test_commands.py - Fix patch locations

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 6: Update test patch locations in test_commands.py to use module-specific paths
(patch where the import is used, not where it's defined).
```

## WHERE

### File to Modify
- `tests/cli/commands/coordinator/test_commands.py`

## WHAT

### Patch Location Changes

Since `commands.py` now imports functions directly, tests must patch at the module where they're used:

```python
# Before (package-level patching)
@patch("mcp_coder.cli.commands.coordinator.JenkinsClient")
@patch("mcp_coder.cli.commands.coordinator.get_jenkins_credentials")
@patch("mcp_coder.cli.commands.coordinator.load_repo_config")
@patch("mcp_coder.cli.commands.coordinator.create_default_config")
@patch("mcp_coder.cli.commands.coordinator.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
@patch("mcp_coder.cli.commands.coordinator.get_cached_eligible_issues")
@patch("mcp_coder.cli.commands.coordinator.dispatch_workflow")
@patch("mcp_coder.cli.commands.coordinator._update_issue_labels_in_cache")

# After (module-specific patching)
@patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
@patch("mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials")
@patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
@patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
@patch("mcp_coder.cli.commands.coordinator.commands.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.commands.IssueBranchManager")
@patch("mcp_coder.cli.commands.coordinator.commands.get_cached_eligible_issues")
@patch("mcp_coder.cli.commands.coordinator.commands.dispatch_workflow")
@patch("mcp_coder.cli.commands.coordinator.commands.update_issue_labels_in_cache")  # renamed!
```

### Classes/Tests to Update

**TestExecuteCoordinatorTest:**
```python
@patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
@patch("mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials")
@patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
@patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
def test_execute_coordinator_test_success(self, ...):
    ...
```

**TestExecuteCoordinatorRun:**
```python
@patch("mcp_coder.cli.commands.coordinator.commands.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.commands.IssueBranchManager")
@patch("mcp_coder.cli.commands.coordinator.commands.JenkinsClient")
@patch("mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials")
@patch("mcp_coder.cli.commands.coordinator.commands.load_repo_config")
@patch("mcp_coder.cli.commands.coordinator.commands.get_cached_eligible_issues")
@patch("mcp_coder.cli.commands.coordinator.commands.dispatch_workflow")
@patch("mcp_coder.cli.commands.coordinator.commands.create_default_config")
def test_execute_coordinator_run_single_repo_success(self, ...):
    ...
```

## HOW

### Find and Replace Pattern

```python
# For all functions imported into commands.py:
# OLD -> NEW
"mcp_coder.cli.commands.coordinator.JenkinsClient" -> "mcp_coder.cli.commands.coordinator.commands.JenkinsClient"
"mcp_coder.cli.commands.coordinator.get_jenkins_credentials" -> "mcp_coder.cli.commands.coordinator.commands.get_jenkins_credentials"
"mcp_coder.cli.commands.coordinator.load_repo_config" -> "mcp_coder.cli.commands.coordinator.commands.load_repo_config"
"mcp_coder.cli.commands.coordinator.create_default_config" -> "mcp_coder.cli.commands.coordinator.commands.create_default_config"
"mcp_coder.cli.commands.coordinator.IssueManager" -> "mcp_coder.cli.commands.coordinator.commands.IssueManager"
"mcp_coder.cli.commands.coordinator.IssueBranchManager" -> "mcp_coder.cli.commands.coordinator.commands.IssueBranchManager"
"mcp_coder.cli.commands.coordinator.get_cached_eligible_issues" -> "mcp_coder.cli.commands.coordinator.commands.get_cached_eligible_issues"
"mcp_coder.cli.commands.coordinator.get_eligible_issues" -> "mcp_coder.cli.commands.coordinator.commands.get_eligible_issues"
"mcp_coder.cli.commands.coordinator.dispatch_workflow" -> "mcp_coder.cli.commands.coordinator.commands.dispatch_workflow"
"mcp_coder.cli.commands.coordinator._update_issue_labels_in_cache" -> "mcp_coder.cli.commands.coordinator.commands.update_issue_labels_in_cache"
```

## ALGORITHM
```
1. Open test_commands.py
2. Find all @patch decorators with path "mcp_coder.cli.commands.coordinator.<name>"
3. For patches of functions used in commands.py:
   - Add ".commands" before the function name
   - Change _update_issue_labels_in_cache to update_issue_labels_in_cache (renamed)
4. Save file
```

## DATA

No data structure changes - only patch path strings change.

## VERIFICATION

After this step:
```bash
# Run the specific test file
pytest tests/cli/commands/coordinator/test_commands.py -v

# All tests should pass
```

## NOTES

- Important: `_update_issue_labels_in_cache` was renamed to `update_issue_labels_in_cache` in Step 1
- Both the path AND the function name change for that particular patch
