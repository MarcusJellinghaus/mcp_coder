# Step 2: CLI parser for init command

**Summary reference:** See `pr_info/steps/summary.md` for overall architecture.

## Goal

Add `--just-skills` and `--project-dir` flags to `mcp-coder init` by creating a dedicated parser function, replacing the bare `add_parser("init")` line.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement step 2: add `add_init_parser()` in `parsers.py` with `--just-skills` and `--project-dir` flags, wire it into `main.py`, and update `execute_init()` signature to accept the new args (no deploy logic yet — just accept and ignore). Write tests first (TDD), then implement, then run all three code quality checks.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/parsers.py` | **Edit** — add `add_init_parser()` |
| `src/mcp_coder/cli/main.py` | **Edit** — replace bare `add_parser("init")` with `add_init_parser()` call + import |
| `src/mcp_coder/cli/commands/init.py` | **Edit** — update `execute_init()` to accept new args (rename `_args` → `args`) |
| `tests/cli/commands/test_init.py` | **Edit** — add parser tests, update existing test Namespace objects |

## WHAT

### `parsers.py` — `add_init_parser()`

```python
def add_init_parser(subparsers: Any) -> None:
    """Add the init command parser."""
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize project: create config and deploy Claude skills",
        formatter_class=WideHelpFormatter,
    )
    init_parser.add_argument(
        "--just-skills",
        action="store_true",
        help="Deploy skills only, skip config creation",
    )
    init_parser.add_argument(
        "--project-dir",
        type=str,
        default=None,
        help="Target project directory (default: current directory)",
    )
```

### `main.py` changes

```python
# Import (add to existing import block):
from .parsers import add_init_parser  # add to existing import list

# In create_parser(), replace:
#     subparsers.add_parser("init", help="Create default configuration file")
# With:
    add_init_parser(subparsers)
```

### `init.py` — Updated signature

```python
def execute_init(args: argparse.Namespace) -> int:
    # args.just_skills: bool
    # args.project_dir: str | None
```

The function body stays the same for now — `just_skills` and `project_dir` are accepted but not yet used. Step 4 adds the deploy logic.

## HOW

- Follows the exact same pattern as `add_verify_parser()`, `add_implement_parser()`, etc.
- `--project-dir` uses `type=str, default=None` matching all other commands.
- `--just-skills` is `store_true`, matching `--dry-run` pattern elsewhere.

## DATA

- `args.just_skills: bool` — default `False`
- `args.project_dir: str | None` — default `None` (resolved to CWD at execution time)

## TESTS

```python
class TestInitParser:
    def test_init_default_args(self):
        """init with no flags sets just_skills=False, project_dir=None."""

    def test_init_just_skills_flag(self):
        """--just-skills sets just_skills=True."""

    def test_init_project_dir_flag(self):
        """--project-dir sets project_dir to given path."""

    def test_init_both_flags(self):
        """--just-skills --project-dir /tmp/foo sets both."""
```

Update existing tests to include `just_skills=False, project_dir=None` in their `argparse.Namespace` objects.
