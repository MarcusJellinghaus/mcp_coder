# Step 3: Implement CLI Argument Parsing and Logging Setup

## Objective
Add command-line interface following existing workflow script patterns.

## Context
Reference `summary.md`. Follow patterns from `workflows/create_PR.py` for consistency.

## WHERE
- Modify: `workflows/define_labels.py`
- Modify: `tests/workflows/test_define_labels.py`

## WHAT

### In `workflows/define_labels.py`:
```python
def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    # Add --dry-run flag
    
def resolve_project_dir(project_dir_arg: Optional[str]) -> Path:
    """Convert and validate project directory path."""
```

### In `tests/workflows/test_define_labels.py`:
```python
def test_parse_arguments_defaults()
def test_parse_arguments_custom_values()
def test_resolve_project_dir_valid(tmp_path)
def test_resolve_project_dir_invalid()
```

## HOW
- Import: `import argparse`, `import sys`
- Import: `from mcp_coder.utils.log_utils import setup_logging`
- Copy `parse_arguments()` and `resolve_project_dir()` from `workflows/create_PR.py`
- Adapt to define_labels context (simpler, no llm-method arg)

## ALGORITHM
```
parse_arguments:
1. Create ArgumentParser with description
2. Add --project-dir argument (optional, default None)
3. Add --log-level argument (choices: DEBUG/INFO/WARNING/ERROR/CRITICAL)
4. Add --dry-run flag (action='store_true', default False)
5. Return parsed namespace

resolve_project_dir:
1. Use current dir if arg is None
2. Resolve to absolute path
3. Validate: exists, is_dir, readable, has .git/
4. Return validated Path or exit with error
```

## DATA
- **parse_arguments() returns**: `argparse.Namespace`
  - Fields: `project_dir: Optional[str]`, `log_level: str`, `dry_run: bool`
- **resolve_project_dir() input**: `project_dir_arg: Optional[str]`
- **resolve_project_dir() returns**: `Path` (validated)

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1.md, pr_info/steps/step_2.md, pr_info/steps/decisions.md

Implement Step 3: CLI argument parsing and validation.

Tasks:
1. Copy parse_arguments() from workflows/create_PR.py to workflows/define_labels.py
2. Remove --llm-method argument (not needed)
3. Keep --project-dir and --log-level arguments
4. Add --dry-run flag (action='store_true', default=False)
5. Copy resolve_project_dir() from workflows/create_PR.py
6. Add 4 tests in tests/workflows/test_define_labels.py for argument parsing and validation
7. Run pytest to verify

Follow exact patterns from workflows/create_PR.py for consistency.
```
