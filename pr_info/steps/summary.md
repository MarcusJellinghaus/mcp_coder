# PR-health: detect and fix merge conflicts (status-71/72/73/74)

GitHub issue: #1212 (part of PR-health epic #1188)

## Goal

`status-10:pr-created` is currently display-only. Add detection of merge
conflicts on those PRs, and a mechanical (no-LLM) fix dispatched to Jenkins,
escalating to a human only when the rebase cannot resolve a real conflict.

## Architecture / design summary

**Four-label state machine**, not three — split by pickup-vs-busy because
`WORKFLOW_MAPPING` dispatch only fires for `bot_pickup`-category labels, and a
single label can't carry both that category and a `bot_busy` stale timeout:

| Label | Category | Role |
|---|---|---|
| `status-71:merge-conflict` | `bot_pickup` | Detected; coordinator dispatches to Jenkins |
| `status-72:fixing-merge-conflict` | `bot_busy` (15 min stale timeout) | Jenkins job running the rebase |
| `status-73:merge-conflict-failed` | `human_action` | Crash watchdog landing label only |
| `status-74:pr-merge-conflict` | `human_action` | Real conflict — rebase couldn't resolve it |

**Two dispatchers, both already existing in this codebase, no third pattern
introduced:**

- *Detection* lives in the long-lived **VSCodeClaude coordinator**
  (`process_eligible_issues()` in `session_launch.py`), spliced in between the
  initial eligible-issues fetch and the `is_status_eligible_for_session()`
  filter — i.e. it runs on the pre-filter `status-10` subset directly, not
  through the per-repo managers built for session-launch purposes. Detection
  has no local git checkout available, so it talks to GitHub purely through
  managers built from a `repo_url`.
- *Execution* (the mechanical rebase) is dispatched to **Jenkins**, exactly
  like every other `bot_pickup` → `bot_busy` workflow, via a new
  `WORKFLOW_MAPPING` entry and a new `fix-conflict` CLI verb. It runs inside
  the Jenkins job's own ephemeral checkout, so it uses `PullRequestManager`
  the normal, `project_dir`-based way.
- `status-73`/`status-74` need **no new dispatch code at all** — both are
  `human_action` and already picked up by the existing VSCodeClaude
  session-launch mechanism, configured with
  `vscodeclaude.commands: ["/check_branch_status"]` and
  `requires_branch: true` (same pattern as `status-07:code-review`).

**Conflict verdict**: only `mergeable_state == "dirty"` counts as a real merge
conflict for this check. Other states (`behind`, `blocked`, `unstable`,
`clean`, `has_hooks`, `draft`) are in scope for CI/review-comment sibling
issues (#1213/#1214), not this one. `"unknown"` is GitHub's
not-yet-computed placeholder — never treated as a verdict; detection skips it
this poll, and the post-rebase poll (5s × 6, 30s cap) waits for it to settle
before leaving the label untouched if it never does.

**No new shared abstraction for the "dirty"/"unknown" string checks.** The
same two one-line comparisons appear once in the detection step and once in
the fix workflow. That's too small and too stable to be worth a shared
module — inline comments document the intent in both places instead.

**`PullRequestManager` construction without a checkout.** Its public
`__init__` only accepts `project_dir` and asserts it is not `None` — unlike
`IssueManager`/`IssueBranchManager`, which accept `repo_url` directly. The
detection step (no checkout) needs a small private helper in
`session_launch.py` that builds the manager by calling
`BaseGitHubManager.__init__` directly on a bare instance with `repo_url=`,
mirroring the existing bypass already used in `workflow_utils/label_transitions.py`
for `IssueBranchManager`. The Jenkins-side execution code has a real
checkout, so it just calls `PullRequestManager(project_dir)` normally — no
bypass needed there.

**`fix_conflict/core.py` is deliberately smaller than `create_pr/core.py` /
`implement/core.py`.** Those carry `run_guarded`, `GuardOutcome`,
failure-category classification and comment-posting because they call an
LLM and need to classify LLM failures for a human. `fix_conflict` calls no
LLM: the mechanical rebase (`_attempt_rebase_and_push`, reused unchanged) is
the only external action, and the issue assigns crash recovery to a shell
watchdog line in the Jenkins template, not to Python. So `core.py` is one
straight-line function with a single `try/except` around the whole body.

**CLI verb is required, not optional.** An existing test enforces that every
`WORKFLOW_MAPPING` workflow has a matching CLI subcommand, so `fix-conflict`
needs full wiring through `cli/commands/fix_conflict.py`, `cli/parsers.py`,
`cli/main.py`, `cli/command_catalog.py` — even though its only caller is the
Jenkins shell template. Its parser takes only `--project-dir`: no
`--llm-method`/`--mcp-config`/`--settings`, since there is no LLM call.

## Files created

- `src/mcp_coder/workflows/fix_conflict/__init__.py`
- `src/mcp_coder/workflows/fix_conflict/core.py`
- `src/mcp_coder/cli/commands/fix_conflict.py`
- `tests/workflows/fix_conflict/__init__.py`
- `tests/workflows/fix_conflict/test_core.py`
- `tests/cli/commands/test_fix_conflict.py`

## Files modified

- `src/mcp_coder/config/labels.json` — add `status-71`..`status-74`
- `tests/workflows/vscodeclaude/test_types.py` — bump `human_action` label count
- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` — `WORKFLOW_MAPPING` entry
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — new templates + `WORKFLOW_TEMPLATES` entry
- `tests/cli/commands/coordinator/test_command_templates.py` — new template constants assertion
- `src/mcp_coder/cli/parsers.py` — `add_fix_conflict_parser`
- `src/mcp_coder/cli/main.py` — import + dispatch for `fix-conflict`
- `src/mcp_coder/cli/command_catalog.py` — description + category entry
- `tests/cli/test_parsers.py` — parser registration test
- `tests/cli/commands/test_help.py` — command count/list
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` — merge-conflict detection splice
- `tests/workflows/vscodeclaude/test_session_launch_process_issues.py` — detection tests
- `src/mcp_coder/workflow_utils/label_transitions.py` — drop the
  `project_dir is None` guard in `update_workflow_label` (the detection
  step's `issue_manager` is repo_url-mode; `get_labels_config_path(None)`
  already supports this)
- `tests/workflow_utils/test_label_transitions.py` — repo_url-mode coverage

## Implementation steps

1. [step_1.md](step_1.md) — Add `status-71`..`status-74` labels to `labels.json`
2. [step_2.md](step_2.md) — `workflows/fix_conflict/core.py`: rebase + poll + label transition
3. [step_3.md](step_3.md) — `fix-conflict` CLI verb wiring
4. [step_4.md](step_4.md) — Coordinator dispatch wiring (`WORKFLOW_MAPPING` + templates)
5. [step_5.md](step_5.md) — VSCodeClaude merge-conflict detection (`session_launch.py`)

Each step is one commit: tests first, then the implementation that makes
them pass, then formatters/pylint/pytest/mypy all green.
