# Implementation Review Log — Issue #684

Rename `from-github` → `install-from-github` across all layers.

## Round 1 — 2026-04-01
**Findings**:
- Stale comment in `src/mcp_coder/workflows/vscodeclaude/workspace.py:562` still references `from_github` instead of `install_from_github`
- No remaining old references in functional code
- No bugs introduced by the rename
- All quality checks pass (pylint, mypy, pytest — one pre-existing flaky test failure unrelated to this branch)

**Decisions**:
- Accept: stale comment — in-scope for a rename issue, trivial fix
- Skip: pre-existing test failure — not related to this branch

**Changes**: Updated comment in workspace.py:562 from `from_github` to `install_from_github`
**Status**: Committed as `0bcb91b`

## Round 2 — 2026-04-01
**Findings**:
- No remaining old references in any source, test, or config files
- One informal comment in test file (`test_workspace_startup_script_github.py:115`) uses shorthand `from-github` — not a config key or identifier
- All quality checks pass (pylint, mypy, pytest)

**Decisions**:
- Skip: informal test comment — readable shorthand, not an identifier reference

**Changes**: None
**Status**: No changes needed

## Final Status
- **Rounds**: 2 (1 with code changes, 1 clean)
- **Commits produced**: 1 (`0bcb91b` — stale comment fix)
- **Remaining issues**: None
- **Rename completeness**: All `from-github`/`from_github` identifiers consistently renamed to `install-from-github`/`install_from_github` across config, CLI, source, and tests
- **Quality checks**: All passing (pylint, mypy, pytest)

