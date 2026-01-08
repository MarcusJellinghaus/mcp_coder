# Step 1: Implement `ignore_files` Parameter

## Reference
- **Summary**: `pr_info/steps/summary.md`
- **Decisions**: `pr_info/steps/Decisions.md`
- **Issue**: #254 - Ignore uv.lock in is_working_directory_clean() check

---

## LLM Prompt

```
Implement Step 1 from pr_info/steps/step_1.md for Issue #254.

1. Add constant `DEFAULT_IGNORED_BUILD_ARTIFACTS` to constants.py
2. Add 5 test scenarios for the new `ignore_files` parameter
3. Add `ignore_files` parameter to `is_working_directory_clean()` function
4. Update all 4 caller locations to use the constant
5. Remove `uv.lock` from `.gitignore`

Reference: pr_info/steps/summary.md for full context.
Reference: pr_info/steps/Decisions.md for design decisions.
```

---

## Part A: Add Constant

### WHERE
```
src/mcp_coder/constants.py
```

### WHAT: Add constant
```python
# Build artifacts to ignore in working directory clean checks
DEFAULT_IGNORED_BUILD_ARTIFACTS: list[str] = ["uv.lock"]
```

---

## Part B: Add Tests

### WHERE
```
tests/utils/git_operations/test_repository.py
```

### WHAT: Test Functions to Add

Add these 5 test methods inside the existing `TestRepositoryOperations` class:

```python
def test_is_working_directory_clean_ignore_files_none(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files=None preserves existing behavior."""

def test_is_working_directory_clean_ignore_files_empty_list(
    self, git_repo_with_commit: tuple[Repo, Path]
) -> None:
    """Test ignore_files=[] behaves same as None (backward compatibility)."""

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

### HOW: Integration Points
- Use existing `git_repo_with_commit` pytest fixture from `conftest.py`
- Add to existing `TestRepositoryOperations` class
- Mark with `@pytest.mark.git_integration`

### ALGORITHM: Test Logic

| Test | Setup | ignore_files | Expected Return |
|------|-------|--------------|-----------------|
| Test 1 | `new.txt` untracked | `None` | `False` |
| Test 2 | `new.txt` untracked | `[]` | `False` |
| Test 3 | `uv.lock` untracked | `["uv.lock"]` | `True` |
| Test 4 | `other.txt` untracked | `["uv.lock"]` | `False` |
| Test 5 | `uv.lock` + `real_change.txt` | `["uv.lock"]` | `False` |

---

## Part C: Implement Function Change

### WHERE
```
src/mcp_coder/utils/git_operations/repository.py
```

### WHAT: Updated Function Signature
```python
def is_working_directory_clean(
    project_dir: Path, 
    ignore_files: list[str] | None = None
) -> bool:
```

### ALGORITHM: Core Logic
```python
ignore_set = set(ignore_files) if ignore_files else set()
status = get_full_status(project_dir)
staged = [f for f in status["staged"] if f not in ignore_set]
modified = [f for f in status["modified"] if f not in ignore_set]
untracked = [f for f in status["untracked"] if f not in ignore_set]
return len(staged) + len(modified) + len(untracked) == 0
```

### DATA: Docstring Update
Update docstring to include `ignore_files` parameter:
```
Args:
    project_dir: Path to the project directory containing git repository
    ignore_files: Optional list of filenames to ignore (exact match only).
                  Useful for excluding build artifacts like 'uv.lock'.
```

---

## Part D: Update Caller Locations

### Caller 1: `create_plan.py`

**WHERE**: `src/mcp_coder/workflows/create_plan.py` (line ~71)

**WHAT**: Inside `check_prerequisites()` function

**HOW**: 
1. Add import: `from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS`
2. Change from:
```python
if not is_working_directory_clean(project_dir):
```
To:
```python
if not is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS):
```

---

### Caller 2: `prerequisites.py`

**WHERE**: `src/mcp_coder/workflows/implement/prerequisites.py` (line ~44)

**WHAT**: Inside `check_git_clean()` function

**HOW**:
1. Add import: `from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS`
2. Change from:
```python
is_clean = is_working_directory_clean(project_dir)
```
To:
```python
is_clean = is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS)
```

---

### Caller 3: `core.py` (first location)

**WHERE**: `src/mcp_coder/workflows/create_pr/core.py` (line ~247)

**WHAT**: Inside `check_prerequisites()` function

**HOW**:
1. Add import: `from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS`
2. Change from:
```python
if not is_working_directory_clean(project_dir):
```
To:
```python
if not is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS):
```

---

### Caller 4: `core.py` (second location)

**WHERE**: `src/mcp_coder/workflows/create_pr/core.py` (line ~592)

**WHAT**: Inside `run_create_pr_workflow()` function

**HOW**: Change from:
```python
if not is_working_directory_clean(project_dir):
```
To:
```python
if not is_working_directory_clean(project_dir, ignore_files=DEFAULT_IGNORED_BUILD_ARTIFACTS):
```

---

## Part E: Remove `.gitignore` Workaround

### WHERE
```
.gitignore
```

### WHAT: Remove these 2 lines at end of file
```
# UV lock file (generated by mcp-coder environment, not target projects)
uv.lock
```

---

## Verification Commands

```bash
# Run new tests
pytest tests/utils/git_operations/test_repository.py -v -k "ignore_files" -m git_integration

# Run all repository tests (backward compatibility)
pytest tests/utils/git_operations/test_repository.py -v -m git_integration

# Run full test suite (excluding slow integration tests)
pytest -m "not claude_cli_integration and not claude_api_integration and not github_integration"
```

---

## Checklist
- [ ] `DEFAULT_IGNORED_BUILD_ARTIFACTS` constant added to `constants.py`
- [ ] 5 test scenarios added to `test_repository.py`
- [ ] `is_working_directory_clean()` accepts `ignore_files` parameter
- [ ] Docstring updated with new parameter documentation
- [ ] `create_plan.py` updated with import and constant
- [ ] `implement/prerequisites.py` updated with import and constant
- [ ] `create_pr/core.py` updated (2 locations) with import and constant
- [ ] `uv.lock` removed from `.gitignore`
- [ ] All tests pass
