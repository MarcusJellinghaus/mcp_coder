# Step 7: CLI Integration

## LLM Prompt

```
Implement Step 7 of the coordinator vscodeclaude feature.
Reference: pr_info/steps/summary.md for overall architecture.
This step: Add CLI parsers, command handlers, and module exports.
```

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/main.py` | Add vscodeclaude parser and routing |
| `src/mcp_coder/cli/commands/coordinator/commands.py` | Add command handlers |
| `src/mcp_coder/cli/commands/coordinator/__init__.py` | Export new functions |
| `tests/cli/commands/coordinator/test_vscodeclaude.py` | Add CLI tests |

## WHAT

### main.py - Parser Addition

Add after `run_parser` definition (around line 270):

```python
# coordinator vscodeclaude command
vscodeclaude_parser = coordinator_subparsers.add_parser(
    "vscodeclaude",
    help="Manage VSCode/Claude sessions for interactive workflow stages",
)
vscodeclaude_subparsers = vscodeclaude_parser.add_subparsers(
    dest="vscodeclaude_subcommand",
    help="VSCodeClaude commands",
    metavar="SUBCOMMAND",
)

# Default (no subcommand) - main vscodeclaude behavior
vscodeclaude_parser.add_argument(
    "--repo",
    type=str,
    metavar="NAME",
    help="Filter to specific repository only",
)
vscodeclaude_parser.add_argument(
    "--max-sessions",
    type=int,
    metavar="N",
    help="Override max concurrent sessions (default: from config or 3)",
)
vscodeclaude_parser.add_argument(
    "--cleanup",
    action="store_true",
    help="Delete stale clean folders (without this flag, only lists them)",
)
vscodeclaude_parser.add_argument(
    "--intervene",
    action="store_true",
    help="Force open a bot_busy issue for debugging",
)
vscodeclaude_parser.add_argument(
    "--issue",
    type=int,
    metavar="NUMBER",
    help="Issue number for intervention mode (requires --intervene)",
)

# vscodeclaude status subcommand
status_parser = vscodeclaude_subparsers.add_parser(
    "status",
    help="Show current VSCodeClaude sessions",
)
status_parser.add_argument(
    "--repo",
    type=str,
    metavar="NAME",
    help="Filter to specific repository only",
)
```

### main.py - Routing Addition

Add in the `coordinator` command routing section:

```python
elif args.coordinator_subcommand == "vscodeclaude":
    # Check for status subcommand first
    if hasattr(args, "vscodeclaude_subcommand") and args.vscodeclaude_subcommand == "status":
        return execute_coordinator_vscodeclaude_status(args)
    else:
        return execute_coordinator_vscodeclaude(args)
```

### commands.py - Handler Functions

```python
from .vscodeclaude import (
    load_vscodeclaude_config,
    load_repo_vscodeclaude_config,
    get_github_username,
    get_eligible_vscodeclaude_issues,
    get_linked_branch_for_issue,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
    get_active_session_count,
    load_sessions,
    check_vscode_running,
    display_status_table,
    cleanup_stale_sessions,
    DEFAULT_MAX_SESSIONS,
)


def execute_coordinator_vscodeclaude(args: argparse.Namespace) -> int:
    """Execute coordinator vscodeclaude command.
    
    Args:
        args: Parsed arguments with:
            - repo: Optional repository filter
            - max_sessions: Optional max sessions override
            - cleanup: Whether to delete stale folders
            - intervene: Intervention mode flag
            - issue: Issue number for intervention
            
    Returns:
        Exit code (0 success, 1 error)
    """

def execute_coordinator_vscodeclaude_status(args: argparse.Namespace) -> int:
    """Execute coordinator vscodeclaude status command.
    
    Args:
        args: Parsed arguments with:
            - repo: Optional repository filter
            
    Returns:
        Exit code (0 success)
    """
