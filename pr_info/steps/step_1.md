# Step 1: Rename 5 orchestrator test files

## References
- [Summary](./summary.md)
- Issue #463

## Goal
Rename 5 test files that map 1:1 to the new source structure. No content changes needed — imports already point to `session_launch`/`session_restart`/`issues` from #458.

## WHERE — File operations

All in `tests/workflows/vscodeclaude/`:

| From | To |
|---|---|
| `test_orchestrator_launch.py` | `test_session_launch.py` |
| `test_orchestrator_regenerate.py` | `test_session_launch_regenerate.py` |
| `test_orchestrator_launch_process_issues.py` | `test_session_launch_process_issues.py` |
| `test_orchestrator_cache.py` | `test_session_restart_cache.py` |
| `test_orchestrator_documentation.py` | `test_issues_branch_requirements.py` |

## WHAT — Operations
- `move_file` for each of the 5 files
- No content changes

## HOW — Verification
- Run all code quality checks per CLAUDE.md (pytest, pylint, mypy, lint_imports, vulture, ruff, format_code)
- All checks must pass with zero failures

## ALGORITHM
```
for each (old_name, new_name) in rename_table:
    move_file(old_name, new_name)
run_checks()  # all code quality checks per CLAUDE.md
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md for context.

Rename 5 test files in tests/workflows/vscodeclaude/:
- test_orchestrator_launch.py → test_session_launch.py
- test_orchestrator_regenerate.py → test_session_launch_regenerate.py
- test_orchestrator_launch_process_issues.py → test_session_launch_process_issues.py
- test_orchestrator_cache.py → test_session_restart_cache.py
- test_orchestrator_documentation.py → test_issues_branch_requirements.py

No content changes. Run format_code before committing. Run all code quality checks per CLAUDE.md (pytest, pylint, mypy, lint_imports, vulture, ruff, format_code). All checks must pass.
```
