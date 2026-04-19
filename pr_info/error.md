# Pre-flight check failed

## Missing dependency: mcp_workspace.git_operations

Issue ② (MarcusJellinghaus/mcp-workspace#98) has not been completed.
`mcp_workspace.git_operations` does not exist as a top-level package.
Currently only `mcp_workspace.file_tools.git_operations` exists.

This issue cannot proceed until the dependency is resolved.

## Step 4 blocked (2026-04-19)

Attempted to delete local `src/mcp_coder/utils/git_operations/` and switch shim imports to `mcp_workspace.file_tools.git_operations.*`. Runtime error:

```
ModuleNotFoundError: No module named 'mcp_workspace.file_tools.git_operations.branch_queries';
'mcp_workspace.file_tools.git_operations' is not a package
```

The installed version of `mcp_workspace` does not expose `file_tools.git_operations` submodules as importable packages. Steps 1-3 completed because the shim imports from the local copy. Step 4 (delete local copy) requires the external dependency to be fully available.

**Action needed**: Update and reinstall `mcp_workspace` so that `mcp_workspace.file_tools.git_operations.*` submodules are importable, then retry Step 4.
