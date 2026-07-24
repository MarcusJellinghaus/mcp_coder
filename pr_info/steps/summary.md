# Summary — Wire automated review into coordinator & create-pr (Issue #1073)

## Goal

Make the per-repo `auto_review_plan` / `auto_review_implementation` flags **consumable**.
Everything ships **flag-off by default → merging is a no-op ("Off == today")**. An operator
later setting `auto_review_*=true` in a `[coordinator.repos.<name>]` section is what turns
automation on; that flag-flip (not this merge) is governed by the separate model-judgment
quality gate from the epic (#1063).

#1072 (merged) already provides everything this issue *consumes*: the `status-14/14i/14f*`
and `status-17/17i/17f*` labels, the `auto_review_*` config `FieldDef`s, the review workflows,
and the `review-plan` / `review-implementation` CLI verbs. #1073 is the **wiring/consumer** PR.

Two independent concerns ride in this PR (flag them separately in the PR description):
- **(A) Wiring** — the gated success transitions, coordinator dispatch, and create-pr assignee-add.
- **(B) Doc-correctness bug fix** — `config.md` uses the wrong field name `executor_test_path`
  in 15 places; the real schema field is `executor_job_path`. Following config.md today yields
  a config the verifier rejects. Renamed here alongside the two new flag rows.

## Architectural / design changes

### 1. New `utils`-level config primitive (`utils/repo_config.py`)
The success-transition gate lives in `create_plan` / `implement` (the **workflows** layer). Per
`.importlinter` `layered_architecture`, `cli` sits *above* `workflows`, so these workflows
**cannot** reuse `cli/utils.py:resolve_issue_interaction_flags` (upward import → contract break).
A new `utils`-level primitive `get_repo_flag(project_dir, key)` maps a project's git remote →
`[coordinator.repos.*]` section → typed bool flag. It is built on:
- `find_repo_section_by_url` + `get_config_values` (same-layer `utils.user_config`), and
- `get_repository_identifier` (from `mcp_workspace_git`, one layer **below** `utils` — downward, legal).

A dedicated module (not folded into `user_config.py`) keeps `user_config.py` a pure schema
reader, free of the `mcp_workspace_git` dependency `get_repository_identifier` pulls in.

**KISS deviation from issue Decisions (accepted):** the issue also asked to refactor
`resolve_issue_interaction_flags` to *delegate* to this primitive. We **skip** that — it is a
working function in the correct layer with passing tests, and delegation only de-duplicates a
~6-line lookup. Not refactoring it means less diff, no cli-resolver test churn, and lower risk.
`get_repo_flag` stands alone; `resolve_issue_interaction_flags` is left untouched.

### 2. Config-gated success transitions (net-new behavior this issue owns)
`create_plan` hardcodes `to_label_id="plan_review"` and `implement` hardcodes
`to_label_id="code_review"`. Both are gated on the repo flag:
- flag **on** → `plan_review_bot` / `code_review_bot` (the `status-14` / `status-17` bot-pickup labels)
- flag **off** → `plan_review` / `code_review` (unchanged — reproduces today's behavior exactly)

The bot `internal_id`s are already registered by #1072, so `update_workflow_label` resolves them.

### 3. Data-driven coordinator dispatch (KISS deviation from issue Decisions — accepted)
The issue framed dispatch as "add a new branch in the `coordinator/core.py` selector chain —
which runs **twice** (Windows + Linux)" plus a dedicated behavioral guard test to catch a
workflow present in `WORKFLOW_MAPPING` but missing its selector branch (which would silently
misroute to `else: create-pr` on Jenkins).

We remove that whole failure mode structurally by replacing the two mirrored `if/elif/else`
ladders with a lookup table `WORKFLOW_TEMPLATES: dict[str, tuple[linux_tpl, windows_tpl]]`.
Dispatch becomes: look up templates by workflow name, pick the OS variant, `.format(...)`.
An unknown workflow now raises `KeyError` at dispatch instead of misrouting.
- Works because `str.format()` **silently ignores extra kwargs** — create-plan uses only
  `{issue_number}`, the others only `{branch_name}`, and `branch_name` is always bound before
  dispatch (`"main"` for the create-plan strategy). We pass all three uniformly.
- Adding a future workflow becomes a **one-line dict entry**, not four edits across two OS arms.
- The behavioral guard test is still added (cheap, still passes) — now belt-and-suspenders.

Delivered in two commits: a **pure refactor** (existing 3 workflows → dict, no behavior change,
guarded by existing tests) then the **review-workflow addition** on top (safe-refactoring order).

### 4. Four explicit Jenkins templates (simplification *rejected* on purpose)
The two review templates are near-identical, but the existing `CREATE_PLAN` / `IMPLEMENT` /
`CREATE_PR` templates are also ~80% identical and are each spelled out in full. To match the
established convention (lowest surprise, best maintainability) we add **four explicit constants**
(Linux + Windows for review-plan and review-implementation) rather than inventing a
parameterized-template pattern for just this pair.

Each new template mirrors `IMPLEMENT_COMMAND_TEMPLATE` (`git checkout {branch_name}` →
`mcp-coder ... review-plan|review-implementation ...`) and carries a silent-death watchdog with
**literal** label names and a **load-bearing `--from-status` guard** (makes the watchdog a no-op
when the review workflow already emitted a terminal label; it only fires on in-progress death):
- review-plan: `set-status status-14f:plan-review-failed --from-status status-14i:plan-reviewing`
- review-implementation: `set-status status-17f:code-review-failed --from-status status-17i:code-reviewing`

### 5. Routing-table data additions
- `WORKFLOW_MAPPING` (`workflow_constants.py`): two entries, `branch_strategy="from_issue"`:
  - `status-14:plan-review-bot` → `review-plan` → next `status-14i:plan-reviewing`
  - `status-17:code-review-bot` → `review-implementation` → next `status-17i:code-reviewing`
- `PRIORITY_ORDER` (`command_templates.py`): closest-to-done first, each review step just below
  the stage it unblocks: `08 → 17 → 05 → 14 → 02`.

### 6. create-pr assignee-add (auto-path only, best-effort)
After a **successful** PR creation, if `auto_review_implementation` is true for the repo
(re-read via `get_repo_flag`), call
`PullRequestManager(project_dir).add_assignees(pr_number, get_authenticated_username())`.
Best-effort by construction upstream (`add_assignees` is decorated to return `{}` on GitHub API
failure, never raises; GitHub silently drops non-assignable logins). Wrap in a light try/except
for non-API exceptions, log a warning; **never** fail the workflow or flip a label.
Auto-path-only so manually created PRs don't spam the user.

### 7. Verification-only (no code / data change)
vscodeclaude behavior is already correct from #1072: the `14f-*` / `17f-*` labels carry
`/check_branch_status`, and the `14/17/14i/17i` bot labels launch no session. `verify` already
covers the two flags. Nothing to change.

## Out of scope / intentionally not done
- No refactor of `resolve_issue_interaction_flags` (see §1).
- No `PRIORITY_ORDER ⊇ WORKFLOW_MAPPING` sync test (sort-only, soft degradation; the behavioral
  guard covers the loud misroute failure).
- No `/implementation_approve` change (never reached on the auto path).
- No mcp-workspace pin bump (floating pin already carries `add_assignees`); no shim change
  (`PullRequestManager` + `get_authenticated_username` already re-exported).

## Files created / modified

### Created
- `src/mcp_coder/utils/repo_config.py` — `get_repo_flag` primitive.
- `tests/utils/test_repo_config.py` — unit tests for `get_repo_flag`.

### Modified — source
- `src/mcp_coder/workflows/create_plan/core.py` — gate `to_label_id` (`plan_review` / `plan_review_bot`).
- `src/mcp_coder/workflows/implement/core.py` — gate `to_label_id` (`code_review` / `code_review_bot`).
- `src/mcp_coder/cli/commands/coordinator/command_templates.py` — 4 review templates,
  `WORKFLOW_TEMPLATES` dict, updated `PRIORITY_ORDER`.
- `src/mcp_coder/cli/commands/coordinator/core.py` — data-driven dispatch; fix stale
  `executor_test_path` docstring (`:377`).
- `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` — 2 `WORKFLOW_MAPPING` entries.
- `src/mcp_coder/cli/commands/coordinator/__init__.py` — export new templates + `WORKFLOW_TEMPLATES`.
- `src/mcp_coder/workflows/create_pr/core.py` — best-effort auto-path assignee-add.

### Modified — tests
- `tests/workflows/implement/test_core_workflow.py` — flag-off (`code_review`) + flag-on
  (`code_review_bot`) cases.
- `tests/workflows/create_plan/` (create-plan gate coverage) — flag-off / flag-on.
- `tests/cli/commands/coordinator/test_command_templates.py` — 4 new templates + watchdog lines +
  `WORKFLOW_TEMPLATES` coverage.
- `tests/cli/commands/coordinator/test_core.py` — behavioral silent-fallthrough guard test.
- `tests/workflows/create_pr/` — auto-path assignee-add tests.

### Modified — docs
- `docs/configuration/config.md` — add `auto_review_plan` / `auto_review_implementation` rows;
  rename `executor_test_path` → `executor_job_path` (15 places, incl. the `:781` error message).

## Step list (one commit each)
1. `utils/repo_config.py` + `get_repo_flag` (TDD).
2. create-plan success-transition gate.
3. implement success-transition gate.
4. Refactor coordinator dispatch to data-driven `WORKFLOW_TEMPLATES` (pure refactor, no behavior change).
5. Add review workflows: 4 templates + `WORKFLOW_MAPPING` + `PRIORITY_ORDER` + guard/watchdog tests.
6. create-pr auto-path assignee-add (best-effort).
7. Docs — `config.md` two flags + `executor_test_path` rename + `core.py:377` docstring.
