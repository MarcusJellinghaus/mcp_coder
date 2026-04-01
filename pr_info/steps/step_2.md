# Step 2: Rename from_github → install_from_github across all source and config

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. This is Step 2 of issue #684.
>
> Rename `from-github` → `install-from-github` in pyproject.toml config, and
> `from_github` → `install_from_github` in all Python source files listed below.
> Also rename the CLI flag `--from-github` → `--install-from-github`.
> After editing, run all three code quality checks (pylint, mypy, pytest).
> ALL checks must pass. Commit with message:
> "rename from-github to install-from-github across all layers (#684)"

## WHERE

23 files to edit (in dependency order — types first, consumers last):

1. `pyproject.toml`
2. `src/mcp_coder/workflows/vscodeclaude/types.py`
3. `src/mcp_coder/workflows/vscodeclaude/helpers.py`
4. `src/mcp_coder/workflows/vscodeclaude/workspace.py`
5. `src/mcp_coder/workflows/vscodeclaude/session_launch.py`
6. `src/mcp_coder/workflows/vscodeclaude/session_restart.py`
7. `src/mcp_coder/cli/parsers.py`
8. `src/mcp_coder/cli/commands/coordinator/commands.py`

**14 test files** (mechanical rename of references):

9. `tests/workflows/vscodeclaude/test_cleanup.py`
10. `tests/workflows/vscodeclaude/test_status_display.py`
11. `tests/workflows/vscodeclaude/test_orchestrator_launch.py`
12. `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`
13. `tests/workflows/vscodeclaude/test_workspace_startup_script_github.py`
14. `tests/workflows/vscodeclaude/test_sessions.py`
15. `tests/workflows/vscodeclaude/test_helpers.py`
16. `tests/cli/commands/coordinator/test_commands.py`
17. `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`
18. `tests/workflows/vscodeclaude/test_types.py`
19. `tests/workflows/vscodeclaude/test_orchestrator_cache.py`
20. `tests/workflows/vscodeclaude/test_closed_issues_integration.py`
21. `tests/workflows/vscodeclaude/test_cache_aware.py`
22. `tests/workflows/vscodeclaude/test_orchestrator_regenerate.py`

## WHAT — Per-file changes

### 1. `pyproject.toml`
```toml
# OLD
[tool.mcp-coder.from-github]
# NEW
[tool.mcp-coder.install-from-github]
```

### 2. `types.py` — TypedDict field
```python
# OLD
from_github: bool
# NEW
install_from_github: bool
```

### 3. `helpers.py` — `build_session()` parameter + dict key + docstring
```python
# OLD: parameter name, docstring line, and dict key "from_github"
# NEW: parameter name, docstring line, and dict key "install_from_github"
```
Affected: function signature, docstring, return dict key.

### 4. `workspace.py` — Two functions

**`_build_github_install_section()`**: 
- Docstring: `[tool.mcp-coder.from-github]` → `[tool.mcp-coder.install-from-github]`
- TOML lookup string: `.get("from-github", {})` → `.get("install-from-github", {})`

**`create_startup_script()`**:
- Parameter: `from_github: bool = False` → `install_from_github: bool = False`
- Docstring: `from_github:` → `install_from_github:` and config reference
- Usage: `if from_github:` → `if install_from_github:`

### 5. `session_launch.py` — Three functions

**`prepare_and_launch_session()`**: parameter name + docstring + 2 keyword arg passes  
**`process_eligible_issues()`**: parameter name + docstring + 1 keyword arg pass  
**`regenerate_session_files()`**: local variable + `session.get("from_github", False)` → `session.get("install_from_github", False)` + keyword arg pass

### 6. `session_restart.py` — `restart_closed_sessions()`
```python
# OLD
"from_github": session.get("from_github", False),
# NEW
"install_from_github": session.get("install_from_github", False),
```

### 7. `parsers.py` — CLI flag
```python
# OLD
"--from-github",
# NEW
"--install-from-github",
```

### 8. `commands.py` — Two occurrences of getattr + variable name
```python
# OLD (lines ~545, ~723)
from_github = getattr(args, "from_github", False)
# NEW
install_from_github = getattr(args, "install_from_github", False)
```
Plus corresponding keyword arg changes when passing to `process_eligible_issues()` and `prepare_and_launch_session()`.

### 9–22. Test files (14 files)

All test files: mechanical rename of `from_github` → `install_from_github` and `from-github` → `install-from-github` in string literals, variable names, dict keys, and function call arguments.

## HOW

- Each file: use `edit_file` with exact old_text → new_text replacements
- No new imports, no structural changes
- The rename is mechanical — same logic, new names

## ALGORITHM (rename strategy)

```
1. Edit pyproject.toml config section header
2. Edit TypedDict field (types.py)
3. Edit build_session() in helpers.py (param + dict key + docstring)
4. Edit workspace.py (TOML string lookup + param + docstring + usage)
5. Edit session_launch.py (3 functions: params + docstrings + keyword args + session.get)
6. Edit session_restart.py (dict key + session.get)
7. Edit parsers.py (CLI flag string)
8. Edit commands.py (getattr + variable + keyword args)
9. Rename `from_github` → `install_from_github` and `from-github` → `install-from-github` in all 14 test files (mechanical find-and-replace)
10. Run pylint, mypy, pytest — all must pass
```

## DATA

- `VSCodeClaudeSession` TypedDict: field rename `from_github` → `install_from_github`
- All function signatures: parameter rename `from_github` → `install_from_github`
- Session dict keys: `"from_github"` → `"install_from_github"`
- TOML config key: `"from-github"` → `"install-from-github"`
- CLI flag: `"--from-github"` → `"--install-from-github"` (argparse stores as `install_from_github`)

## Expected Outcome

- pylint: PASS
- mypy: PASS
- pytest: PASS (including `test_pyproject_install_from_github_config_exists` from Step 1)
