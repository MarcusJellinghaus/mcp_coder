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
1. Parse command-line arguments
2. Resolve and validate project_dir
3. Setup logging with specified level
4. Log start message
5. Call apply_labels(project_dir)
6. Log summary: "Created: X, Updated: Y, Deleted: Z, Unchanged: W"
7. Exit 0 on success, 1 on failure
```

## DATA
- **Returns**: `None`
- **Exit codes**: 0 (success), 1 (failure)
- **Logs**: Summary statistics from apply_labels() results

## LLM Prompt
```
Reference: pr_info/steps/summary.md, pr_info/steps/step_1-3.md

Implement Step 4: main() function and entry point.

Tasks:
1. Add shebang and module docstring to workflows/define_labels.py
2. Implement main() function following workflows/create_PR.py pattern
3. Call parse_arguments(), resolve_project_dir(), setup_logging(), apply_labels()
4. Log summary: "Created: X, Updated: Y, Deleted: Z, Unchanged: W"
5. Add if __name__ == "__main__": main()
6. Add 2 tests for main() covering success and error scenarios
7. Run pytest to verify

Keep error handling simple - let exceptions propagate with proper logging.
```
