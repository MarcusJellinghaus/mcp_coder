# Step 5: Gate operations in `define_labels.py` + updated summary

## LLM Prompt

> Read `pr_info/steps/summary.md` for full context. Implement Step 5: Modify `execute_define_labels()` to gate init/validate behind flags, expand `--all`, use `default: true` label, pass `--config` to discovery, call `validate_labels_config()`, and update summary output to show "skipped". Write tests first (TDD), then implement. Run all code quality checks after changes.

## WHERE

- `src/mcp_coder/cli/commands/define_labels.py` — modify `execute_define_labels()` and `format_validation_summary()`
- `tests/cli/commands/test_define_labels.py` — add/update tests
- `tests/cli/commands/test_define_labels_format.py` — update summary format tests

## WHAT

### Modified: `execute_define_labels(args)`

Changes to the function body:

1. **`--all` expansion** — at the top: if `args.all`, set `init=True`, `validate=True`, `generate_github_actions=True`
2. **`--config` support** — pass `config_override=Path(args.config) if args.config else None` to `get_labels_config_path()`
3. **Config validation** — call `validate_labels_config(labels_config)` after loading (always runs)
4. **Gate `IssueManager`** — only create `IssueManager` and call `list_issues()` when `init or validate`
5. **Gate `initialize_issues`** — only call when `init` is set
6. **Gate `validate_issues`** — only call when `validate` is set
7. **Use `default: true` label** — find default label from config instead of hardcoded `"status-01:created"` fallback

### Modified: `format_validation_summary(label_changes, validation_results, repo_url, *, init_requested, validate_requested)`

Add keyword arguments `init_requested: bool` and `validate_requested: bool`. When an operation was not requested, show "skipped" instead of count.

### New import in `define_labels.py`

```python
from ...utils.github_operations.label_config import (
    build_label_lookups,
    get_labels_config_path,
    load_labels_config,
    validate_labels_config,  # NEW
)
```

## HOW

- `execute_define_labels` reads `args.init`, `args.validate`, `args.all`, `args.config`, `args.generate_github_actions`
- Uses `getattr()` with defaults for backward safety
- `generate_github_actions` is not implemented yet (Step 6) — just read the flag, skip if false

## ALGORITHM

```python
# --all expansion
init = getattr(args, "init", False) or getattr(args, "all", False)
validate = getattr(args, "validate", False) or getattr(args, "all", False)
gen_actions = getattr(args, "generate_github_actions", False) or getattr(args, "all", False)

# Config loading with --config support
config_override = Path(args.config) if getattr(args, "config", None) else None
config_path = get_labels_config_path(project_dir, config_override=config_override)
labels_config = load_labels_config(config_path)
validate_labels_config(labels_config)  # always runs, raises ValueError on error

# Find default label from config
default_label = next(l for l in labels_config["workflow_labels"] if l.get("default"))
created_label_name = default_label["name"]

# Gate IssueManager
if init or validate:
    issue_manager = IssueManager(project_dir)
    issues = issue_manager.list_issues(state="open", include_pull_requests=False)
    if init:
        initialized = initialize_issues(...)
    if validate:
        validation = validate_issues(...)
```

### Summary format change

```python
# Instead of always showing count:
if init_requested:
    lines.append(f"  Issues initialized: {initialized_count}")
else:
    lines.append("  Issues initialized: skipped")
```

## DATA

- `format_validation_summary` signature gains `init_requested: bool` and `validate_requested: bool` keyword args
- When operation is skipped, `validation_results` may have empty lists for those sections

## Tests (TDD — write first)

```python
class TestFlagGating:
    def test_no_flags_skips_issue_manager(self):
        """Without --init or --validate, IssueManager is never created."""
        
    def test_init_flag_creates_issue_manager(self):
        """With --init, IssueManager is created and initialize_issues called."""
        
    def test_validate_flag_creates_issue_manager(self):
        """With --validate, IssueManager is created and validate_issues called."""
        
    def test_all_flag_expands(self):
        """--all enables init, validate, and generate_github_actions."""
        
    def test_config_flag_passed_to_discovery(self):
        """--config path is passed as config_override to get_labels_config_path."""
        
    def test_config_validation_always_runs(self):
        """validate_labels_config is called even without --init or --validate."""

class TestSummarySkipped:
    def test_init_skipped_shows_skipped(self):
        """When init_requested=False, summary shows 'skipped' for initialized."""
        
    def test_validate_skipped_shows_skipped(self):
        """When validate_requested=False, summary shows 'skipped' for errors/warnings."""
        
    def test_both_requested_shows_counts(self):
        """When both requested, summary shows actual counts."""
```

## Verification

- All new and existing tests pass
- Pylint, mypy, pytest all green
