# Implementation Review Log — feat/mac-support

**Branch**: `feat/mac-support` → `main`
**Mode**: Ad-hoc supervisor review (no `pr_info/steps/summary.md` available — scope inferred from diff and commit log)
**Date started**: 2026-05-03

## Round 1 — 2026-05-03

**Findings** (from engineer subagent + follow-up investigation):
1. `pyproject.toml` mypy override for `mcp_coder.mcp_workspace_github` is stale — file is now a plain re-export shim, no try/except sentinels
2. Launcher activation order: `claude.sh` does B→A (activate then discover); `claude.bat`, `claude_local.sh`, `claude_local.bat` do A→B (discover then activate). Inconsistent.
3. `.mcp.json` (Windows) lacks `obsidian-dev-wiki` reference repo (present only in `.mcp.macos.json`)
4. `.gitignore` un-ignores `.mcp.macos.json` but still ignores `.mcp.linux.json` and `.mcp.windows.json`
5. `workflows/create_pr/core.py`: `if not pr_result` → `if pr_result is None` change
6. `vulture_whitelist.py`: possibly stale entries from removed code

**Decisions**:
- #1: ✅ **Auto-resolved by rebase** — main commit `5c0fc740` already removed the override
- #2: **Accept (A)** — discover-then-activate (A→B) for prod (`.sh` and `.bat`); activate-then-discover (B→A) for `_local` variants (project `.venv` is the tool env). User confirmed via /discuss. Action: revert `claude.sh` to A→B; flip both `_local` to B→A; `claude.bat` already correct.
- #3: **Skip** — Mac-only intentional; user confirmed via /discuss
- #4: **Accept** — un-ignore `.mcp.linux.json` and `.mcp.windows.json` to avoid the same trap; user confirmed via /discuss
- #5: ✅ **Auto-resolved by rebase** — main commit `9711469c` superseded
- #6: **Defer** to step 8 (vulture/lint-imports check)

**Rebase**: 6 commits replayed onto `origin/main` cleanly. One test fix needed (`tests/icoder/ui/test_app.py` — main's PR #940 added a test referencing the old `workspace` server name; updated to `mcp-workspace`). All 3738 unit tests pass; mypy/pylint clean. Force-pushed as `70712a49`.

**Changes** (this round):
- `claude.sh`: reverted to discover-then-activate (A→B); dropped `PRE_ACTIVATION_VENV` capture
- `claude_local.sh`: flipped to activate-then-discover (B→A); removed external-env branch
- `claude_local.bat`: flipped to activate-then-discover (B→A); removed `:discover_from_path`/`:tool_env_found` labels
- `.gitignore`: un-ignored `.mcp.linux.json` and `.mcp.windows.json`

**Status**: Committed as `ee362031` and pushed. Plus `70712a49` from rebase (mcp-workspace test alignment).

## Round 2 — 2026-05-03

**Findings**:
1. `claude.bat` parity with reordered scripts — confirmed intentional (no change needed)
2. `claude.sh` self-hosting fallback could use explanatory comment
3. `claude_local.sh` Step 2 comment could clarify PATH-lookup edge case

**Decisions**:
- #1: **Skip** — already-resolved acknowledgement, not a finding
- #2: **Skip** — cosmetic; code is now structurally cleaner (true `else` branch); SE principle "don't change working code for cosmetic reasons"
- #3: **Skip** — speculative ("if .venv install is broken AND another mcp-coder on PATH AND editable check doesn't exit"); per SE principle "if a change only matters when someone makes a future mistake, skip it"

**Changes** (this round): zero — review terminates

## Final Status

**Architecture checks (step 8)**:
- `run_vulture_check`: clean (no unused code reported)
- `run_lint_imports_check`: 23/23 contracts kept, 0 broken

**Commits produced this review**:
- `70712a49` — `test(icoder): align tool-name assertion with mcp-workspace rename` (rebase fix)
- `ee362031` — `fix(launcher): align venv activation order; un-ignore platform mcp configs` (round 1 changes)

**Result**: No critical issues. Two rounds of review; round 2 produced zero accepted findings (all cosmetic/speculative). Branch is rebased on top of `origin/main` and ready for PR review / merge.

## Scope (inferred from commits)

- `feat(mac)`: macOS launcher (`claude.sh`, `claude_local.sh`, `icoder_local.bat` parity), `tools/reinstall_local.sh`, `.mcp.macos.json`
- `fix(mcp)`: rename MCP servers to avoid reserved names (`workspace` → `mcp-workspace`, `tools-py` → `mcp-tools-py`)
- `fix(launcher)`: activate `.venv` before tool discovery; align `_local` variants with prod
- `test(verify)`: tighten and trim mcp parser tests
- Removal: `branch_info_service` and Textual `branch_info_bar` widget plus their tests
- Reference: add `obsidian-dev-wiki` reference repo

