# Step 5 — Add review workflows: templates + routing tables + guard test

**Read `pr_info/steps/summary.md` first** (§4 four explicit templates, §5 routing-table additions).
Depends on Step 4 (`WORKFLOW_TEMPLATES` exists). This wires `review-plan` / `review-implementation`
into coordinator dispatch. Flags are off by default, so this changes no live behavior until an
operator sets `auto_review_*=true`. TDD: write template/watchdog/guard tests first.

## WHERE
- Modify `src/mcp_coder/cli/commands/coordinator/command_templates.py`:
  - Add `REVIEW_PLAN_COMMAND_TEMPLATE`, `REVIEW_PLAN_COMMAND_WINDOWS`,
    `REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE`, `REVIEW_IMPLEMENTATION_COMMAND_WINDOWS`.
  - Add the 2 new entries to `WORKFLOW_TEMPLATES`.
  - Replace `PRIORITY_ORDER` with the 5-item list.
- Modify `src/mcp_coder/cli/commands/coordinator/workflow_constants.py` — 2 `WORKFLOW_MAPPING` entries.
- Modify `src/mcp_coder/cli/commands/coordinator/__init__.py` — export the 4 new templates.
- Modify `tests/cli/commands/coordinator/test_command_templates.py` — extend template lists +
  watchdog assertions.
- Modify `tests/cli/commands/coordinator/test_core.py` — behavioral silent-fallthrough guard test.

## WHAT — templates
Each mirrors `IMPLEMENT_COMMAND_TEMPLATE` / `IMPLEMENT_COMMAND_WINDOWS` exactly, swapping only the
verb and the watchdog labels. Linux verb line: `mcp-coder --log-level {log_level} review-plan
--project-dir /workspace/repo --mcp-config .mcp.json` (and `review-implementation`). No positional
args and no `--update-issue-labels` flag (config-driven, like implement).

Watchdog lines (literal names; `--from-status` guard is load-bearing — do NOT drop it):
- review-plan Linux: `mcp-coder gh-tool set-status status-14f:plan-review-failed --from-status status-14i:plan-reviewing --project-dir /workspace/repo --force || true`
- review-plan Windows: same, `--project-dir %WORKSPACE%\repo --force` (no `|| true`).
- review-implementation Linux: `... set-status status-17f:code-review-failed --from-status status-17i:code-reviewing --project-dir /workspace/repo --force || true`
- review-implementation Windows: `... --project-dir %WORKSPACE%\repo --force`.

## WHAT — routing data
```python
# workflow_constants.py — add to WORKFLOW_MAPPING
"status-14:plan-review-bot": {
    "workflow": "review-plan",
    "branch_strategy": "from_issue",
    "next_label": "status-14i:plan-reviewing",
},
"status-17:code-review-bot": {
    "workflow": "review-implementation",
    "branch_strategy": "from_issue",
    "next_label": "status-17i:code-reviewing",
},

# command_templates.py
PRIORITY_ORDER = [
    "status-08:ready-pr",           # create-pr (closest to done)
    "status-17:code-review-bot",    # review-implementation
    "status-05:plan-ready",         # implement
    "status-14:plan-review-bot",    # review-plan
    "status-02:awaiting-planning",  # create-plan (furthest from done)
]

# WORKFLOW_TEMPLATES — add
"review-plan": (REVIEW_PLAN_COMMAND_TEMPLATE, REVIEW_PLAN_COMMAND_WINDOWS),
"review-implementation": (REVIEW_IMPLEMENTATION_COMMAND_TEMPLATE,
                          REVIEW_IMPLEMENTATION_COMMAND_WINDOWS),
```

## DATA
- 4 template `str` constants; 2 `WORKFLOW_MAPPING` keys; 5-item `PRIORITY_ORDER`; 2 dict entries.

## TESTS
1. **Template tests** (`test_command_templates.py`): extend the parametrized Linux/Windows lists to
   include the 4 new templates; assert each carries its exact watchdog `set-status ... --from-status`
   line and captures RC (`RC=$?` / `set RC=%ERRORLEVEL%`). Assert Linux templates contain
   `review-plan` / `review-implementation` verbs and `git checkout {branch_name}` formats.
2. **Behavioral silent-fallthrough guard** (`test_core.py`): for every distinct `workflow` in
   `WORKFLOW_MAPPING`, build a fake `IssueData` carrying that workflow's pickup label, mock the
   Jenkins client / branch resolution, and drive `dispatch_workflow` on **both** `executor_os`
   arms (`"windows"` and `"linux"`); assert the `COMMAND` param passed to `start_job` contains that
   workflow's verb (`create-plan` / `implement` / `create-pr` / `review-plan` /
   `review-implementation`). A workflow missing from `WORKFLOW_TEMPLATES` raises `KeyError` and
   fails the test loudly.

## Commit
One commit: templates + routing + exports + tests. Run pylint, pytest (`-n auto` unit exclusion),
mypy, `lint-imports`, `vulture`.
