# Implementation Summary — PR-health: detect and fix failing CI (status-81/82/83/84)

GitHub issue: #1213 (part of PR-health epic #1188; mirrors the merged sibling #1212).

## Goal

When a `status-10:pr-created` PR's CI is red (and the branch isn't already escalated
for a merge conflict this poll), escalate it to `status-81:failing-ci`. A new
`fix-ci` Jenkins-dispatched workflow reuses the existing CI auto-fix loop
(`check_and_fix_ci`) to try to fix it, succeeding back to `status-10` or
escalating to a human on exhaustion / LLM failure (`status-84`) or on a crash
(`status-83`).

## Architectural / design changes

- **Detection lives in the existing VSCodeClaude coordinator poll**, not a new
  poller: `session_launch.py`'s `process_eligible_issues()` gets a second
  per-issue check, `_check_ci()`, parallel to the existing `_check_merge_conflict()`.
  Conflict detection keeps priority — `_check_merge_conflict()` changes from
  returning nothing to returning `bool` (`escalated`), and `_check_ci()` only
  runs when that returns `False`. This is the only behavioural change to
  already-shipped #1212 code.
- **No local checkout for detection.** `CIResultsManager(repo_url=...)` is
  constructed directly (it takes `repo_url` natively, unlike
  `PullRequestManager`, which needs the `__new__`-bypass helper
  `_build_pr_manager`). Built once per repo, next to the already-hoisted
  `issue_manager`/`branch_manager`, and passed into `_check_ci()` — not
  rebuilt per issue.
- **The fix loop is 100% reused, not reinvented.** `workflows/fix_ci/core.py`
  is a thin wrapper around `workflow_steps/ci.py::check_and_fix_ci` — the same
  function `implement` and `status-06f-ci` already call. No new CI-fixing
  logic is written.
- **Failure reporting follows the established `run_guarded` /
  `handle_workflow_failure` pattern** (`workflow_utils/failure_handling.py`),
  already used by `implement`/`create_pr`/`create_plan`/`review`. Unlike
  `implement`'s multi-label failure taxonomy (`FAILURE_LABELS`/
  `CATEGORY_DISPLAY` dicts covering ~8 reasons → multiple labels), `fix_ci`
  has exactly 3 deliberate failure reasons that all collapse to the **same**
  label (`status-84:pr-ci-failed`). So `fix_ci/core.py` uses one small local
  `_fail()` helper (category label is a constant; only the comment's
  `Category:` text varies) instead of a reusable dict-based taxonomy module —
  that generality isn't needed by a single call site with one label.
- **Crash net reuses `run_guarded()` as-is**, with its default comment
  formatting (no custom `build_comment` closure) — `fix_ci` has no running
  "progress" state to render into the comment, unlike `implement`.
- **Dispatch is pure config**, not new code: one `WORKFLOW_MAPPING` entry +
  one `WORKFLOW_TEMPLATES` entry (Linux/Windows shell templates), following
  the exact same data-driven dispatch `coordinator/core.py` already uses for
  every other status label. No Jenkins-client changes.
- **Retrofit of `fix_conflict/core.py` (in scope here):** wraps its existing
  body in `run_guarded()` so a crash now also posts a comment, matching every
  other `*/core.py` workflow. Its handled outcomes (dirty / clean / unknown)
  and existing shell watchdog line are unchanged — only the *unhandled-crash*
  path gains reporting.

## New labels (`config/labels.json`)

| Label | internal_id | category | Notes |
|---|---|---|---|
| `status-81:failing-ci` | `failing_ci` | `bot_pickup` | Set by `_check_ci()` |
| `status-82:fixing-ci` | `fixing_ci` | `bot_busy` | `stale_timeout_minutes: 120` |
| `status-83:ci-fix-failed` | `ci_fix_failed` | `human_action`, `failure` | Crash watchdog (`run_guarded` net + shell fallback) |
| `status-84:pr-ci-failed` | `pr_ci_failed` | `human_action`, `failure` | Deliberate failure (exhausted / LLM timeout / MCP unavailable) |

## Files created

- `src/mcp_coder/workflows/fix_ci/__init__.py`
- `src/mcp_coder/workflows/fix_ci/core.py`
- `src/mcp_coder/cli/commands/fix_ci.py`
- `tests/workflows/fix_ci/__init__.py`
- `tests/workflows/fix_ci/test_core.py`
- `tests/cli/commands/test_fix_ci.py`

## Files modified

- `src/mcp_coder/config/labels.json` — 4 new labels
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — `_check_merge_conflict()` returns `bool`; new `_check_ci()`; wiring
- `src/mcp_coder/cli/parsers.py` — `add_fix_ci_parser`
- `src/mcp_coder/cli/main.py` — import, parser registration, dispatch
- `src/mcp_coder/cli/command_catalog.py` — description + category entry
- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` — `WORKFLOW_MAPPING` entry
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — `FIX_CI_COMMAND_TEMPLATE`/`FIX_CI_COMMAND_WINDOWS` + `WORKFLOW_TEMPLATES` entry
- `src/mcp_coder/cli/commands/coordinator/__init__.py` — export the two new template constants
- `src/mcp_coder/workflows/fix_conflict/core.py` — `run_guarded()` retrofit
- `tests/cli/commands/test_define_labels.py` — label count 41 → 45
- `tests/cli/commands/test_define_labels_label_changes.py` — new-label count 40 → 44
- `tests/cli/commands/test_help.py` — `fix-ci` added to `expected_commands`
- `tests/cli/test_parsers.py` — `TestFixCiParser`
- `tests/cli/commands/coordinator/test_command_templates.py` — `fix-ci` template assertions
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` — CI-detection tests + conflict-priority test
- `tests/workflows/fix_conflict/test_core.py` — guard-net tests

## Implementation steps

1. [step_1.md](./step_1.md) — Add the 4 labels
2. [step_2.md](./step_2.md) — CI detection in the VSCodeClaude coordinator poll
3. [step_3.md](./step_3.md) — `fix_ci` workflow module (the Jenkins-side fix loop)
4. [step_4.md](./step_4.md) — `fix-ci` CLI verb
5. [step_5.md](./step_5.md) — Coordinator dispatch wiring
6. [step_6.md](./step_6.md) — Retrofit `fix_conflict/core.py` with `run_guarded()`
