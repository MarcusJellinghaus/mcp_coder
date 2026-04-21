# Step 7 — Update `.importlinter` and `tach.toml`

> **Reference**: See `pr_info/steps/summary.md` for full context (Issue #833, part 5 of 5).

## Goal

Update architecture configuration files to reflect the new shim module, removed github_operations, and updated boundaries.

## WHERE

- `.importlinter` (modify)
- `tach.toml` (modify)

## WHAT

### `.importlinter` changes

**1. Layered architecture contract — add shim to proper layer:**
- Add `mcp_coder.mcp_workspace_github` alongside `mcp_coder.mcp_workspace_git` in the shim layer line:
  ```
  mcp_coder.mcp_tools_py | mcp_coder.mcp_workspace_git | mcp_coder.mcp_workspace_github
  ```
- Add ignore for shim → local utils (if needed during transition):
  ```
  mcp_coder.mcp_workspace_github -> mcp_workspace.github_operations.**
  ```

**2. Remove `external_services` independence contract:**
- Delete the entire `[importlinter:contract:external_services]` section — `github_operations` no longer exists as a local module.

**3. Update `github_library_isolation` contract:**
- Remove the old exception: `mcp_coder.utils.github_operations.** -> github`
- After deletion, verify if `mcp_coder.mcp_workspace_github -> github` exception is needed (the shim re-exports but may not directly import PyGithub). Add only if lint-imports fails without it.

**4. Update `requests_library_isolation` contract:**
- Remove the old exception: `mcp_coder.utils.github_operations.** -> requests`
- The shim doesn't import `requests` directly, so no new exception should be needed. Verify with lint-imports.

**5. Update `jenkins_independence` contract:**
- Remove `mcp_coder.utils.github_operations` from `forbidden_modules` (it no longer exists)
- Add `mcp_coder.mcp_workspace_github` to `forbidden_modules` (jenkins shouldn't depend on github shim)

**6. Add shim isolation contract (new) — if supported:**
```ini
[importlinter:contract:mcp_workspace_github_isolation]
name = MCP Workspace GitHub Operations Isolation
type = forbidden
source_modules =
    mcp_coder
forbidden_modules =
    mcp_workspace.github_operations
ignore_imports =
    mcp_coder.mcp_workspace_github -> mcp_workspace.github_operations
```

**Note**: import-linter v2.11 may not support external subpackage paths in `forbidden_modules` (same limitation as the git shim contract). If this contract causes unmatched-ignore exit code 1, add it as a TODO comment instead.

### `tach.toml` changes

**1. Add `mcp_coder.mcp_workspace_github` module:**
```toml
[[modules]]
path = "mcp_coder.mcp_workspace_github"
layer = "shim_workspace"
depends_on = []
```

**2. Update dependency lists:**
- Modules that previously depended on `mcp_coder.utils` for github_operations now get their github operations from the shim. Add `mcp_coder.mcp_workspace_github` to `depends_on` for:
  - `mcp_coder.cli` (already has mcp_workspace_git, add mcp_workspace_github)
  - `mcp_coder.workflows` (already has mcp_workspace_git, add mcp_workspace_github)
  - `mcp_coder.workflow_utils` (add mcp_workspace_github)
  - `mcp_coder.checks` (already has mcp_workspace_git, add mcp_workspace_github)
  - `mcp_coder` root module (add if needed)

**3. Add `tests` dependency on shim:**
- `tests` module's `depends_on` should include `{ path = "mcp_coder.mcp_workspace_github" }` since test files will import from the shim

**4. Remove `utils` dependency where it was only for github_operations:**
- Check each module — if `utils` was listed only for github_operations access, it may no longer be needed. However, `utils` still has git_operations, jenkins_operations, and general utilities, so most modules will still depend on it.

## ALGORITHM

No algorithm — configuration file updates.

## DATA

No data structure changes.

## Commit

```
chore: update architecture configs for github shim
```

## LLM Prompt

```
Read pr_info/steps/summary.md for full context, then implement step 7 from pr_info/steps/step_7.md.

Update .importlinter and tach.toml to reflect the new architecture.
After changes, run lint-imports and tach check to verify the configs are correct.
Run all checks (pylint, mypy, pytest unit tests, lint-imports) after implementation.
```
