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

- Uses `importlib.resources.files("mcp_coder")` (already imported in `data_files.py` — same pattern).
- Fallback walks from `Path(mcp_coder.__file__).parent` up at most 3 levels looking for `.claude/skills/`.
- Validates that at least `skills/` subdir exists before returning.
- On failure, calls `sys.exit(1)` with a terse error message.

## ALGORITHM

```python
def _find_claude_source_dir() -> Path:
    # 1. Try importlib.resources (wheel install)
    pkg_path = Path(str(files("mcp_coder"))) / "resources" / "claude"
    if pkg_path.is_dir() and (pkg_path / "skills").is_dir():
        return pkg_path

    # 2. Fallback: walk up from package __file__ to find repo-root .claude/
    pkg_dir = Path(__file__).resolve().parent  # cli/commands/
    for ancestor in pkg_dir.parents:
        candidate = ancestor / ".claude"
        if candidate.is_dir() and (candidate / "skills").is_dir():
            return candidate

    # 3. Both failed
    logger.error("Cannot find Claude skill files. Is mcp-coder installed correctly?")
    sys.exit(1)
```

## DATA

- **Returns:** `Path` to a directory that contains `skills/`, `knowledge_base/`, `agents/` subdirs.
- **Raises:** `SystemExit(1)` if both lookups fail.
- **Constant:** `DEPLOY_SUBDIRS = ("skills", "knowledge_base", "agents")` — used here for validation and in step 4 for deploy.

## TESTS

```python
class TestFindClaudeSourceDir:
    def test_finds_via_importlib_resources(self, tmp_path, monkeypatch):
        """Returns importlib.resources path when resources/claude/skills/ exists."""

    def test_falls_back_to_repo_root(self, tmp_path, monkeypatch):
        """Falls back to repo-root .claude/ when importlib path is empty."""

    def test_exits_when_both_fail(self, tmp_path, monkeypatch):
        """Calls sys.exit(1) when neither location has skills/."""

    def test_requires_skills_subdir(self, tmp_path, monkeypatch):
        """Directory without skills/ subdir is rejected even if it exists."""
```

Tests use `monkeypatch` to override `importlib.resources.files` return value and `__file__` ancestry. Use `tmp_path` to create fake directory structures.
