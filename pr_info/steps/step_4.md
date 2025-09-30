# Step 4: Implement main() Function and Script Entry Point

## Objective
Create the main orchestration function and script entry point.

## Context
Reference `summary.md`. Complete the script by adding main() following workflow script patterns.

## WHERE
- Modify: `workflows/define_labels.py`
- Modify: `tests/workflows/test_define_labels.py`

## WHAT

### In `workflows/define_labels.py`:
```python
def main() -> None:
    """Main entry point for label definition workflow."""
    
if __name__ == "__main__":
    main()
```

### In `tests/workflows/test_define_labels.py`:
```python
def test_main_success_flow(mock_labels_manager, tmp_path, monkeypatch)
def test_main_handles_errors(tmp_path, monkeypatch)
```

## HOW
- Add shebang: `#!/usr/bin/env python3`
- Add module docstring
- Import logger: `logger = logging.getLogger(__name__)`
- Call `setup_logging()`, `parse_arguments()`, `resolve_project_dir()`, `apply_labels()`
- Log summary of results

## ALGORITHM
```
main:
1. Parse command-line arguments (including dry_run flag)
2. Resolve and validate project_dir
3. Setup logging with specified level
4. Log: project directory, repository name, dry-run mode status
5. Call apply_labels(project_dir, dry_run=args.dry_run)
6. Exit 0 on success, 1 on failure (fail fast on any error)
```

## DATA
- **main() returns**: `None`
- **Exit codes**: 0 (success), 1 (failure)
- **Logs at start**: Project directory, repository name, dry-run mode status
- **Logs at end**: Summary statistics from apply_labels() results

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1-3.md, pr_info/steps/decisions.md

Implement Step 4: main() function and entry point.

Tasks:
1. Add shebang and module docstring to workflows/define_labels.py
2. Implement main() function following workflows/create_PR.py pattern
3. Call parse_arguments(), resolve_project_dir(), setup_logging(), apply_labels()
4. Pass dry_run flag to apply_labels(): apply_labels(project_dir, dry_run=args.dry_run)
5. At start, log: project directory, repository name, dry-run mode status
6. Add if __name__ == "__main__": main()
7. Add 2 tests for main() covering success and error scenarios
8. Run pytest to verify

Fail fast on any error - exit(1) immediately.
```
