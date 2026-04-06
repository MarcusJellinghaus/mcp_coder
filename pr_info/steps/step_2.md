# Step 2: Create `pyproject_config.py` with tests

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Create the shared `pyproject.toml` reading utility with typed, section-specific functions. Write tests first (TDD).

## Changes

### CREATE: `tests/utils/test_pyproject_config.py`

Tests for all three public functions.

```python
class TestGetGithubInstallConfig:
    # test_returns_packages_and_no_deps(tmp_path)
    #   Write pyproject.toml with both lists -> verify both returned
    # test_returns_empty_when_section_missing(tmp_path)
    #   Write pyproject.toml without section -> verify empty lists
    # test_returns_empty_when_file_missing(tmp_path)
    #   No pyproject.toml -> verify empty lists
    # test_returns_empty_when_lists_empty(tmp_path)
    #   Section exists with empty lists -> verify empty lists

class TestGetFormatterConfig:
    # test_reads_black_and_isort(tmp_path)
    #   Write pyproject.toml with both -> verify both returned
    # test_returns_empty_when_no_tool_section(tmp_path)
    #   No [tool] section -> verify empty dict
    # test_returns_empty_when_file_missing(tmp_path)
    #   No pyproject.toml -> verify empty dict

class TestCheckLineLengthConflicts:
    # (reuse existing test patterns from tests/formatters/test_config_reader.py)
    # test_detects_conflict
    # test_no_conflict_when_matching
    # test_no_conflict_when_missing
```

### CREATE: `src/mcp_coder/utils/pyproject_config.py`

**WHERE:** `src/mcp_coder/utils/pyproject_config.py`

**Module docstring:**
```
Project-level configuration reader for pyproject.toml.

This module reads tool configuration from pyproject.toml (project config).
For user-level configuration (API tokens, Jenkins, etc.), see user_config.py
which reads from config.toml.
```

#### Function: `get_github_install_config`

```python
def get_github_install_config(project_dir: Path) -> GitHubInstallConfig:
```

**DATA — return type:**
```python
@dataclass(frozen=True)
class GitHubInstallConfig:
    packages: list[str]          # installed WITH deps
    packages_no_deps: list[str]  # installed WITHOUT deps
```

**ALGORITHM:**
```
1. path = project_dir / "pyproject.toml"
2. if not path.exists(): return GitHubInstallConfig([], [])
3. data = tomllib.load(path)
4. gh = data["tool"]["mcp-coder"]["install-from-github"]  # with .get() defaults
5. return GitHubInstallConfig(packages=gh["packages"], packages_no_deps=gh["packages-no-deps"])
```

#### Function: `get_formatter_config`

```python
def get_formatter_config(project_dir: Path, filename: str = "pyproject.toml") -> dict[str, Any]:
```

**ALGORITHM:**
```
1. path = project_dir / filename
2. if not path.exists(): return {}
3. data = tomllib.load(path)
4. tool = data.get("tool", {})
5. result = {}; if "black" in tool: result["black"] = tool["black"]; same for "isort"
6. return result
```

**Returns:** `{"black": {...}, "isort": {...}}` — same structure as current `read_formatter_config()`.

#### Function: `check_line_length_conflicts`

```python
def check_line_length_conflicts(config: dict[str, Any]) -> str | None:
```

Exact same logic as current `config_reader.check_line_length_conflicts`. Moved here, not copied — the original will delegate in step 3.

### UPDATE: existing `tests/test_pyproject_config.py`

The existing test `test_pyproject_install_from_github_config_exists` tests the raw TOML structure. Keep it — it validates the actual `pyproject.toml` file. The new tests in `tests/utils/test_pyproject_config.py` test the utility functions with synthetic data.

## Verification

- New tests pass
- All existing tests pass
- pylint, mypy clean

## Commit

```
feat: add shared pyproject.toml config reader (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Create the test file first (tests/utils/test_pyproject_config.py), then implement 
src/mcp_coder/utils/pyproject_config.py with GitHubInstallConfig dataclass and three 
public functions. Run all quality checks.
```
