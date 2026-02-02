# Step 5: Update test_core.py - Fix patch locations

## LLM Prompt
```
You are implementing Issue #365: Refactor coordinator - Remove _get_coordinator() late-binding pattern.
See pr_info/steps/summary.md for full context.

This is Step 5: Update test patch locations in test_core.py to use module-specific paths
(patch where the import is used, not where it's defined).
```

## WHERE

### File to Modify
- `tests/cli/commands/coordinator/test_core.py`

## WHAT

### Patch Location Changes

Since `core.py` now imports `get_config_values` and `load_labels_config` directly,
tests must patch at the module where they're used:

```python
# Before (package-level patching)
@patch("mcp_coder.cli.commands.coordinator.get_config_values")
@patch("mcp_coder.cli.commands.coordinator.load_labels_config")

# After (module-specific patching)
@patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
@patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
```

### Classes/Tests to Update

**TestLoadRepoConfig:**
```python
# All tests that patch get_config_values
@patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
def test_load_repo_config_success(self, mock_get_config):
    ...
```

**TestGetJenkinsCredentials:**
```python
@patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
def test_get_jenkins_credentials_from_config(self, mock_get_config, monkeypatch):
    ...
```

**TestGetEligibleIssues:**
```python
@patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
def test_get_eligible_issues_filters_by_bot_pickup_labels(self, ...):
    ...
```

## HOW

### Find and Replace Pattern

```python
# Find all occurrences of:
@patch("mcp_coder.cli.commands.coordinator.get_config_values")
@patch("mcp_coder.cli.commands.coordinator.load_labels_config")
@patch("mcp_coder.cli.commands.coordinator.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.IssueBranchManager")
@patch("mcp_coder.cli.commands.coordinator.JenkinsClient")

# Replace with:
@patch("mcp_coder.cli.commands.coordinator.core.get_config_values")
@patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
@patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
@patch("mcp_coder.cli.commands.coordinator.core.IssueBranchManager")
@patch("mcp_coder.cli.commands.coordinator.core.JenkinsClient")
```

Note: Some patches in test_core.py may already use the correct path if they're testing
functions that don't go through the coordinator pattern. Review each patch individually.

## ALGORITHM
```
1. Open test_core.py
2. Find all @patch decorators with path "mcp_coder.cli.commands.coordinator.<name>"
3. For patches of functions used in core.py:
   - get_config_values -> ...coordinator.core.get_config_values
   - load_labels_config -> ...coordinator.core.load_labels_config
4. Keep patches that already target the correct module unchanged
5. Save file
```

## DATA

No data structure changes - only patch path strings change.

## VERIFICATION

After this step:
```bash
# Run the specific test file
pytest tests/cli/commands/coordinator/test_core.py -v

# All tests should pass
```

## NOTES

- The principle: patch where the name is **looked up**, not where it's **defined**
- Since `core.py` imports `get_config_values` directly, we patch `...core.get_config_values`
- The `@patch` decorator intercepts the name lookup in the specified module
