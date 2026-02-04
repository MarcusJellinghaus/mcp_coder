# Step 3: Update Tests

## LLM Prompt

```
Implement Step 3 of Issue #399 (see pr_info/steps/summary.md for context).

Update the test file for the new .txt format:
1. Update test_update_gitignore_* tests to check for .txt
2. Update test_create_status_file* tests for new filename and format
3. Update test_create_vscode_task to verify two tasks exist

Run tests to verify all changes work correctly.
```

## WHERE

**File:** `tests/workflows/vscodeclaude/test_workspace.py`

**Tests to modify:**
- `test_update_gitignore_adds_entry` (line ~169)
- `test_update_gitignore_creates_file` (line ~178)
- `test_update_gitignore_idempotent` (line ~185)
- `test_create_status_file` (line ~257)
- `test_create_status_file_intervention` (line ~277)
- `test_create_vscode_task` (line ~248)

## WHAT

### 1. test_update_gitignore_* tests

**Change:** Assert `.vscodeclaude_status.txt` instead of `.vscodeclaude_status.md`

### 2. test_create_status_file

**Changes:**
- Check for `.vscodeclaude_status.txt` file instead of `.md`
- Update content assertions for plain text format

### 3. test_create_status_file_intervention

**Changes:**
- Check for `.vscodeclaude_status.txt` file
- Assert "INTERVENTION" still appears in content

### 4. test_create_vscode_task

**Changes:**
- Verify tasks.json contains 2 tasks
- Verify second task has label "Open Status File"

## HOW

Direct assertion changes in test methods. No new imports needed.

## ALGORITHM

```python
# test_update_gitignore_adds_entry
def test_update_gitignore_adds_entry(self, tmp_path):
    # ... setup ...
    update_gitignore(tmp_path)
    content = gitignore.read_text()
    assert ".vscodeclaude_status.txt" in content  # Changed from .md

# test_create_status_file  
def test_create_status_file(self, tmp_path, mock_vscodeclaude_config):
    create_status_file(...)
    status_file = tmp_path / ".vscodeclaude_status.txt"  # Changed from .md
    assert status_file.exists()
    content = status_file.read_text()
    assert "#123" in content
    assert "Add feature" in content
    assert "Branch:" in content  # New field
    assert "Started:" in content  # New field

# test_create_vscode_task
def test_create_vscode_task(self, tmp_path):
    # ... setup ...
    create_vscode_task(tmp_path, script_path)
    content = json.loads(tasks_file.read_text())
    assert len(content["tasks"]) == 2  # Now 2 tasks
    assert content["tasks"][0]["runOptions"]["runOn"] == "folderOpen"
    assert content["tasks"][1]["label"] == "Open Status File"
```

## DATA

### Test assertions (updated)

| Test | Old Assertion | New Assertion |
|------|---------------|---------------|
| `test_update_gitignore_adds_entry` | `.vscodeclaude_status.md` in content | `.vscodeclaude_status.txt` in content |
| `test_update_gitignore_creates_file` | `.vscodeclaude_status.md` in content | `.vscodeclaude_status.txt` in content |
| `test_update_gitignore_idempotent` | count `.vscodeclaude_status.md` == 1 | count `.vscodeclaude_status.txt` == 1 |
| `test_create_status_file` | file is `.vscodeclaude_status.md` | file is `.vscodeclaude_status.txt`, contains Branch and Started |
| `test_create_status_file_intervention` | file is `.vscodeclaude_status.md` | file is `.vscodeclaude_status.txt`, contains INTERVENTION |
| `test_create_vscode_task` | 1 task | 2 tasks, second has label "Open Status File" |

## VERIFICATION

Run the full test suite for this module:
```bash
pytest tests/workflows/vscodeclaude/test_workspace.py -v
```

Expected: All tests pass with the updated assertions.