```

### __init__.py - Exports

Add to imports and `__all__`:

```python
from .vscodeclaude import (
    # Types
    VSCodeClaudeSession,
    VSCodeClaudeSessionStore,
    VSCodeClaudeConfig,
    # Constants
    VSCODECLAUDE_PRIORITY,
    HUMAN_ACTION_COMMANDS,
    DEFAULT_MAX_SESSIONS,
    # Session management
    load_sessions,
    save_sessions,
    add_session,
    remove_session,
    get_session_for_issue,
    check_vscode_running,
    get_active_session_count,
    # Configuration
    load_vscodeclaude_config,
    load_repo_vscodeclaude_config,
    get_github_username,
    sanitize_folder_name,
    # Issue selection
    get_human_action_labels,
    get_eligible_vscodeclaude_issues,
    get_linked_branch_for_issue,
    # Workspace setup
    get_working_folder_path,
    create_working_folder,
    setup_git_repo,
    validate_mcp_json,
    run_setup_commands,
    # Launch
    launch_vscode,
    prepare_and_launch_session,
    process_eligible_issues,
    restart_closed_sessions,
)

from .commands import (
    execute_coordinator_vscodeclaude,
    execute_coordinator_vscodeclaude_status,
)

__all__ = [
    # ... existing exports ...
    # VSCodeClaude
    "execute_coordinator_vscodeclaude",
    "execute_coordinator_vscodeclaude_status",
    "VSCodeClaudeSession",
    "VSCodeClaudeSessionStore",
    "VSCodeClaudeConfig",
    "VSCODECLAUDE_PRIORITY",
    "HUMAN_ACTION_COMMANDS",
    "DEFAULT_MAX_SESSIONS",
    # ... add other public functions as needed
]
```

## HOW

### Command Handler Pattern

Follow existing `execute_coordinator_test` and `execute_coordinator_run` patterns:

```python
def execute_coordinator_vscodeclaude(args: argparse.Namespace) -> int:
    try:
        coordinator = _get_coordinator()
        
        # Auto-create config if needed
        created = coordinator.create_default_config()
        if created:
            config_path = get_config_file_path()
            print(f"Created default config at {config_path}")
            print("Please configure [coordinator.vscodeclaude] section.")
            return 1
        
        # Load vscodeclaude config
        vscodeclaude_config = load_vscodeclaude_config()
        
        # Handle intervention mode
        if args.intervene:
            if not args.issue:
                print("Error: --intervene requires --issue NUMBER", file=sys.stderr)
                return 1
            return handle_intervention_mode(args, vscodeclaude_config)
        
        # Determine max sessions
        max_sessions = args.max_sessions or vscodeclaude_config["max_sessions"]
        
        # Step 1: Restart closed sessions
        restarted = restart_closed_sessions()
        for session in restarted:
            print(f"Restarted: #{session['issue_number']} ({session['status']})")
        
        # Step 2: Handle cleanup if requested
        if args.cleanup:
            cleanup_stale_sessions(dry_run=False)
        
        # Step 3: Start new sessions if under limit
        # ... process repositories based on --repo filter or all
        
        return 0
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

## ALGORITHM

### execute_coordinator_vscodeclaude()
```
1. Create default config if needed
2. Load vscodeclaude config (may raise ValueError)
3. If --intervene: validate --issue, call handle_intervention_mode()
4. Determine max_sessions (args override or config)
5. Call restart_closed_sessions(), print restarted
6. If --cleanup: call cleanup_stale_sessions()
7. Get repo list (from --repo filter or all from config)
8. For each repo: process_eligible_issues()
9. Print summary of started sessions
10. Return 0
```

### execute_coordinator_vscodeclaude_status()
```
1. Load sessions
2. Get eligible issues for all repos
3. Build combined table data
4. Apply --repo filter if specified
5. Print formatted table
6. Return 0
```

### handle_intervention_mode()
```
1. Validate issue exists via IssueManager
2. Get linked branch (or use main)
3. Build intervention session with is_intervention=True
4. Print warning about automation
5. prepare_and_launch_session(is_intervention=True)
6. Return 0
```

## DATA

### CLI Arguments

| Argument | Type | Description |
|----------|------|-------------|
| `--repo` | str | Single repo filter |
| `--max-sessions` | int | Override max concurrent |
| `--cleanup` | flag | Delete stale clean folders |
| `--intervene` | flag | Force open bot_busy issue |
| `--issue` | int | Issue number for intervention |

### Test Coverage

