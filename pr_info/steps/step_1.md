# Step 1: Shipped Default Prompts + `prompt_loader.py` Module with Tests

## References
- Summary: `pr_info/steps/summary.md`
- Issue: #648

## WHERE

**New files:**
- `src/mcp_coder/prompts/system-prompt.md` — shipped default system prompt
- `src/mcp_coder/prompts/project-prompt.md` — shipped default project prompt
- `src/mcp_coder/prompts/prompt_loader.py` — config reader + path resolver + loader
- `tests/prompts/__init__.py` — test package
- `tests/prompts/test_prompt_loader.py` — comprehensive tests

**Modified files:**
- `src/mcp_coder/utils/pyproject_config.py` — add `get_prompts_config()`

## WHAT

### `pyproject_config.py` — new function

```python
@dataclass(frozen=True)
class PromptsConfig:
    system_prompt: str | None    # path or None (use default)
    project_prompt: str | None   # path or None (use default)
    claude_system_prompt_mode: str  # "append" or "replace"

def get_prompts_config(project_dir: Path) -> PromptsConfig:
    """Read [tool.mcp-coder.prompts] from pyproject.toml."""
```

### `prompt_loader.py` — three public functions

```python
def load_system_prompt(project_dir: Path | None = None) -> str:
    """Load system prompt content. Falls back to shipped default."""

def load_project_prompt(project_dir: Path | None = None) -> str:
    """Load project prompt content. Falls back to shipped default."""

def load_prompts(project_dir: Path | None = None) -> tuple[str, str, PromptsConfig]:
    """Load both prompts + config. Main entry point.
    Returns (system_prompt, project_prompt, config)."""

def get_project_prompt_path(project_dir: Path | None = None) -> Path | None:
    """Resolve the project prompt file path (for redundancy detection).
    Returns None when using shipped default."""
```

### `system-prompt.md`

Comprehensive system prompt covering: role definition (AI coding assistant), MCP tool usage instructions, git conventions, coding practices, quality standards.

### `project-prompt.md`

Generic baseline: "This is a Python project. Follow existing code conventions. Run quality checks after changes." With comments indicating where to add project-specific instructions.

## HOW

- `get_prompts_config()` follows the exact same pattern as `get_github_install_config()` in `pyproject_config.py` (read TOML, extract nested keys, return dataclass)
- `prompt_loader.py` uses `importlib.resources.files("mcp_coder.prompts")` for shipped defaults (same pattern as `data_files.py`)
- Path resolution order: if configured path is absolute → use as-is; if relative → resolve against `project_dir`; if neither exists → try as package-relative
- No new dependencies

## ALGORITHM

```
def load_prompts(project_dir):
    config = get_prompts_config(project_dir) if project_dir else PromptsConfig(defaults)
    system = _resolve_and_read(config.system_prompt, project_dir) or _read_shipped_default("system-prompt.md")
    project = _resolve_and_read(config.project_prompt, project_dir) or _read_shipped_default("project-prompt.md")
    return (system, project, config)

def _read_shipped_default(filename):
    return files("mcp_coder.prompts").joinpath(filename).read_text()

def _resolve_and_read(configured_path, project_dir):
    if configured_path is None: return None
    path = Path(configured_path)
    if path.is_absolute(): return path.read_text() if path.exists() else None
    if project_dir: candidate = project_dir / path; return candidate.read_text() if candidate.exists() else None
    return None
```

## DATA

```python
PromptsConfig(
    system_prompt="path/to/custom.md" | None,
    project_prompt=".claude/CLAUDE.md" | None,
    claude_system_prompt_mode="append" | "replace",
)

load_prompts() -> tuple[str, str, PromptsConfig]
# (system_prompt_content, project_prompt_content, config)
```

## TESTS (`tests/prompts/test_prompt_loader.py`)

1. **`test_load_prompts_defaults`** — no project_dir → returns shipped defaults (non-empty strings)
2. **`test_load_prompts_no_pyproject`** — project_dir exists but no pyproject.toml → shipped defaults
3. **`test_load_prompts_empty_section`** — pyproject.toml exists but no `[tool.mcp-coder.prompts]` → shipped defaults
4. **`test_load_prompts_custom_system_prompt`** — configured path resolves correctly, content loaded
5. **`test_load_prompts_custom_project_prompt`** — configured path resolves correctly
6. **`test_load_prompts_absolute_path`** — absolute path works
7. **`test_load_prompts_missing_file_falls_back`** — configured path doesn't exist → shipped default
8. **`test_get_prompts_config_defaults`** — missing config returns all-None/default-mode
9. **`test_get_prompts_config_replace_mode`** — `claude-system-prompt-mode = "replace"` parsed
10. **`test_get_project_prompt_path_default`** — returns None for shipped default
11. **`test_get_project_prompt_path_custom`** — returns resolved Path
12. **`test_shipped_defaults_exist`** — system-prompt.md and project-prompt.md are non-empty and loadable

## LLM Prompt

```
Read pr_info/steps/summary.md for overall context, then implement Step 1.

Create the shipped default prompt files (system-prompt.md, project-prompt.md) in
src/mcp_coder/prompts/. Add get_prompts_config() to pyproject_config.py following
the existing get_github_install_config() pattern. Create prompt_loader.py with
load_prompts(), load_system_prompt(), load_project_prompt(), and
get_project_prompt_path(). Write comprehensive tests in tests/prompts/test_prompt_loader.py.

Use importlib.resources for shipped defaults (same pattern as data_files.py).
All quality checks must pass.
```
