# Step 2: Update Test Files

## LLM Prompt

```
Reference: pr_info/steps/summary.md and this step file.

Update test files to use `.vscodeclaude_status.txt` instead of `.vscodeclaude_status.md`
to match the source file changes from Step 1.
```

## WHERE: Files to Modify

1. `tests/workflows/vscodeclaude/test_workspace.py`
2. `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py`
3. `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`

## WHAT: Changes Required

### test_workspace.py

| Test Method | Change |
|-------------|--------|
| `test_update_gitignore_adds_entry` | Assertion string |
| `test_update_gitignore_creates_file` | Assertion string |
| `test_update_gitignore_idempotent` | Assertion string |
| `test_create_status_file` | Status file path |
| `test_create_status_file_intervention` | Status file path |

### test_orchestrator_regenerate.py

| Test Method | Change |
|-------------|--------|
| `test_regenerate_creates_status_file` | Status file path |
| `test_regenerate_creates_all_files` | Required files list |

### test_vscodeclaude_cli.py

| Test Method | Change |
|-------------|--------|
| `test_gitignore_entry_has_session_files` | Assertion string |

## HOW: Integration Points

No integration changes. These are string literal replacements in test assertions only.

## ALGORITHM

```
1. Open each test file
2. Replace ".vscodeclaude_status.md" with ".vscodeclaude_status.txt"
3. Save file
4. Run tests to verify
```

## DATA: Expected State After

All tests should pass with the updated `.txt` extension.

## Verification

Run the affected tests:
```bash
pytest tests/workflows/vscodeclaude/test_workspace.py tests/workflows/vscodeclaude/test_orchestrator_regenerate.py tests/cli/commands/coordinator/test_vscodeclaude_cli.py -v
```

All tests should pass. If any fail, investigate whether additional occurrences were missed.
