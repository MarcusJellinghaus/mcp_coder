# Step 2: Core File Size Checking Logic (TDD)

## LLM Prompt
```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.
Implement Step 2: Create the checks package with file_sizes.py core logic.
Follow TDD - write tests first in tests/checks/test_file_sizes.py, then implement in src/mcp_coder/checks/file_sizes.py.
```

## Objective
Implement core file size checking logic with full test coverage using TDD.

---

## Task 2.1: Create checks/__init__.py

### WHERE
`src/mcp_coder/checks/__init__.py`

### WHAT
Package init with public exports.

### IMPLEMENTATION
```python
"""Code quality checks package."""

from .file_sizes import (
    CheckResult,
    FileMetrics,
    check_file_sizes,
    count_lines,
    get_file_metrics,
    load_allowlist,
    render_allowlist,
    render_output,
)

__all__ = [
    "CheckResult",
    "FileMetrics",
    "check_file_sizes",
    "count_lines",
    "get_file_metrics",
    "load_allowlist",
    "render_allowlist",
    "render_output",
]
```

---

## Task 2.2: Create file_sizes.py with Data Structures

### WHERE
`src/mcp_coder/checks/file_sizes.py`

### WHAT - Data Structures
```python
@dataclass
class FileMetrics:
    path: Path
    line_count: int

@dataclass
class CheckResult:
    passed: bool
    violations: list[FileMetrics]
    total_files_checked: int
    allowlisted_count: int
    stale_entries: list[str]
```

---

## Task 2.3: Implement count_lines()

### WHAT
```python
def count_lines(file_path: Path) -> int
```

### ALGORITHM
```
1. Try to open file with UTF-8 encoding
2. Count lines using sum(1 for _ in file)
3. On UnicodeDecodeError: log debug warning, return -1 (signals binary/skip)
4. On other errors: re-raise
```

### DATA
- **Input**: Path to file
- **Output**: Line count (int), or -1 if binary/non-UTF-8

### TEST CASES
```python
def test_count_lines_normal_file(tmp_path):
    """Test counting lines in a normal text file."""
    
def test_count_lines_empty_file(tmp_path):
    """Test counting lines in empty file returns 0."""

def test_count_lines_binary_file(tmp_path):
    """Test binary file returns -1."""
```

---

## Task 2.4: Implement load_allowlist()

### WHAT
```python
def load_allowlist(allowlist_path: Path) -> set[str]
```

### ALGORITHM
```
1. If file doesn't exist, return empty set
2. Read file lines
3. Strip whitespace, skip empty lines and # comments
4. Normalize paths to OS-native format (replace / or \ appropriately)
5. Return set of normalized paths
```

### DATA
- **Input**: Path to allowlist file
- **Output**: Set of normalized path strings

### TEST CASES
```python
def test_load_allowlist_with_comments(tmp_path):
    """Test that # comments are ignored."""

def test_load_allowlist_blank_lines(tmp_path):
    """Test that blank lines are ignored."""

def test_load_allowlist_path_normalization(tmp_path):
    """Test path separator normalization to OS-native format."""

def test_load_allowlist_missing_file(tmp_path):
    """Test missing file returns empty set."""
```

---

## Task 2.5: Implement get_file_metrics()

### WHAT
```python
def get_file_metrics(files: list[Path], project_dir: Path) -> list[FileMetrics]
```

### ALGORITHM
```
1. For each file path:
2.   Calculate absolute path from project_dir
3.   Call count_lines()
4.   If count >= 0, create FileMetrics and add to result
5. Return list of FileMetrics
```

### DATA
- **Input**: List of relative file paths, project directory
- **Output**: List of FileMetrics (excludes binary files)

### TEST CASES
```python
def test_get_file_metrics_multiple_files(tmp_path):
    """Test getting metrics for multiple files."""

def test_get_file_metrics_skips_binary(tmp_path):
    """Test that binary files are excluded from results."""
```

---

## Task 2.6: Implement check_file_sizes()

### WHAT
```python
def check_file_sizes(
    project_dir: Path, 
    max_lines: int, 
    allowlist: set[str]
) -> CheckResult
```

### ALGORITHM
```
1. Call list_files() to get all project files
2. Call get_file_metrics() for line counts
3. Separate violations (> max_lines) from passing files
4. Filter out allowlisted paths from violations
5. Count allowlisted files
6. Detect stale allowlist entries (missing files or under limit)
7. Sort violations by line_count descending
8. Return CheckResult
```

### DATA
- **Input**: project_dir, max_lines threshold, allowlist set
- **Output**: CheckResult with violations, counts, stale entries

### TEST CASES
```python
def test_check_file_sizes_all_pass(tmp_path):
    """Test when all files are under limit."""

def test_check_file_sizes_with_violations(tmp_path):
    """Test detecting files over limit."""

def test_check_file_sizes_with_allowlist(tmp_path):
    """Test that allowlisted files don't cause failure."""

def test_check_file_sizes_stale_allowlist_missing_file(tmp_path):
    """Test detecting allowlist entry for non-existent file."""

def test_check_file_sizes_stale_allowlist_under_limit(tmp_path):
    """Test detecting allowlist entry for file now under limit."""

def test_check_file_sizes_violations_sorted_descending(tmp_path):
    """Test violations are sorted by line count descending."""
```

---

## Task 2.7: Implement render_output()

### WHAT
```python
def render_output(result: CheckResult, max_lines: int) -> str
```

### ALGORITHM
```
1. If passed:
   a. Build success message with counts
   b. If stale_entries: append info section
2. If not passed:
   a. Build failure header with violation count
   b. List each violation with path and line count
   c. Append guidance message
3. Return formatted string
```

### DATA
- **Input**: CheckResult, max_lines for display
- **Output**: Formatted string for terminal output

### TEST CASES
```python
def test_render_output_success():
    """Test success message format."""

def test_render_output_success_with_stale():
    """Test success message includes stale allowlist info."""

def test_render_output_failure():
    """Test failure message format with violations listed."""
```

---

## Task 2.8: Implement render_allowlist()

### WHAT
```python
def render_allowlist(violations: list[FileMetrics]) -> str
```

### ALGORITHM
```
1. For each violation:
2.   Output path with forward slashes (cross-platform allowlist format)
3. Join with newlines
```

### DATA
- **Input**: List of FileMetrics violations
- **Output**: Newline-separated paths for allowlist file

### TEST CASES
```python
def test_render_allowlist_format():
    """Test allowlist output uses forward slashes."""

def test_render_allowlist_empty():
    """Test empty violations produces empty string."""
```

---

## Verification Checklist
- [ ] All tests in `tests/checks/test_file_sizes.py` pass
- [ ] `src/mcp_coder/checks/__init__.py` exports all public symbols
- [ ] `src/mcp_coder/checks/file_sizes.py` implements all functions
- [ ] Run pylint, mypy on new files
- [ ] Binary file handling works correctly (returns -1, excluded from metrics)
