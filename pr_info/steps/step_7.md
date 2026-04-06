# Step 7: Documentation updates + config system docstrings

> **Context:** See `pr_info/steps/summary.md` for full issue context.

## Goal

Add docstring notes about the two config systems and update documentation to reflect the changes made in steps 1-6.

## Changes

### MODIFY: `src/mcp_coder/utils/user_config.py`

Update the module docstring to mention the two config systems:

```python
"""User configuration utilities for MCP Coder.

This module reads user-level configuration from config.toml files located
in user-specific configuration directories (e.g. ~/.mcp_coder/config.toml).

    config.toml  — user config (API tokens, Jenkins, coordinator settings)
    pyproject.toml — project config (formatter settings, GitHub deps)

For project-level configuration from pyproject.toml, see pyproject_config.py.
"""
```

### MODIFY: `docs/configuration/config.md`

Add a new section near the top (after "Quick Reference", before "Configuration File Locations"):

```markdown
## Configuration Systems

MCP Coder uses two separate configuration files for different purposes:

| File | Scope | Module | Contents |
|------|-------|--------|----------|
| `config.toml` | Per-user | `utils/user_config.py` | API tokens, Jenkins credentials, coordinator settings, LLM provider |
| `pyproject.toml` | Per-project | `utils/pyproject_config.py` | Formatter settings (`[tool.black]`, `[tool.isort]`), GitHub dependency overrides (`[tool.mcp-coder.install-from-github]`) |

**Priority:** Environment variables > config file values (for both systems).

`config.toml` lives in the user's home directory and is never committed to git.
`pyproject.toml` lives in the project root and is committed to git.
```

### MODIFY: `docs/environments/environments.md`

Targeted updates only:

1. In the "Entry Point Matrix" table, remove the `reinstall.bat` reference if present (it's not currently there, so this may be a no-op).

2. In any section referencing `reinstall_local.bat`, note that it now reads GitHub dependencies from `pyproject.toml` via `tools/read_github_deps.py` instead of hardcoding URLs.

3. Add a note about version printing in the launcher description:
   > All launcher scripts (`claude.bat`, `claude_local.bat`, `icoder.bat`, `icoder_local.bat`) print MCP server versions (`mcp-workspace --version`, `mcp-tools-py --version`) at startup after tool verification.

## Verification

- Documentation reads correctly
- No broken references
- pylint, mypy, pytest clean

## Commit

```
docs: document config systems, update environments (#640)
```

---

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_7.md.

1. Update the module docstring in src/mcp_coder/utils/user_config.py to mention the 
   two config systems (config.toml vs pyproject.toml).
2. Add a "Configuration Systems" section to docs/configuration/config.md explaining 
   both config files.
3. Make targeted updates to docs/environments/environments.md reflecting the changes: 
   reinstall_local.bat now uses read_github_deps.py, launchers print versions.
   Do NOT rewrite — only add/update what changed.

Note: pyproject_config.py should already have its docstring from step 2.
Run all quality checks.
```
