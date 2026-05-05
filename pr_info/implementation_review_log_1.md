# Implementation Review Log #1 — Issue #949

**Branch:** `949-user-config-full-mcp-coder-cleanup-via-mcp-coder-utils-user-app-data`
**Started:** 2026-05-05
**Scope:** Adopt `mcp_coder_utils.user_app_data.get_user_app_data_dir` at every per-user data directory site in `mcp_coder`; reduce `get_config_file_path()` to a one-liner; drop phantom `~/.config/mcp-coder/config.toml` fallback in `tools/*.py`; sweep docs to a single `~/.mcp_coder/` path.

---

## Round 1 — 2026-05-05

**Findings**:
1. Unused `import platform` in `src/mcp_coder/workflows/vscodeclaude/sessions.py:8` — spec assumed it was still needed for `VSCODE_PROCESS_NAMES` but verification shows that constant is a static set with no platform-module call. Vulture skips stdlib name-imports, so the project tools didn't catch it.
2. `docs/configuration/config.md:9` Quick Reference table row still shows split Linux/macOS vs Windows path presentation — content is correct after the spec-aligned sweep, just stylistically legacy.
3. Whitespace/reformat noise bundled into commit `5cf9f3a` (tools MLflow scripts).
4. Mlflow doc collapse confirmed correct — informational.
5. Plan files (`pr_info/`) in branch — repo convention.
6. Branch is BEHIND `origin/main` per `check_branch_status` — needs rebase before PR open, no code change.

**Decisions**:
1. **Accept** — directly tied to this PR's platform-branch removal in the same file; leaves dead code if not removed; principle: "Boy Scout Rule" + Python guideline against unused imports.
2. **Skip** — content is correct, spec didn't mandate collapsing the table row, change would be cosmetic-only.
3. **Skip** — already committed, harmless auto-formatter side-effect.
4. **Skip** — already correct, no action needed.
5. **Skip** — repo convention to keep plan files on the branch.
6. **Note for final status** — recorded for `## Final Status`, will be reported in completion message; no fix in this round.

**Changes**: Removed `import platform` line in `src/mcp_coder/workflows/vscodeclaude/sessions.py`. All checks pass (pylint 10.00/10, mypy --strict clean, ruff clean, lint-imports 23/0, fast unit pytest 3756 passed).

**Status**: committed as `f0a46e4` — `vscodeclaude: drop dead import platform from sessions.py`

## Round 2 — 2026-05-05

**Findings**:
1. `src/mcp_coder/workflows/vscodeclaude/sessions.py:15` uses absolute import `from mcp_coder.utils.user_app_data import get_user_app_data_dir`. Sibling files modified in the same PR — `src/mcp_coder/llm/storage/session_storage.py:14` and `src/mcp_coder/llm/storage/session_finder.py:15` — use 3-dot relative imports. Step 3 plan's prose says "Match existing relative-import style" while its literal code example shows absolute (self-contradictory plan).

**Decisions**:
1. **Accept** — for in-PR consistency with the two sibling-purpose files. Trivial one-line edit. Plan's prose intent was clearly relative.

**Changes**: Switched shim import in `src/mcp_coder/workflows/vscodeclaude/sessions.py` from absolute to 3-dot relative; isort merged import groups (now consistent with `session_storage.py` and `session_finder.py`). All checks pass (pylint, mypy, ruff, lint-imports 23/0; pytest passes per-directory).

**Status**: committed as `7cd276d` — `vscodeclaude: switch sessions.py to relative shim import for in-PR consistency`

## Round 3 — 2026-05-05

**Findings**: None — implementation is clean.

**Decisions**: N/A.

**Changes**: None.

**Status**: loop terminated (zero code changes this round).

---

## Final Status

**Rounds completed**: 3 (rounds 1 and 2 produced commits; round 3 was clean and terminated the loop).

**Commits produced by review**:
- `f0a46e4` — `vscodeclaude: drop dead import platform from sessions.py`
- `7cd276d` — `vscodeclaude: switch sessions.py to relative shim import for in-PR consistency`

**Supervisor checks** (run by supervisor in step 8):
- `run_vulture_check` (min_confidence=70): clean — no output.
- `run_lint_imports_check`: 23 contracts kept, 0 broken (incl. `MCP Coder Utils Isolation`).

**Acceptance criteria** (issue #949 + summary): all ✓ — every bullet met.

**Quality checks** (final, all via `mcp__mcp-tools-py__*`):
- `run_pylint_check`: pass.
- `run_mypy_check`: pass.
- `run_ruff_check`: pass.
- `run_lint_imports_check`: pass (23/0).
- `run_vulture_check` (conf 70): pass.
- `run_pytest_check` fast unit: pass per-directory; full-suite hits a known pre-existing pytest internal error in `tests/workflows/create_pr/test_workflow.py` (unmodified vs `main`).

**Outstanding (non-code)**: branch was reported BEHIND `origin/main` by `check_branch_status` in round 1 — needs rebase before opening a PR.

**Verdict**: implementation is correct and complete; PR ready to merge from a code-review standpoint pending rebase onto current `main`.
