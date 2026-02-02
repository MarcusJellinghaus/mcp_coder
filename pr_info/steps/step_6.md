# Step 6: coordinator issue-stats CLI Wiring

## LLM Prompt
```
Implement Step 6 of Issue #340. Reference: pr_info/steps/summary.md

Wire the coordinator issue-stats command into the CLI:
1. Add execute_coordinator_issue_stats() entry point
2. Register subcommand in main.py
3. Add argument parsing

Follow TDD: Write tests first, then implement.
```

---

## WHERE

| File | Action |
|------|--------|
| `tests/cli/commands/coordinator/test_issue_stats.py` | Add CLI tests |
| `src/mcp_coder/cli/commands/coordinator/issue_stats.py` | Add execute function |
| `src/mcp_coder/cli/main.py` | Add subcommand |

---

## WHAT

### New Function in `issue_stats.py`

```python
def execute_coordinator_issue_stats(args: argparse.Namespace) -> int:
    """Execute coordinator issue-stats command.
    
    Args:
        args: Parsed arguments with:
            - project_dir: Optional project directory path
            - filter: Category filter ('all', 'human', 'bot')
            - details: Show individual issue details
            
    Returns:
        Exit code (0 for success, 1 for error)
    """
```

### CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--filter` | choice | `"all"` | Filter: `human`, `bot`, `all` |
| `--details` | flag | `False` | Show individual issue details |
| `--project-dir` | path | cwd | Project directory path |

### Test Classes

```python
class TestParseArguments:
    """Test argument parsing for issue-stats."""
    
    def test_default_values(self) -> None: ...
    def test_filter_human(self) -> None: ...
    def test_filter_bot(self) -> None: ...
    def test_details_flag(self) -> None: ...
    def test_project_dir_argument(self) -> None: ...


class TestExecuteCoordinatorIssueStats:
    """Test execute_coordinator_issue_stats function."""
    
    def test_returns_zero_on_success(self) -> None: ...
    def test_returns_one_on_error(self) -> None: ...
    def test_applies_filter_argument(self) -> None: ...
    def test_applies_details_argument(self) -> None: ...
```

---

## HOW

### Changes to `main.py`

```python
# In create_parser() function, under coordinator subparsers:

issue_stats_parser = coordinator_subparsers.add_parser(
    "issue-stats",
    help="Display issue statistics by workflow status"
)
issue_stats_parser.add_argument(
    "--filter",
    type=str.lower,
    choices=["all", "human", "bot"],
    default="all",
    help="Filter issues by category (default: all)"
)
issue_stats_parser.add_argument(
    "--details",
    action="store_true",
    default=False,
    help="Show individual issue details with links"
)
issue_stats_parser.add_argument(
    "--project-dir",
    metavar="PATH",
    help="Project directory path (default: current directory)"
)
issue_stats_parser.set_defaults(func=execute_coordinator_issue_stats)
```

### Import in `main.py`
```python
from .commands.coordinator.issue_stats import execute_coordinator_issue_stats
```

---

## ALGORITHM

### execute_coordinator_issue_stats
```
1. Resolve project_dir using resolve_project_dir()
2. Get repo_url from git remote
3. Load labels_config from get_labels_config_path()
4. Create IssueManager and fetch open issues
5. Filter ignored issues
6. Group issues by category
7. Display statistics with filter and details args
8. Return 0 (or 1 on exception)
```

---

## DATA

### Example CLI Usage
```bash
# All categories, summary only
mcp-coder coordinator issue-stats

# Human action issues only
mcp-coder coordinator issue-stats --filter human

# Bot issues with details
mcp-coder coordinator issue-stats --filter bot --details

# Specific project
mcp-coder coordinator issue-stats --project-dir /path/to/repo
```

### Example Output
```
=== Human Action Required ===
  status-01:created           5 issues
  status-04:plan-review       2 issues
  status-07:code-review       1 issue
  status-10:pr-created        0 issues

=== Bot Should Pickup ===
  status-02:awaiting-planning 3 issues
  status-05:plan-ready        1 issue
  status-08:ready-pr          0 issues

=== Bot Busy ===
  status-03:planning          0 issues
  status-06:implementing      1 issue
  status-09:pr-creating       0 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 16 open issues (13 valid, 3 errors)
```

---

## VERIFICATION

```bash
pytest tests/cli/commands/coordinator/test_issue_stats.py -v
pytest tests/cli/test_main.py -v -k "issue_stats"

# Integration test
mcp-coder coordinator issue-stats --help
mcp-coder coordinator issue-stats --filter human --project-dir .
```
