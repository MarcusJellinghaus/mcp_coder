# Summary: Split `tests/workflows/vscodeclaude/test_cleanup.py` (#1320)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal

`tests/workflows/vscodeclaude/test_cleanup.py` (975 lines, allowlisted) is over the 750-line limit.
This is a **test-only split** into prefixed siblings, organized by the source function each test covers.
The source `src/mcp_coder/workflows/vscodeclaude/cleanup.py` (~258 lines) is **not** changed.

## Pure refactoring rules (from the issue — binding for every step)

- **Move, don't change.** Classes, methods, helpers move verbatim. No logic edits, renames, test deletions or merges.
- **Only allowed hand edits:** import statements, removal of the allowlist entry, and deleting section-banner comments that have nothing left under them.
- **Moves go through `mcp__mcp-tools-py__move_symbol` (dry run first)**, never by hand.
- **No Bash.** Use MCP tools only.
- **No stubs or re-exports.** Never import a `Test*` class from `test_cleanup.py`, or pytest collects it twice.

## Architectural / design changes

There are no production-code or architecture changes. The test layout changes as follows:

| Concern in `cleanup.py` | Test file |
|---|---|
| `cleanup_stale_sessions` dispatch + `delete_session_folder` basics + end-to-end scenarios | `test_cleanup.py` (keeps `TestCleanup`, `TestCompositionScenarios`) |
| `get_stale_sessions` | `test_cleanup_get_stale_sessions.py` (`TestGetStaleSessions`) |
| `.to_be_deleted` queue: lock veto + `_retry_to_be_deleted` | `test_cleanup_retry.py` (`TestSoftDeleteAndRetry`) |

Design decisions:
- **The shared helpers stay in `test_cleanup.py`.** These are `_session`, `_assessment` and `_patch_sessions_file`. The new siblings import them via
  `from tests.workflows.vscodeclaude.test_cleanup import _assessment, _patch_sessions_file, _session`.
  `move_symbol` cannot move the helpers (mcp-tools-py#255). The precedent for importing them from a sibling test module is
  `tests/llm/providers/langchain/test_langchain_agent_streaming_tool_output.py:5`.
- **No `conftest.py` changes.** All files stay in the same directory, so the fixture chain is identical.
- **The module docstring of `test_cleanup.py` is unchanged.** `test_status_display_scenario.py` is unchanged too, because its docstring reference to `test_cleanup.py` stays valid.
- **Independent of #1319.**

## Files

| Path | Action |
|---|---|
| `tests/workflows/vscodeclaude/test_cleanup.py` | modified (two classes moved out, `get_stale_sessions` import dropped) |
| `tests/workflows/vscodeclaude/test_cleanup_get_stale_sessions.py` | **created** (step 1) |
| `tests/workflows/vscodeclaude/test_cleanup_retry.py` | **created** (step 2) |
| `.large-files-allowlist` | modified (step 2: remove `tests/workflows/vscodeclaude/test_cleanup.py`) |

No other file is touched. No folders or modules are created.

## Expected counts

| Point | `test_cleanup.py` | `..._get_stale_sessions.py` | `..._retry.py` | `tests/workflows/vscodeclaude/` |
|---|---:|---:|---:|---:|
| Baseline | 29 | — | — | 680 (record actual) |
| After step 1 | 23 | 6 | — | = baseline |
| After step 2 | 14 | 6 | 9 | = baseline |

## TDD note

This is a pure move, so no new tests are written. The moved tests are the safety net. Each step proves equivalence
with `--collect-only -q` counts (no marker filter) and a passing run at the new locations.

## Steps

1. Move `TestGetStaleSessions` → `test_cleanup_get_stale_sessions.py`. Record the baseline first. (1 commit)
2. Move `TestSoftDeleteAndRetry` → `test_cleanup_retry.py`, then remove the allowlist entry. (1 commit)
