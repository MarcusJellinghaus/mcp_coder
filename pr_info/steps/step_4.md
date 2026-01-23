# Step 4: Issue Selection & Configuration

## LLM Prompt

```
Implement Step 4 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Config loading, GitHub username detection, issue filtering for human_action.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/coordinator/vscodeclaude.py` | Add config and filtering functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add config and filtering tests |

## WHAT

### vscodeclaude.py - Configuration Functions

```python
def load_vscodeclaude_config() -> VSCodeClaudeConfig:
    """Load vscodeclaude configuration from config.toml.
    
    Returns:
        VSCodeClaudeConfig with workspace_base and max_sessions
        
    Raises:
        ValueError: If workspace_base not configured or doesn't exist
    """

def load_repo_vscodeclaude_config(repo_name: str) -> RepoVSCodeClaudeConfig:
    """Load repo-specific vscodeclaude config (setup commands).
    
    Args:
        repo_name: Repository name from config (e.g., "mcp_coder")
        
    Returns:
        RepoVSCodeClaudeConfig with optional setup_commands_windows/linux
    """

def get_github_username() -> str:
    """Get authenticated GitHub username via PyGithub API.
    
    Returns:
        GitHub username string
        
    Raises:
        ValueError: If GitHub authentication fails
    """

def sanitize_folder_name(name: str) -> str:
    """Sanitize string for use in folder names.
    
    Args:
        name: Input string (e.g., repo name)
        
    Returns:
        String with only alphanumeric, dash, underscore chars
    """
```

### vscodeclaude.py - Issue Filtering Functions

```python
def get_human_action_labels() -> set[str]:
    """Get set of human_action status labels from labels.json.
    
    Returns:
        Set of label names with category="human_action"
    """

def get_eligible_vscodeclaude_issues(
    issue_manager: IssueManager,
    github_username: str,
) -> List[IssueData]:
    """Get issues eligible for vscodeclaude sessions.
    
    Filters for:
    - Open issues only
    - Exactly one human_action label
    - Assigned to github_username
    - No ignore_labels
    
    Args:
        issue_manager: IssueManager for GitHub API
        github_username: Username to filter assignments
        
    Returns:
        List of eligible issues sorted by priority (later stages first)
    """

def get_linked_branch_for_issue(
    branch_manager: IssueBranchManager,
    issue_number: int,
) -> Optional[str]:
    """Get linked branch for issue, fail if multiple.
    
    Args:
        branch_manager: IssueBranchManager for GitHub API
        issue_number: GitHub issue number
        
    Returns:
        Branch name if exactly one linked, None if none
        
    Raises:
        ValueError: If multiple branches linked to issue
    """
```

## HOW

### Integration Points

1. Uses `get_config_values()` from `user_config.py` (via `_get_coordinator()` pattern)
2. Uses `load_labels_config()` for human_action labels
3. Uses `IssueManager.list_issues()` and `IssueBranchManager.get_linked_branches()`
4. Reuses `ignore_labels` from `labels.json` (same as `coordinator run`)

### Config Structure

```toml
[coordinator.vscodeclaude]
workspace_base = "C:\\Users\\Marcus\\Documents\\GitHub"
max_sessions = 3

[coordinator.repos.mcp_coder]
setup_commands_windows = ["uv venv", "uv sync --extra types"]
setup_commands_linux = ["uv venv", "uv sync --extra types"]
```

## ALGORITHM

### load_vscodeclaude_config()
```
1. Use get_config_values for coordinator.vscodeclaude section
2. Get workspace_base (required) - raise ValueError if missing
3. Validate workspace_base path exists - raise ValueError if not
4. Get max_sessions with DEFAULT_MAX_SESSIONS fallback
5. Return VSCodeClaudeConfig
```

### get_eligible_vscodeclaude_issues()
```
1. Load human_action labels and ignore_labels from labels.json
2. Get all open issues via issue_manager.list_issues()
3. Filter: has exactly one human_action label
4. Filter: assigned to github_username (check assignees list)
5. Filter: no ignore_labels present
6. Sort by VSCODECLAUDE_PRIORITY (status-10 first, status-01 last)
7. Return sorted list
```

### get_github_username()
```
1. Get GitHub token from config (same path as IssueManager)
2. Create PyGithub Github instance
3. Call github.get_user().login
4. Return username string
```

## DATA

### Priority Sorting

Issues sorted by `VSCODECLAUDE_PRIORITY` index (lower = higher priority):
- status-10:pr-created → index 0 (highest)
- status-07:code-review → index 1
- status-04:plan-review → index 2
- status-01:created → index 3 (lowest)

### Test Coverage

