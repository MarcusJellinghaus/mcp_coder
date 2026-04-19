# Step 4: CLI flags in `gh_parsers.py`

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 4: Add `--init`, `--validate`, `--config`, `--generate-github-actions`, `--all` arguments and improved help text to the `define-labels` subparser. Write parser tests first (TDD), then implement. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/cli/gh_parsers.py` — modify `define_labels_parser`
- `tests/cli/test_parsers.py` — add parser tests (if define-labels parsing is tested there, otherwise `tests/cli/commands/test_define_labels.py`)

## WHAT

### New arguments on `define_labels_parser`

```python
define_labels_parser.add_argument(
    "--init", action="store_true",
    help="Assign the default label to open issues without a status label",
)
define_labels_parser.add_argument(
    "--validate", action="store_true",
    help="Check all open issues for errors and warnings",
)
define_labels_parser.add_argument(
    "--config", type=str, default=None, metavar="PATH",
    help="Path to labels config file (overrides pyproject.toml and bundled defaults)",
)
define_labels_parser.add_argument(
    "--generate-github-actions", action="store_true",
    help="Write label-new-issues.yml and approve-command.yml to .github/workflows/",
)
define_labels_parser.add_argument(
    "--all", action="store_true",
    help="Enable all optional operations (--init --validate --generate-github-actions)",
)
```

### Updated help text

Replace the `help=` on `define_labels_parser` (the `add_parser` call) with a multi-line description using `description=` and `epilog=`:

```python
define_labels_parser = gh_tool_subparsers.add_parser(
    "define-labels",
    help="Sync workflow label definitions to a GitHub repository",
    description="Sync workflow label definitions to a GitHub repository.",
    epilog="""Operations (always):
  - Validate labels config (default label, promotable targets)
  - Create, update, and delete status-* label definitions from config

With --init:
  - Assign the default label to open issues without a status label

With --validate:
  - Check all open issues for errors (multiple status labels)
    and warnings (stale bot processes)

With --generate-github-actions:
  - Write label-new-issues.yml and approve-command.yml
    to {project_dir}/.github/workflows/

With --all:
  - Run all optional operations (--init --validate --generate-github-actions)

Config resolution:
  1. --config PATH (explicit, highest priority)
  2. [tool.mcp-coder] labels-config in pyproject.toml
  3. Bundled package defaults""",
    formatter_class=WideHelpFormatter,
)
```

## HOW

- Edit `add_gh_tool_parsers()` in `gh_parsers.py`
- All new args use `store_true` or `type=str` — standard argparse patterns
- No new imports needed

## ALGORITHM

N/A — argument definitions only.

## DATA

The parsed `argparse.Namespace` will now include:
- `args.init: bool`
- `args.validate: bool`
- `args.config: Optional[str]`
- `args.generate_github_actions: bool`
- `args.all: bool`

(Plus existing `args.project_dir` and `args.dry_run`)

## Tests (TDD — write first)

```python
class TestDefineLabelsParser:
    def test_default_flags_are_false(self):
        """All optional flags default to False/None."""
        
    def test_init_flag(self):
        """--init sets args.init=True."""
        
    def test_validate_flag(self):
        """--validate sets args.validate=True."""
        
    def test_config_flag(self):
        """--config path/to/config.json sets args.config."""
        
    def test_generate_github_actions_flag(self):
        """--generate-github-actions sets args.generate_github_actions=True."""
        
    def test_all_flag(self):
        """--all sets args.all=True."""
        
    def test_combined_flags(self):
        """Multiple flags can be combined."""
```

Tests should parse args via the actual parser (import the main parser or `add_gh_tool_parsers` and parse `["gh-tool", "define-labels", "--init", "--validate"]`).

## Verification

- Parser tests pass
- Existing tests unaffected
- Pylint, mypy, pytest all green