```python
# test_vscodeclaude.py

class TestCLI:
    """Test CLI argument parsing and routing."""
    
    def test_vscodeclaude_parser_exists(self):
        """vscodeclaude subcommand is registered."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        # Parse valid command
        args = parser.parse_args(["coordinator", "vscodeclaude"])
        assert args.coordinator_subcommand == "vscodeclaude"
    
    def test_vscodeclaude_repo_argument(self):
        """--repo argument is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args(["coordinator", "vscodeclaude", "--repo", "test"])
        assert args.repo == "test"
    
    def test_vscodeclaude_max_sessions_argument(self):
        """--max-sessions argument is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args(["coordinator", "vscodeclaude", "--max-sessions", "5"])
        assert args.max_sessions == 5
    
    def test_vscodeclaude_cleanup_flag(self):
        """--cleanup flag is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args(["coordinator", "vscodeclaude", "--cleanup"])
        assert args.cleanup is True
    
    def test_vscodeclaude_intervene_with_issue(self):
        """--intervene with --issue is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args([
            "coordinator", "vscodeclaude", 
            "--intervene", "--issue", "123"
        ])
        assert args.intervene is True
        assert args.issue == 123
    
    def test_vscodeclaude_status_subcommand(self):
        """status subcommand is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args(["coordinator", "vscodeclaude", "status"])
        assert args.vscodeclaude_subcommand == "status"
    
    def test_vscodeclaude_status_with_repo(self):
        """status --repo argument is parsed."""
        from mcp_coder.cli.main import create_parser
        parser = create_parser()
        
        args = parser.parse_args([
            "coordinator", "vscodeclaude", "status", "--repo", "myrepo"
        ])
        assert args.vscodeclaude_subcommand == "status"
        assert args.repo == "myrepo"


class TestCommandHandlers:
    """Test command handler functions."""
    
    def test_execute_vscodeclaude_creates_config(self, monkeypatch, capsys):
        """Creates config file on first run."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._get_coordinator",
            lambda: type("M", (), {"create_default_config": lambda: True})()
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands.get_config_file_path",
            lambda: Path("/fake/config.toml")
        )
        
        args = argparse.Namespace(
            repo=None, max_sessions=None, cleanup=False, 
            intervene=False, issue=None
        )
        
        result = execute_coordinator_vscodeclaude(args)
        
        assert result == 1  # Exit to let user configure
        captured = capsys.readouterr()
        assert "config" in captured.out.lower()
    
    def test_execute_vscodeclaude_intervene_requires_issue(self, monkeypatch, capsys):
        """Intervention mode requires --issue."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.commands._get_coordinator",
            lambda: type("M", (), {"create_default_config": lambda: False})()
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.load_vscodeclaude_config",
            lambda: {"workspace_base": "/tmp", "max_sessions": 3}
        )
        
        args = argparse.Namespace(
            repo=None, max_sessions=None, cleanup=False,
            intervene=True, issue=None  # Missing issue
        )
        
        result = execute_coordinator_vscodeclaude(args)
        
        assert result == 1
        captured = capsys.readouterr()
        assert "--issue" in captured.err
    
    def test_execute_vscodeclaude_status_success(self, monkeypatch, capsys):
        """Status command prints table."""
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.load_sessions",
            lambda: {"sessions": [], "last_updated": "2024-01-01T00:00:00Z"}
        )
        monkeypatch.setattr(
            "mcp_coder.cli.commands.coordinator.vscodeclaude.display_status_table",
            lambda sessions, eligible, repo_filter: print("Table displayed")
        )
        
        args = argparse.Namespace(repo=None)
        
        result = execute_coordinator_vscodeclaude_status(args)
        
        assert result == 0
```

## Verification

```bash
# Test CLI parsing
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestCLI -v

# Test command handlers
pytest tests/cli/commands/coordinator/test_vscodeclaude.py::TestCommandHandlers -v

# Test full CLI integration
python -m mcp_coder.cli.main coordinator vscodeclaude --help
python -m mcp_coder.cli.main coordinator vscodeclaude status --help

# Type check all modified files
mypy src/mcp_coder/cli/main.py
mypy src/mcp_coder/cli/commands/coordinator/commands.py
mypy src/mcp_coder/cli/commands/coordinator/__init__.py
```
