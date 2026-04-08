# Step 1: Build-time packaging infrastructure

**Summary reference:** See `pr_info/steps/summary.md` for overall architecture.

## Goal

Make `.claude/{skills,knowledge_base,agents}/` ship inside the wheel so downstream users who `pip install mcp-coder` get the skill files bundled.

## LLM Prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement step 1: create `setup.py` with a custom `build_py` command that copies skill files into the package at build time, update `pyproject.toml` package-data, and add the build artifact to `.gitignore`. Write tests first (TDD), then implement, then run all three code quality checks.

## WHERE

| File | Action |
|------|--------|
| `setup.py` | **Create** — custom build_py hook |
| `pyproject.toml` | **Edit** — add `"resources/claude/**/*"` to package-data |
| `.gitignore` | **Edit** — add `src/mcp_coder/resources/claude/` |
| `tests/cli/commands/test_init.py` | **Edit** — add test for build-time copy |

## WHAT

### `setup.py` — Custom build_py

```python
import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

class BuildPyWithSkills(build_py):
    """Copy .claude/ skill dirs into package resources before building."""

    def run(self) -> None:
        _copy_claude_resources()
        super().run()

def _copy_claude_resources() -> None:
    """Copy .claude/{skills,knowledge_base,agents}/ → src/mcp_coder/resources/claude/."""
    ...

setup(cmdclass={"build_py": BuildPyWithSkills})
```

### Signatures

```python
# setup.py
def _copy_claude_resources() -> None: ...

class BuildPyWithSkills(build_py):
    def run(self) -> None: ...
```

## HOW

- `setup.py` works alongside `pyproject.toml` — setuptools merges both. The `cmdclass` override is the standard pattern for pre-build hooks.
- `pyproject.toml` already has `[tool.setuptools.package-data]` with `prompts/*.md` and `config/*.json` — add `"resources/claude/**/*"` on a new line.

## ALGORITHM — `_copy_claude_resources()`

```
repo_root = Path(__file__).parent
source = repo_root / ".claude"
dest = repo_root / "src" / "mcp_coder" / "resources" / "claude"
for subdir in ["skills", "knowledge_base", "agents"]:
    if (source / subdir).exists():
        shutil.copytree(source / subdir, dest / subdir, dirs_exist_ok=True)
```

## DATA

- No return values — side effect only (copies files to disk).
- The three subdirectories are: `skills`, `knowledge_base`, `agents`.
- Excludes: `CLAUDE.md`, `settings.local.json` (they live directly in `.claude/`, not in subdirs).

## TESTS

### Unit tests (fast)

Load `setup.py` via `importlib.util.spec_from_file_location` to exercise `_copy_claude_resources()` directly:

```python
class TestBuildPyWithSkills:
    def test_copy_claude_resources_creates_target_dirs(self, tmp_path):
        """_copy_claude_resources copies skills/knowledge_base/agents."""

    def test_copy_claude_resources_skips_claude_md(self, tmp_path):
        """CLAUDE.md and settings.local.json are not copied."""

    def test_copy_claude_resources_overwrites_stale_build_artifacts(self, tmp_path):
        """Re-running copy replaces stale files (build artifact, not user files)."""
```

### Integration test (slow — wheel build)

One integration test that copies the repo to a tmp dir, runs `python -m build --wheel`, and inspects the resulting `.whl` (via `zipfile`) to confirm files under `resources/claude/skills/`, `resources/claude/knowledge_base/`, and `resources/claude/agents/` are present inside the wheel. This is the authoritative check for packaging correctness (it catches anything package-data / MANIFEST misses — which is why MANIFEST.in is intentionally NOT added in this step).

- Mark slow/integration (e.g. a dedicated marker) so it is excluded from fast unit runs.
- Keep it to a single test — it is expensive (build invocation).

## pyproject.toml change

```toml
[tool.setuptools.package-data]
mcp_coder = [
    "prompts/*.md",
    "config/*.json",
    "resources/claude/**/*"
]
```

## .gitignore addition

```
# Build artifact: skill files copied at build time (canonical source: .claude/)
src/mcp_coder/resources/claude/
```
