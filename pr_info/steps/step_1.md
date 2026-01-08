# Step 1: Add Tests for `ignore_files` Parameter

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #254 - Ignore uv.lock in is_working_directory_clean() check

---

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md for Issue #254.

Add 4 test scenarios to test the new `ignore_files` parameter for `is_working_directory_clean()`.
Follow TDD - write tests that will initially fail, to be made passing in Step 2.

Reference: pr_info/steps/summary.md for full context.
```

---

## WHERE: File Path
```
tests/utils/git_operations/test_repository.py
```

---

## WHAT: Test Functions to Add

Add these 4 test methods inside the existing `TestRepositoryOperations` class:

```python
def test_is_working_directory_clean_ignore_files_none(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files=None preserves existing behavior."""

def test_is_working_directory_clean_ignore_files_matches_untracked(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files filters matching untracked file."""

def test_is_working_directory_clean_ignore_files_other_untracked(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files does not filter non-matching files."""

def test_is_working_directory_clean_ignore_files_with_other_changes(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files with matching file AND other changes."""
```

---

## HOW: Integration Points
- Use existing `git_repo_with_commit` pytest fixture from `conftest.py`
- Add to existing `TestRepositoryOperations` class
- Mark with `@pytest.mark.git_integration`

---

## ALGORITHM: Test Logic Pseudocode

### Test 1: `ignore_files=None` (backward compatibility)
```
1. Create untracked file "new.txt"
2. Call is_working_directory_clean(project_dir, ignore_files=None)
3. Assert returns False (untracked file detected)
```

### Test 2: `ignore_files` matches untracked file
```
1. Create untracked file "uv.lock"
2. Call is_working_directory_clean(project_dir, ignore_files=["uv.lock"])
3. Assert returns True (uv.lock ignored, directory is clean)
```

### Test 3: `ignore_files` with non-matching file
```
1. Create untracked file "other.txt"
2. Call is_working_directory_clean(project_dir, ignore_files=["uv.lock"])
3. Assert returns False (other.txt not ignored)
```

### Test 4: `ignore_files` with matching file AND other changes
```
1. Create untracked file "uv.lock"
2. Create untracked file "real_change.txt"
3. Call is_working_directory_clean(project_dir, ignore_files=["uv.lock"])
4. Assert returns False (real_change.txt still detected)
```

---

## DATA: Expected Test Results

| Test | Setup | ignore_files | Expected Return |
|------|-------|--------------|-----------------|
| Test 1 | `new.txt` untracked | `None` | `False` |
| Test 2 | `uv.lock` untracked | `["uv.lock"]` | `True` |
| Test 3 | `other.txt` untracked | `["uv.lock"]` | `False` |
| Test 4 | `uv.lock` + `real_change.txt` | `["uv.lock"]` | `False` |

---

## Verification Command
```bash
pytest tests/utils/git_operations/test_repository.py -v -k "ignore_files" -m git_integration
```

Note: Tests will fail until Step 2 implements the `ignore_files` parameter.