```python
# test_vscodeclaude.py

class TestConfiguration:
    """Test configuration loading."""
    
    def test_load_vscodeclaude_config_success(self, monkeypatch):
        """Loads config with valid workspace_base."""
        mock_config = {
            ("coordinator.vscodeclaude", "workspace_base"): "/valid/path",
            ("coordinator.vscodeclaude", "max_sessions"): "5",
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"get_config_values": lambda keys: mock_config})()
        )
        # Mock path existence
        monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
        
        config = load_vscodeclaude_config()
        assert config["workspace_base"] == "/valid/path"
        assert config["max_sessions"] == 5
    
    def test_load_vscodeclaude_config_missing_workspace_base(self, monkeypatch):
        """Raises ValueError when workspace_base missing."""
        mock_config = {
            ("coordinator.vscodeclaude", "workspace_base"): None,
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"get_config_values": lambda keys: mock_config})()
        )
        
        with pytest.raises(ValueError, match="workspace_base"):
            load_vscodeclaude_config()
    
    def test_load_vscodeclaude_config_default_max_sessions(self, monkeypatch):
        """Uses default when max_sessions not set."""
        mock_config = {
            ("coordinator.vscodeclaude", "workspace_base"): "/valid/path",
            ("coordinator.vscodeclaude", "max_sessions"): None,
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"get_config_values": lambda keys: mock_config})()
        )
        monkeypatch.setattr("pathlib.Path.exists", lambda self: True)
        
        config = load_vscodeclaude_config()
        assert config["max_sessions"] == DEFAULT_MAX_SESSIONS
    
    def test_sanitize_folder_name(self):
        """Removes invalid characters from folder names."""
        assert sanitize_folder_name("mcp-coder") == "mcp-coder"
        assert sanitize_folder_name("my repo!@#$") == "my-repo"
        assert sanitize_folder_name("test_project") == "test_project"
        assert sanitize_folder_name("a/b\\c:d") == "a-b-c-d"


class TestIssueSelection:
    """Test issue filtering for vscodeclaude."""
    
    def test_get_human_action_labels(self, monkeypatch):
        """Extracts human_action labels from config."""
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-04:plan-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"]
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"load_labels_config": lambda path: mock_labels_config})()
        )
        
        labels = get_human_action_labels()
        assert "status-01:created" in labels
        assert "status-04:plan-review" in labels
        assert "status-02:awaiting-planning" not in labels
    
    def test_get_eligible_issues_filters_by_assignment(self, monkeypatch):
        """Only returns issues assigned to user."""
        mock_issues = [
            {"number": 1, "state": "open", "labels": ["status-07:code-review"], 
             "assignees": [{"login": "testuser"}]},
            {"number": 2, "state": "open", "labels": ["status-07:code-review"], 
             "assignees": [{"login": "otheruser"}]},
            {"number": 3, "state": "open", "labels": ["status-07:code-review"], 
             "assignees": []},  # Unassigned
        ]
        
        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues
        
        # Mock labels config
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": []
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"load_labels_config": lambda path: mock_labels_config})()
        )
        
        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "testuser")
        
        assert len(eligible) == 1
        assert eligible[0]["number"] == 1
    
    def test_get_eligible_issues_priority_order(self, monkeypatch):
        """Issues sorted by priority (later stages first)."""
        mock_issues = [
            {"number": 1, "state": "open", "labels": ["status-01:created"], 
             "assignees": [{"login": "user"}]},
            {"number": 2, "state": "open", "labels": ["status-07:code-review"], 
             "assignees": [{"login": "user"}]},
            {"number": 3, "state": "open", "labels": ["status-04:plan-review"], 
             "assignees": [{"login": "user"}]},
        ]
        
        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues
        
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-04:plan-review", "category": "human_action"},
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": []
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"load_labels_config": lambda path: mock_labels_config})()
        )
        
        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")
        
        # Should be: code-review, plan-review, created
        assert eligible[0]["labels"][0] == "status-07:code-review"
        assert eligible[1]["labels"][0] == "status-04:plan-review"
        assert eligible[2]["labels"][0] == "status-01:created"
    
    def test_get_eligible_issues_excludes_ignore_labels(self, monkeypatch):
        """Skips issues with ignore_labels."""
        mock_issues = [
            {"number": 1, "state": "open", "labels": ["status-07:code-review", "Overview"], 
             "assignees": [{"login": "user"}]},
            {"number": 2, "state": "open", "labels": ["status-07:code-review"], 
             "assignees": [{"login": "user"}]},
        ]
        
        mock_issue_manager = Mock()
        mock_issue_manager.list_issues.return_value = mock_issues
        
        mock_labels_config = {
            "workflow_labels": [
                {"name": "status-07:code-review", "category": "human_action"},
            ],
            "ignore_labels": ["Overview"]
        }
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude._get_coordinator",
            lambda: type("M", (), {"load_labels_config": lambda path: mock_labels_config})()
        )
        
        eligible = get_eligible_vscodeclaude_issues(mock_issue_manager, "user")
        
        assert len(eligible) == 1
        assert eligible[0]["number"] == 2
    
    def test_get_linked_branch_single(self):
        """Returns branch when exactly one linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["feature-123"]
        
        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch == "feature-123"
    
    def test_get_linked_branch_none(self):
        """Returns None when no branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = []
        
        branch = get_linked_branch_for_issue(mock_branch_manager, 123)
        assert branch is None
    
    def test_get_linked_branch_multiple_raises(self):
        """Raises ValueError when multiple branches linked."""
        mock_branch_manager = Mock()
        mock_branch_manager.get_linked_branches.return_value = ["branch-a", "branch-b"]
        
        with pytest.raises(ValueError, match="multiple branches"):
            get_linked_branch_for_issue(mock_branch_manager, 123)
```

## Verification

```bash
# Run configuration tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestConfiguration -v

# Run issue selection tests
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestIssueSelection -v

# Type check
mypy src/mcp_coder/cli/commands/coordinator/vscodeclaude.py
```
