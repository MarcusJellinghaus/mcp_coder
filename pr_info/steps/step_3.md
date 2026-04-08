# Step 3: Runtime skill source resolver

**Summary reference:** See `pr_info/steps/summary.md` for overall architecture.

## Goal

Add `_find_claude_source_dir()` to `init.py` — a private function that locates the Claude skill/knowledge_base/agents source directory at runtime, supporting both wheel installs and editable installs.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3: add `_find_claude_source_dir()` in `init.py` with dual-lookup logic (importlib.resources for wheel, repo-root fallback for editable). Write tests first (TDD), then implement, then run all three code quality checks.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/cli/commands/init.py` | **Edit** — add `_find_claude_source_dir()` |
| `tests/cli/commands/test_init.py` | **Edit** — add resolver tests |

## WHAT

### `init.py` — `_find_claude_source_dir()`

```python
DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")

def _find_claude_source_dir() -> Path:
    """Locate the Claude resources directory (skills, knowledge_base, agents).

    Tries two locations in order:
    1. Package resources (wheel install): importlib.resources path
    2. Repo root fallback (editable install): walk up from mcp_coder.__file__

    Returns:
        Path to directory containing skills/, knowledge_base/, agents/.

    Raises:
        SystemExit: If neither location has the expected subdirectories.
    """
```

## HOW

- Uses `importlib.resources.files("mcp_coder")` — mirror the pattern in `src/mcp_coder/utils/data_files.py` precisely (use `files()` and `as_file()` if needed to get a concrete `Path`). Add `from importlib.resources import files` to the imports.
- Fallback walks from `Path(__file__).resolve().parent` upward via unbounded `.parents` iteration looking for `.claude/`.
- Validates that **all three** `DEPLOY_SUBDIRS` (`skills`, `knowledge_base`, `agents`) exist under the resolved source before returning — this exercises the `DEPLOY_SUBDIRS` constant already in step 3.
- On failure, calls `sys.exit(1)` with a **detailed** error message including:
  1. What was being looked for (packaged Claude resources: `skills/`, `knowledge_base/`, `agents/`).
  2. Each path that was tried (the importlib.resources path, and each ancestor directory checked).
  3. A remediation hint: `pip install --force-reinstall mcp-coder`.

## ALGORITHM

```python
from importlib.resources import files

def _has_all_subdirs(base: Path) -> bool:
    return all((base / name).is_dir() for name in DEPLOY_SUBDIRS)

def _find_claude_source_dir() -> Path:
    tried: list[Path] = []

    # 1. Try importlib.resources (wheel install) — mirror data_files.py pattern
    pkg_path = Path(str(files("mcp_coder"))) / "resources" / "claude"
    tried.append(pkg_path)
    if pkg_path.is_dir() and _has_all_subdirs(pkg_path):
        return pkg_path

    # 2. Fallback: walk up from this file to find repo-root .claude/ (editable install)
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / ".claude"
        tried.append(candidate)
        if candidate.is_dir() and _has_all_subdirs(candidate):
            return candidate

    # 3. Both failed — detailed error
    logger.error(
        "Cannot locate packaged Claude resources (skills/, knowledge_base/, agents/).\n"
        "Paths tried:\n%s\n"
        "Try reinstalling: pip install --force-reinstall mcp-coder",
        "\n".join(f"  - {p}" for p in tried),
    )
    sys.exit(1)
```

## DATA

- **Returns:** `Path` to a directory that contains `skills/`, `knowledge_base/`, `agents/` subdirs.
- **Raises:** `SystemExit(1)` if both lookups fail.
- **Constant:** `DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")` — defined in this step and used here to validate **all three** subdirs exist under the resolved source. Reused by step 4 for deploy.

## TESTS

```python
class TestFindClaudeSourceDir:
    def test_finds_via_importlib_resources(self, tmp_path, monkeypatch):
        """Returns importlib.resources path when resources/claude/skills/ exists."""

    def test_falls_back_to_repo_root(self, tmp_path, monkeypatch):
        """Falls back to repo-root .claude/ when importlib path is empty."""

    def test_exits_when_both_fail(self, tmp_path, monkeypatch, caplog):
        """Calls sys.exit(1) when neither location has the required subdirs.

        Asserts the error message mentions:
        - What was sought (skills/, knowledge_base/, agents/)
        - At least one of the paths tried
        - The reinstall hint (pip install --force-reinstall mcp-coder)
        """

    def test_requires_all_subdirs(self, tmp_path, monkeypatch):
        """Directory missing any of skills/knowledge_base/agents is rejected."""
```

Tests use `monkeypatch` to override `importlib.resources.files` return value and `__file__` ancestry. Use `tmp_path` to create fake directory structures.
