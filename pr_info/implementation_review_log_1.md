# Implementation Review Log — Issue #965

Branch: `965-vscodeclaude-launcher-scripts-missing-mcp-config-strict-mcp-config-flags-blocks-macos-mcp-tools`
Started: 2026-05-14
Commit under review: `7e12a49 fix(vscodeclaude): pass --mcp-config and --strict-mcp-config to claude`

Files changed (vs `main`):
- `src/mcp_coder/workflows/vscodeclaude/templates.py`
- `src/mcp_coder/workflows/vscodeclaude/workspace.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_cli.py`
- `tests/workflows/vscodeclaude/test_workspace_startup_script.py`


## Round 1 — 2026-05-14

**Findings** (from engineer subagent `/implementation_review`):
- No critical issues.
- S1: `workspace.py:551` — Windows branch lacks a `mcp_config_path.exists()` validation that POSIX branch performs at L666-672.
- S2: `test_workspace_startup_script.py:1056-1058` — multi-command assertion could be tightened to require two occurrences of `--mcp-config <expected>`.
- S3: `templates.py:236, 362` — strict-mcp-config on Windows diverges from reference `claude.sh:112-114` (which only emits override when override file exists, and `claude.bat` never emits these flags).
- S4: `workspace.py:551` — minor redundancy when `is_windows` is true (computed even though it equals `.mcp.json`).
- S5: Filenames are relative; could add a code comment near templates explaining the cwd assumption.

**Decisions**:
- S1: **Skip** — pre-existing scope; #965 is about adding flags, not expanding validation. (Software-eng principles: "Pre-existing issues are out of scope".)
- S2: **Skip** — speculative; the 9-cell `TestMcpConfigFlagsFullMatrix` already independently verifies each flow.
- S3: **Skip** — intentional. Issue #965 Decisions table: "Scope: Update both POSIX and Windows templates for symmetry".
- S4: **Skip** — cosmetic; don't change working code for cosmetic reasons.
- S5: **Skip** — existing `AUTOMATED_*_POSIX` templates already use the same relative-path convention without comment; new code matches that convention. Adding a one-off comment would be asymmetric.

**Changes**: None.

**Status**: No changes needed this round.


## Final Status

- **Rounds**: 1 (zero code changes accepted).
- **Vulture**: clean (no output).
- **Lint-imports**: PASSED — 23/23 contracts kept.
- **Verdict**: Implementation correctly addresses every requirement and decision in issue #965. No code changes needed from this review.
