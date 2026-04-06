# Step 4: Refactor `_build_github_install_section()` + regression test

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Replace inline `tomllib` reading in `_build_github_install_section()` with a call to `get_github_install_config()`. Add a focused regression test for the function itself.

## Changes

### CREATE: `tests/workflows/vscodeclaude/test_build_github_install_section.py`

Regression test that verifies the output format of `_build_github_install_section()`:

```python
"""Regression test for _build_github_install_section output format."""

from pathlib import Path
from mcp_coder.workflows.vscodeclaude.workspace import _build_github_install_section


class TestBuildGithubInstallSection:

    def test_output_contains_install_lines_for_packages(self, tmp_path: Path) -> None:
        """Output contains uv pip install for each package from config."""
        # Write pyproject.toml with packages and packages-no-deps
        # Call _build_github_install_section(tmp_path)
        # Assert 'uv pip install "pkg1" "pkg2"' in output
        # Assert '--no-deps' NOT in the packages line

    def test_output_contains_no_deps_for_packages_no_deps(self, tmp_path: Path) -> None:
        """Output contains uv pip install --no-deps for packages-no-deps entries."""
        # Write pyproject.toml with packages-no-deps
        # Call _build_github_install_section(tmp_path)
        # Assert 'uv pip install --no-deps "pkg3"' in output

    def test_output_contains_editable_restore(self, tmp_path: Path) -> None:
        """Output contains uv pip install -e . --no-deps to restore editable install."""
        # Write pyproject.toml with at least one package
        # Assert 'uv pip install -e . --no-deps' in output

    def test_empty_config_returns_empty_string(self, tmp_path: Path) -> None:
        """No packages configured returns empty string."""
        # Write pyproject.toml without install-from-github section
        # Assert result == ""

    def test_missing_pyproject_returns_empty_string(self, tmp_path: Path) -> None:
        """No pyproject.toml returns empty string."""
        # Don't create pyproject.toml
        # Assert result == ""
```

**DATA — helper to write test pyproject.toml:**
```python
def _write_pyproject(tmp_path, packages=None, packages_no_deps=None):
    # Same pattern as test_workspace_startup_script_github.py
```

### MODIFY: `src/mcp_coder/workflows/vscodeclaude/workspace.py`

**WHAT:** Replace inline `tomllib` reading with `get_github_install_config()` call.

**BEFORE (`_build_github_install_section`):**
```python
import tomllib
# ...
with pyproject_path.open("rb") as f:
    config = tomllib.load(f)
gh_config = config.get("tool", {}).get("mcp-coder", {}).get("install-from-github", {})
packages = gh_config.get("packages", [])
packages_no_deps = gh_config.get("packages-no-deps", [])
```

**AFTER:**
```python
from ...utils.pyproject_config import get_github_install_config
# ...
gh_config = get_github_install_config(folder_path)
packages = gh_config.packages
packages_no_deps = gh_config.packages_no_deps
```

**ALGORITHM (unchanged output):**
```
1. gh_config = get_github_install_config(folder_path)
2. if not gh_config.packages and not gh_config.packages_no_deps: return ""
3. Build "uv pip install" line for packages (with deps)
4. Build "uv pip install --no-deps" line for packages_no_deps
5. Append "uv pip install -e . --no-deps" restore line
6. Return joined lines
```

**HOW — cleanup:** Remove `import tomllib` from workspace.py if no longer used elsewhere in that file. (Check: `tomllib` is only used in `_build_github_install_section`, so it can be removed.)

## Verification

- New regression tests pass
- All existing `test_workspace_startup_script_github.py` tests pass (these test the full `create_startup_script` flow with `install_from_github=True`)
- pylint, mypy, pytest all clean

## Commit

```
refactor: use get_github_install_config in workspace (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md.

First create the regression test file tests/workflows/vscodeclaude/test_build_github_install_section.py.
Then refactor _build_github_install_section() in src/mcp_coder/workflows/vscodeclaude/workspace.py 
to use get_github_install_config() from pyproject_config. Remove the tomllib import if no longer 
needed. Run all quality checks — especially the existing test_workspace_startup_script_github.py tests.
```
