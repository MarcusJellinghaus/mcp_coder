# Step 3: CLI command — `git_tool.py` + parser + `main.py` wiring + tests

## Goal

Expose `get_compact_diff()` as `mcp-coder git-tool compact-diff`, following the
exact same pattern as the existing `gh-tool` / `get-base-branch` command.

---

## WHERE

**Create:** `src/mcp_coder/cli/commands/git_tool.py`

**Create:** `tests/cli/commands/test_git_tool.py`

**Modify:** `src/mcp_coder/cli/parsers.py`  
**Modify:** `src/mcp_coder/cli/main.py`

---

## WHAT

### `git_tool.py`

```python
def execute_compact_diff(args: argparse.Namespace) -> int:
    """Execute git-tool compact-diff command.

    Returns:
        0  Success — compact diff printed to stdout
        1  Could not detect base branch
        2  Error (invalid repo, unexpected exception)
    """
```

Logic:
1. `project_dir = resolve_project_dir(args.project_dir)`
2. `base_branch = detect_base_branch(project_dir)` — from `workflow_utils.base_branch`
3. If `base_branch` is `None`: print error to stderr, return 1
4. `result = get_compact_diff(project_dir, base_branch, args.exclude or [])`
5. `print(result)` ; return 0

Imports mirror `gh_tool.py`:
```python
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir
from ...utils.git_operations.compact_diffs import get_compact_diff
```

---

### `parsers.py` — new function

```python
def add_git_tool_parsers(subparsers: Any) -> None:
    """Add git-tool command parsers."""
```

Parser structure:
```
git-tool
└── compact-diff
    ├── --base-branch BRANCH   (optional; auto-detected if omitted)
    ├── --project-dir PATH     (standard; default: cwd)
    └── --exclude PATTERN      (repeatable via action="append")
```

Note: `--base-branch` is **parsed** but if provided it overrides
`detect_base_branch()`. Pass it through `args.base_branch`.

---

### `main.py` additions

```python
# New import (alongside existing add_gh_tool_parsers import):
from .parsers import add_git_tool_parsers

# New import (alongside existing execute_get_base_branch import):
from .commands.git_tool import execute_compact_diff

# In create_parser(): add after add_gh_tool_parsers():
add_git_tool_parsers(subparsers)

# New handler function:
def _handle_git_tool_command(args: argparse.Namespace) -> int:
    if args.git_tool_subcommand == "compact-diff":
        return execute_compact_diff(args)
    ...

# In main(): add elif after "gh-tool" branch:
elif args.command == "git-tool":
    return _handle_git_tool_command(args)
```

`dest` for the git-tool subparser must be `"git_tool_subcommand"` (matching the
handler attribute lookup above).

---

## HOW

- `--base-branch`: when provided by user, pass it directly to `get_compact_diff()`
  instead of calling `detect_base_branch()`. Update `execute_compact_diff()` to
  check `args.base_branch` first.
- `--exclude` with `action="append"` produces a list or `None`; normalise with
  `args.exclude or []`.
- Output goes to stdout only (compact diff text). All errors go to stderr.

---

## ALGORITHM (`execute_compact_diff`)

```
project_dir = resolve_project_dir(args.project_dir)
base_branch = args.base_branch if args.base_branch else detect_base_branch(project_dir)
if base_branch is None: print error to stderr; return 1
result = get_compact_diff(project_dir, base_branch, args.exclude or [])
print(result)
return 0
```

---

## DATA

Exit codes:
- `0` — success, compact diff written to stdout
- `1` — base branch could not be detected
- `2` — error (ValueError from resolve_project_dir, unexpected exception)

---

## TESTS (`test_git_tool.py`)

Follow `test_gh_tool.py` structure exactly. All tests use `unittest.mock`.

```python
# Fixtures (module-level)
@pytest.fixture
def mock_get_compact_diff() -> Generator[MagicMock, None, None]:
    with patch("mcp_coder.cli.commands.git_tool.get_compact_diff") as mock:
        yield mock

@pytest.fixture
def mock_detect_base_branch() -> Generator[MagicMock, None, None]:
    with patch("mcp_coder.cli.commands.git_tool.detect_base_branch") as mock:
        yield mock

@pytest.fixture
def mock_resolve_project_dir() -> Generator[MagicMock, None, None]:
    with patch("mcp_coder.cli.commands.git_tool.resolve_project_dir") as mock:
        yield mock

# Test classes
class TestCompactDiffExitCodes:
    """Test exit codes 0, 1, 2."""
    # test_exit_code_success              → returns 0, output on stdout
    # test_exit_code_no_base_branch       → detect returns None → returns 1
    # test_exit_code_invalid_repo         → resolve raises ValueError → returns 2
    # test_exit_code_unexpected_exception → get_compact_diff raises → returns 2

class TestCompactDiffOutputFormat:
    """Test stdout/stderr separation."""
    # test_diff_printed_to_stdout         → captured.out contains diff text
    # test_no_extra_text_in_output        → stdout is exactly the diff string

class TestCompactDiffArguments:
    """Test argument handling."""
    # test_exclude_passed_to_get_compact_diff   → args.exclude forwarded
    # test_base_branch_override                 → args.base_branch skips detect
    # test_exclude_none_defaults_to_empty_list  → None → []

class TestGitToolCommandIntegration:
    """Test CLI registration (no mocks — inspect parser)."""
    # test_git_tool_command_registered_in_cli
    # test_compact_diff_subcommand_registered
    # test_exclude_flag_is_repeatable
```

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement Step 3 exactly as specified.

Files to create:
  src/mcp_coder/cli/commands/git_tool.py
  tests/cli/commands/test_git_tool.py

Files to modify:
  src/mcp_coder/cli/parsers.py      (add add_git_tool_parsers function)
  src/mcp_coder/cli/main.py         (import, wire _handle_git_tool_command, routing)

Implementation rules:
1. git_tool.py must mirror gh_tool.py in structure (same error handling pattern,
   same stderr/stdout separation, same exit code conventions).
2. In parsers.py, add add_git_tool_parsers() after add_gh_tool_parsers().
   --exclude must use action="append" so it is repeatable.
   --base-branch is optional (auto-detected if absent).
   The subparser dest must be "git_tool_subcommand".
3. In main.py, add _handle_git_tool_command() following _handle_gh_tool_command()
   as the pattern. Wire it after the "gh-tool" elif branch.

Test rules:
1. Follow test_gh_tool.py structure exactly (same fixture/class layout).
2. All tests use unittest.mock — no real git repos.
3. Include the TestGitToolCommandIntegration class that inspects the live parser
   (no mocks needed there).

Run all tests after implementing to verify they pass.
```
