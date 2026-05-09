# vscodeclaude: macOS/Linux launch support — implementation summary

**Issue:** #963

## Goal

Make `mcp-coder vscodeclaude launch` work on macOS and Linux. Today the non-Windows branch in `create_startup_script` raises `NotImplementedError`. This implementation generates a POSIX shell-script counterpart to `.vscodeclaude_start.bat`, with platform decisions made in Python (no `case $(uname)` in the generated shell).

## Design decisions (from issue, settled)

| Topic | Decision |
|---|---|
| POSIX template structure | One set of `*_POSIX` constants covering macOS and Linux; per-platform values baked in by Python at script-creation time. |
| MCP config selection | Python resolves `platform.system()` → `.mcp.macos.json` / `.mcp.linux.json` / `.mcp.json` and bakes `--mcp-config <file>` into each section template literally. |
| `validate_mcp_json` | Requires the platform-appropriate config file; clear error naming the missing file. |
| `tasks.json` command | Windows: bare filename (unchanged). POSIX: `./<script-name>`. |
| Setup commands | Add `setup_commands_macos`. Resolution on Darwin: `macos` → fallback to `linux`. Linux: `linux`. Windows: `windows` (unchanged). |
| `.mcp.linux.json` | Authored in this PR; literal copy of `.mcp.macos.json` (same shape works on both). |
| POSIX failure UX | `set -euo pipefail` + `trap … ERR` inline at top of each POSIX script. No retry loop (AV/IDE-lock cause is Windows-specific). |
| GitHub override install on POSIX | Not emitted. POSIX uses only `uv sync --extra dev`. `skip_github_install` is a no-op for POSIX. (Whole mechanism is on the way out via #956.) |
| POSIX title escaping | Inline `value.replace("'", "'\\''")` + single-quote wrapping. No helper function. |

## Architectural / design changes

The change is small and surgical. No new modules, no new public APIs.

- **`workspace.py`**: a single module-level constant `_MCP_CONFIG_FILES: dict[str, str]` becomes the source of truth for "which `.mcp.*.json` does this platform need". Used by `validate_mcp_json` and `create_startup_script`. Avoids drift between validation and script generation.
- **`workspace.create_startup_script`**: the `else: raise NotImplementedError` branch is replaced by a POSIX path that mirrors the Windows path's structure (single / multi / no command, intervention) but skips `_build_github_install_section()` and uses POSIX shell semantics. The function signature is unchanged.
- **`workspace.create_vscode_task`**: gains a per-platform decision on the `command` field of `tasks.json` (`<name>` vs `./<name>`). Decided in Python, not in `TASKS_JSON_TEMPLATE`.
- **`session_launch.prepare_and_launch_session`**: the binary `is_windows` check for setup-commands becomes a small platform → key-list lookup with a Darwin → Linux fallback.
- **`types.RepoVSCodeClaudeConfig`**: gains an optional `setup_commands_macos: list[str]` field.
- **`config.load_repo_vscodeclaude_config`**: parses the new key with the same list / JSON-string / plain-string handling as the existing two keys.
- **`templates.py`**: gains six POSIX template constants paralleling the six Windows ones. The shared 3-line POSIX header (`#!/usr/bin/env bash`, `set -euo pipefail`, `trap … ERR`) is inlined at the top of `STARTUP_SCRIPT_POSIX` and `INTERVENTION_SCRIPT_POSIX` rather than factored into a separate constant — the duplication is trivial and the constant adds indirection.
- **`.mcp.linux.json`** (new file at repo root): literal copy of `.mcp.macos.json`. Required so when the workflow clones *this* repo on Linux, validation passes.

## Files to create or modify

### Create
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md` … `step_5.md`
- `.mcp.linux.json`

### Modify
- `src/mcp_coder/workflows/vscodeclaude/types.py` — add `setup_commands_macos`.
- `src/mcp_coder/workflows/vscodeclaude/config.py` — parse `setup_commands_macos`.
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` — `_MCP_CONFIG_FILES` constant; platform-aware `validate_mcp_json`; platform-aware `create_vscode_task`; POSIX path in `create_startup_script`.
- `src/mcp_coder/workflows/vscodeclaude/templates.py` — six new POSIX template constants.
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — Darwin → Linux fallback in `prepare_and_launch_session`.
- `tests/workflows/vscodeclaude/test_types.py` — assert new field shape.
- `tests/workflows/vscodeclaude/test_config.py` — assert parsing of `setup_commands_macos`.
- `tests/workflows/vscodeclaude/test_workspace.py` — parametrized `validate_mcp_json` and `create_vscode_task` tests.
- `tests/workflows/vscodeclaude/test_session_launch.py` — Darwin resolution-order tests.
- `tests/workflows/vscodeclaude/test_workspace_startup_script.py` — parametrize existing tests over Windows / Darwin / Linux; add POSIX-specific assertions.

### Out of scope (per issue)
- POSIX twin of GitHub override install mechanism (deferred to #956).
- `code` CLI availability detection in `launch_vscode`.
- Window-title-based session detection on POSIX.

## Step plan (each = one commit)

1. **Step 1** — Add `setup_commands_macos` to `RepoVSCodeClaudeConfig` and `load_repo_vscodeclaude_config`. Tests.
2. **Step 2** — Add `.mcp.linux.json`; introduce `_MCP_CONFIG_FILES`; make `validate_mcp_json` platform-aware. Tests.
3. **Step 3** — Make `create_vscode_task` emit `./<name>` on POSIX. Tests.
4. **Step 4** — Wire `prepare_and_launch_session` to resolve setup commands per platform with Darwin → Linux fallback. Tests.
5. **Step 5** — Add six POSIX templates; replace the `NotImplementedError` branch in `create_startup_script` with the POSIX path. Parametrized tests.

Steps are ordered by dependency: step 4 uses step 1's new key; step 5 uses step 2's `_MCP_CONFIG_FILES`. Steps 1–3 are independent of each other.

## Verification (every step)

After each step, all three checks must pass per `CLAUDE.md`:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_mypy_check`
- `mcp__tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`

POSIX-only assertions (e.g. `chmod 0o755` taking effect) must use `pytest.mark.skipif(sys.platform == "win32")`.
