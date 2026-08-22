# Summary — Issue #1112: a blocked agent can only spin or fabricate

## Problem

`process_single_task` treats an empty git status as `no_changes` and retries up to
`MAX_NO_CHANGE_RETRIES` (3). That conflates *"nothing needed doing"* with *"I could not
verify the work, so I refused to claim it"*. Both get the same response — re-send the
prompt with `RETRY_REMINDER`, which (like `prompts.md:115`) states unconditionally that
ticking the checkbox **IS** the deliverable.

A blocked agent therefore has exactly two moves: **spin** (burn three attempts, end on
`status-06f-nochange`) or **fabricate** (tick a box for a check it never saw pass). Both
were observed on issue #1107; the second is worse, because the tracker then records a
green quality gate on a commit whose own message says the checks fail.

## Goal

Give the agent a third exit — *"I am blocked, and here is why"* — that is terminal,
non-retrying, and surfaces the reason to a human.

---

## Architectural / design changes

### 1. New file-marker channel: `pr_info/.blocked.txt`

Mirrors the existing `pr_info/.commit_message.txt` convention the prompt already teaches,
so the agent needs no new concept. The agent writes one line; the workflow reads it,
deletes it, and fails the run with a dedicated label.

`BLOCKED_FILE` lives in `workflow_steps/constants.py` (the workflow-agnostic middle tier)
beside `COMMIT_MESSAGE_FILE`, re-exported from `implement/constants.py`. Placing it in the
shared tier is the only preparation needed for the CI-fix loop to adopt the same channel
later — that adoption is explicitly **out of scope** here.

### 2. `tuple[bool, str]` → `TaskOutcome`

`process_single_task` / `process_task_with_retry` currently return `(success, reason)`
where `reason` is a category key into `FAILURE_LABELS`. The blocked reason needs free text
alongside that key, so the return type becomes:

```python
@dataclass(frozen=True)
class TaskOutcome:
    success: bool
    reason: str
    detail: str = ""
```

This is unavoidable rather than chosen: `detail` is consumed at **two** sites in `core.py`
— the `blocked` branch and the `timeout` / `mcp_unavailable` branches (where the marker
text must be appended to the failure message). Both live in `core.py`'s reason chain, so
the text has to travel through the return value. A `NamedTuple` would not reduce the
migration cost — the arity changes from 2 to 3 either way. The conversion is mechanical
but touches ~50 call sites across 3 source files and 5 test files, so it lands as its own
commit (Step 2) with no behaviour change.

### 3. Blocked-first ordering (the load-bearing part)

`pr_info/` has no `.gitignore` entry anywhere, `get_full_status` includes `untracked`, and
`commit_all_changes` stages everything. A `.blocked.txt` written alone would satisfy the
existing files-changed check, get committed into the branch, and the run would report
**success** — precisely inverted. Therefore:

- the marker read happens **inside** `process_single_task`, **before** the Step 6
  files-changed check (not in the `process_task_with_retry` wrapper, where the Step 9
  commit would already have staged it);
- an **empty or whitespace-only** marker still counts as blocked with a generic message —
  falling through to `no_changes` would restore the same inverted path.

### 4. The read cannot be bypassed

Three early exits sit between the LLM call and the intended read point: the empty-response
guard (a plain `return` inside the `try` body) and the two `except` paths. A marker left on
disk is not merely a lost message — `check_git_clean` refuses the next run, and
`prepare_task_tracker` hard-fails with `task_tracker_prep_failed` because it requires
exactly one changed file equal to `TASK_TRACKER.md`.

The fix keeps this to one local variable and a `finally`: the three `return`s become
assignments to `llm_error`, the marker is read in `finally`, and the branching happens once
afterwards. No helper extraction, no control-flow indirection.

**Precedence** when both a marker and a typed LLM failure are present: the LLM failure wins
the label (`llm_timeout` / `mcp_unavailable`) — the label drives what the operator does
next, and an unavailable MCP server is more actionable than the agent's downstream
complaint about it. The marker is deleted either way and its text appended to the failure
message, so the reason is never lost. For the untyped `error` paths, **blocked wins** —
`general` is exactly the uninformative label the marker exists to replace.

### 5. Commit paths that need marker cleanup

`create_pr/core.py`'s `get_branch_diff` excludes only `pr_info/steps/`, so a marker that
ever reaches a commit surfaces in the PR summary diff. Three of the four paths that stage
everything get cleanup:

