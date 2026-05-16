# Implementation Review Log — Run 1

**Branch:** 969-chore-cancel-ecosystem-wide-migration-to-uv-sync-post-mortem
**Scope of change:** Add CI job `vscodeclaude-template-install` to `.github/workflows/ci.yml` that exercises the install sequence emitted by `src/mcp_coder/workflows/vscodeclaude/templates.py` (VENV_SECTION_*) + `workspace.py:_build_github_install_section`. Mirrors `uv venv` → `uv sync --extra dev` → `uv pip install -e . --no-deps` → GitHub overrides from `[tool.mcp-coder.install-from-github]`.
**Related issue:** #969 (cancellation of uv sync migration — keeps Approach A as the canonical install path).
**Diff:** 71 added lines in `.github/workflows/ci.yml` only.

## Round 1 — 2026-05-16

**Findings:**
- (Critical) None.
- (Accept) `ci.yml` inline Python heredoc — add a comment explaining the deliberate POSIX-vs-batch quoting divergence from `workspace.py:_build_github_install_section`, to prevent a future reader from trying to "DRY-merge" the two renderers.
- (Skip) Trim of 6-line header comment — each line is load-bearing context (#969, what it mirrors, why it's independent). Reviewer rated optional. Keep as-is.
- (Skip) Deeper smoke check that verifies overrides actually applied (e.g. assert sibling import path contains git artifact) — speculative; `set -euo pipefail` + `bash github_install.sh` already fails loudly on any install error.
- (Skip) Hard-fail when `[tool.mcp-coder.install-from-github]` is empty — would couple CI to a template-optional setting. Out of scope.
- (Skip) Various verified non-issues: independence claim (no `needs:`, runs in parallel), action versions match `test`/`architecture` (`checkout@v6`, `setup-uv@v7`, `setup-python@v6`, py3.11, ubuntu-latest), heredoc redirect syntax valid, omitted env vars (`MCP_CODER_PROJECT_DIR`, `MCP_TIMEOUT`, second PATH export) are not install-relevant.

**Decisions:** Accept the divergence-comment finding (1 change). Skip everything else per reasoning above.

**Changes:** `.github/workflows/ci.yml` — three-line Python comment added in the heredoc above the first `out.append(...)`, explaining intentional POSIX-vs-batch renderer divergence and naming the shared seam (`get_github_install_config`).

**Status:** Pending commit.

## Round 2 — 2026-05-16

**Findings:** None (Critical, Accept, or new Skip).
**Decisions:** Confirmed Round 1 commit `bcdc65cc` applied the accepted comment cleanly at `.github/workflows/ci.yml:181-183`; all Round 1 skip decisions still hold.
**Changes:** None.
**Status:** Loop exit condition met (zero code changes this round).

## Final Status

- **Rounds run:** 2.
- **Code changes produced:** 1 commit — `bcdc65cc chore(ci): note POSIX renderer divergence` (3-line comment in `.github/workflows/ci.yml`).
- **`run_vulture_check`:** clean (no output).
- **`run_lint_imports_check`:** PASSED — 23 contracts kept, 0 broken.
- **Outcome:** All findings triaged; one accepted finding implemented and verified; loop exited on Round 2 with zero new findings. No architectural or import-contract violations introduced.
