# Pre-flight check failed

## Missing dependency: mcp_workspace.git_operations

Issue ② (MarcusJellinghaus/mcp-workspace#98) has not been completed.
`mcp_workspace.git_operations` does not exist as a top-level package.
Currently only `mcp_workspace.file_tools.git_operations` exists.

This issue cannot proceed until the dependency is resolved.

## Step 4 blocked (2026-04-19, re-confirmed 2026-04-19)

Attempted to delete local `src/mcp_coder/utils/git_operations/` and switch shim imports to `mcp_workspace.file_tools.git_operations.*`. Runtime error:

```
ModuleNotFoundError: No module named 'mcp_workspace.file_tools.git_operations.branch_queries';
'mcp_workspace.file_tools.git_operations' is not a package
```

The installed version of `mcp_workspace` does not expose `file_tools.git_operations` submodules as importable packages. Steps 1-3 completed because the shim imports from the local copy. Step 4 (delete local copy) requires the external dependency to be fully available.

Second attempt also confirmed:
- Pylint reports `E0401` (unable to import) and `E0611` (no name in module) for all 11 submodules
- Files were restored from reference project `p_workspace` (identical content, relative imports)
- Additional blocker: `github_operations` files cannot import from the shim due to circular import chain: `shim` → `git_operations.*` → `utils.__init__` → `github_operations` → `shim` (still loading). These must keep direct `git_operations` imports.

**Action needed**: Reinstall `mcp_workspace` from latest GitHub source (`pip install --force-reinstall git+https://github.com/MarcusJellinghaus/mcp-workspace.git`) so that `mcp_workspace.file_tools.git_operations.*` submodules are importable, then retry Step 4.