| Path | Where |
|------|-------|
| Main task loop | `process_single_task` — start-of-task cleanup + the read itself |
| Final mypy block | `core.py`, immediately before its `get_full_status` |
| Finalisation | `finalisation.py`, in a `finally` on its `prompt_llm` call — after the LLM turn (so the agent's own marker is caught, not just stale ones), before the step-4 changes check, and on the early exits too (the empty-response guard at `:104-106` returns `False`) |
| CI-fix loop | **excluded — see below** |

`run_finalisation` gets **cleanup only** — no blocked channel there.

**The CI-fix loop is the fourth path, and it is deliberately excluded.**
`check_and_fix_ci` (called from `core.py` after finalisation) runs its own LLM turns and
commits at `workflow_steps/ci.py:247`, so in principle a marker written there would be
committed. It is left alone because:

- **No marker can be stale by then.** Every earlier path deletes it — `process_single_task`
  at task start and in its `finally`, the final-mypy block, and finalisation in its own
  `finally`. A blocked task returns terminally, so the CI stage is only ever reached
  after every task and finalisation succeeded. The only way a marker exists at that point
  is if the CI-fix agent writes one — and the CI Fix Prompt (`prompts.md:286`) never
  mentions `.blocked.txt`, nor does the CI-fix loop have a blocked channel (explicitly out
  of scope in the issue).
- **Cleanup there is not a one-liner.** `ci.py` sits in `workflow_steps`, whose tach
  `depends_on` (`tach.toml`) does not include `mcp_coder.workflows` — it cannot import
  `read_and_clear_blocked` from `implement/task_processing.py`. Covering it means moving
  the helper into the shared tier, which is the CI-fix adoption work the issue defers.

**Revisit condition:** when the CI-fix loop adopts the blocked channel, move
`read_and_clear_blocked` to `workflow_steps/` beside `BLOCKED_FILE` and add the cleanup
immediately before `ci.py`'s `commit_changes` — same placement rule as finalisation.

The per-task mypy path is a non-issue for the same reason it is not listed: the
`check_and_fix_mypy` call inside `process_single_task` (`task_processing.py:427`) sits
between the marker read and Step 9's `commit_changes`, but it is gated on
`RUN_MYPY_AFTER_EACH_TASK`, which is `False`.

### 6. One helper, four call sites

A single `read_and_clear_blocked(project_dir) -> str | None` serves both the read and the
three cleanups (cleanup callers ignore the return). No separate `_cleanup_blocked_file`.

### 7. Prompt pressure removed at both sources

`RETRY_REMINDER` is **replaced** wholesale, not extended — appending a blocked exit would
leave *"you MUST tick … IS the deliverable"* standing two sentences away, and an agent
under retry pressure resolves that contradiction toward the stronger imperative. The same
reasoning applies to `prompts.md:115`, which governs attempt 1 before any reminder exists:
the existing bullet is **conditioned in place**, not followed by a contradicting qualifier.

### 8. New terminal label

`status-06f-blocked:implementation-blocked` — `category: human_action`, `failure: true`,
**no retry**. Partial work stays uncommitted by design; the failure comment's diff stat
surfaces it. The next automated run will refuse at `check_git_clean` — acceptable, because
a human is already required.

Note `blocked` already exists in `labels.json` as an *ignore* label meaning "human says
don't touch". `get_matching_ignore_label` matches exactly, so there is no functional
collision, but the display name is kept distinct.

### 9. Drive-by: `finalisation.py` double prefix (a live bug, not a typo)

`f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}"` resolves to `pr_info/pr_info/.commit_message.txt`
because `COMMIT_MESSAGE_FILE` already carries the prefix. The placeholder **is** consumed
(`prompts.md:196`), so the finalisation agent is handed a path that does not exist, the
read at `finalisation.py:121` never finds the file, and **every finalisation silently falls
through to Level 2 LLM message generation**.

---

## Data structures

| Name | Where | Value / shape |
|------|-------|---------------|
| `BLOCKED_FILE` | `workflow_steps/constants.py` | `"pr_info/.blocked.txt"` |
| `BLOCKED_REASON_MAX_CHARS` | `implement/task_processing.py` | `500` |
| `BLOCKED_REASON_FALLBACK` | `implement/task_processing.py` | generic message for an empty marker |
| `TaskOutcome` | `implement/task_processing.py` | `success: bool`, `reason: str`, `detail: str = ""` |
| `read_and_clear_blocked` | `implement/task_processing.py` | `(project_dir: Path) -> str \| None` |
| reason `"blocked"` | `FAILURE_LABELS` | → `"implementation_blocked"` |
| reason `"blocked"` | `CATEGORY_DISPLAY` | → `"Blocked"` |

`process_single_task` reasons after this change:
`completed` \| `no_tasks` \| `no_changes` \| `blocked` \| `error` \| `timeout` \| `mcp_unavailable`.
`process_task_with_retry` adds `no_changes_after_retries`.

---

## Files created / modified

### Created

- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_8.md` (planning artifacts)
- `tests/workflows/implement/test_core_failure_routing.py` (created in **Step 2**, which
  moves the four existing failure-routing tests out of `test_core_workflow.py`; Step 5's
  blocked-routing tests join them there). `test_core_workflow.py` is at 747 lines and is
  not in `.large-files-allowlist`, while the CI `file-size` job caps at 750 — Step 2's
  `TaskOutcome` import plus black's rewrap of its line 114 alone would breach it.

No new source modules — every source change lands in an existing file.

### Modified — source

| File | Change |
|------|--------|
| `src/mcp_coder/workflow_steps/constants.py` | `BLOCKED_FILE` |
| `src/mcp_coder/workflows/implement/constants.py` | re-export `BLOCKED_FILE` |
| `src/mcp_coder/workflows/implement/task_processing.py` | `TaskOutcome`, `read_and_clear_blocked`, blocked detection, `RETRY_REMINDER` replacement |
| `src/mcp_coder/workflows/implement/core.py` | `TaskOutcome` unpack, `blocked` routing, detail on timeout/mcp messages, final-mypy cleanup |
| `src/mcp_coder/workflows/implement/failure_reporting.py` | `FAILURE_LABELS`, `CATEGORY_DISPLAY`, `append_detail` |
| `src/mcp_coder/workflows/implement/finalisation.py` | marker cleanup, `commit_message_path` double-prefix fix |
| `src/mcp_coder/prompts/prompts.md` | conditioned rule at `:115` + blocked bullet |
| `src/mcp_coder/config/labels.json` | `implementation_blocked` label |

### Modified — tests

`tests/workflows/implement/test_task_processing.py`, `test_core.py`, `test_core_workflow.py`,
`test_failure_reporting.py`, `test_finalisation.py`,
`tests/integration/test_execution_dir_integration.py`,
`tests/config/test_label_config.py`, `tests/cli/commands/test_define_labels.py`,
`tests/cli/commands/test_define_labels_label_changes.py`,
`tests/workflows/vscodeclaude/test_types.py`

The last two are label **count** assertions derived from the bundled `labels.json`
(`35` → `36` at `test_define_labels_label_changes.py:308,311`; `26` → `27` at
`test_types.py:309`, since the new label is `category: human_action`). They are not listed
in the issue's "five places to touch" but fail immediately without the bump.

### Modified — docs

`docs/processes-prompts/development-process.md`,
`docs/processes-prompts/github_Issue_Workflow_Matrix.html`,
`docs/architecture/architecture.md`

---

## Steps

| # | Step | Scope |
|---|------|-------|
| 1 | `BLOCKED_FILE` + `read_and_clear_blocked()` | src + tests, unused so far |
| 2 | `TaskOutcome` mechanical conversion | src + all test call sites; no behaviour change; splits the failure-routing tests out of `test_core_workflow.py` to stay under the file-size gate |
| 3 | Blocked detection in `process_single_task` | the core fix |
| 4 | `implementation_blocked` label definition | `labels.json` + 4 test files (name list, `ERROR_STATUS_IDS`, and three count assertions: `36` → `37`, `35` → `36` twice, `26` → `27`) |
| 5 | `core.py` routing + final-mypy cleanup | label mapping, ERROR log, detail append |
| 6 | `RETRY_REMINDER` + `prompts.md` | remove the fabricate pressure |
| 7 | `finalisation.py` cleanup + double-prefix fix | third commit path + live bug |
| 8 | Docs tables, HTML matrix, architecture note | docs only |

Ordering constraints: Step 2 before 3 (`TaskOutcome` must exist); Step 4 before 5 (the
label id must exist before `FAILURE_LABELS` maps to it); Steps 6–8 are independent of each
other but assume 1–5.

Steps 3 and 5 are split because Step 4 has to sit between them, so Step 3 lands a `blocked`
reason that `core.py` does not yet handle. `core.py:155-191` has no `else`, so for that one
commit a `blocked` outcome is counted as a completed task and the loop runs again. The
checks stay green either way; Step 5 closes it. No test pins the intermediate behaviour.

---

## Invariants the tests must pin

1. A marker **plus** changed files → `blocked`, never success. *(The inverted-path trap.)*
2. An **empty** marker → `blocked`, never `no_changes`. *(Same trap.)*
3. Marker + `LLMTimeoutError` → reason `timeout`, marker deleted, text in the message.
4. A stale marker is removed at task start.
5. `blocked` never retries.
6. The marker is deleted before the finalisation commit path stages anything — including
   when finalisation exits early on an empty LLM response.

## Out of scope

Project-specific pytest guidance in the workflow prompt; the workflow re-running the checks
itself; getting the project's `CLAUDE.md` to the agent; a blocked channel for the CI-fix
loop **and marker cleanup on its commit path — exclusion justified in §5**; the
`status-03f-*` / `status-09f-*` docs omissions (other lanes).

## Deployment note

Every driven repo needs `define-labels` re-run after this change.
