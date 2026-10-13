# Summary — Send a build LABEL to the Jenkins executor job

GitHub issue: #1206

## Goal

The Jenkins executor job accepts an optional `LABEL` parameter that sets the
build's display name in the Jenkins UI (e.g. `mcp_coder - #123 - implement`).
`executor-job.groovy` already reads `params.LABEL` — no AutoRunner-side work
is needed. On the coordinator side, neither `dispatch_workflow()` nor
`execute_coordinator_test()` currently send it, so builds triggered by the
coordinator are indistinguishable in the Jenkins UI beyond build number and
timestamp.

## Architectural / design changes

No new modules, classes, or abstractions. This is a parameter-passing change
confined to two existing functions in the `coordinator` package:

- `dispatch_workflow()` gains one new required parameter, `repo_name: str`,
  supplied by its only caller (`execute_coordinator_run()`, which already
  holds it as a loop variable). The function builds a `LABEL` string from
  `repo_name`, the issue number, and the resolved workflow verb, and adds it
  to the Jenkins job `params` dict it already builds.
- The `branch_strategy == "from_issue"` branch parses `repo_config["repo_url"]`
  via `RepoIdentifier` into local variables `repo_owner, repo_name`, which
  would otherwise shadow the new `repo_name` parameter for the rest of the
  function. That local variable is renamed to `issue_repo_name` (and its one
  downstream use) so the parameter stays valid everywhere, including when
  `LABEL` is built in the `params` dict.
- `execute_coordinator_test()` (a manual smoke-test path with no issue or
  workflow) builds its own `LABEL` from `args.repo_name` and `args.branch_name`
  plus the literal `"test"`. It does not call `dispatch_workflow()`.
- `format_job_output()` and all other CLI output are unchanged — `LABEL` is
  a Jenkins job parameter only, invisible to the CLI's own output.

## Files modified

No files are created; everything below is a modification of existing files.

- `src/mcp_coder/cli/commands/coordinator/core.py` — `dispatch_workflow()`:
  new `repo_name` parameter, `LABEL` entry in `params`.
- `src/mcp_coder/cli/commands/coordinator/commands.py` —
  `execute_coordinator_run()`: pass `repo_name=repo_name` to
  `dispatch_workflow(...)`; `execute_coordinator_test()`: new `LABEL` entry
  in `params`.
- `tests/cli/commands/coordinator/test_core.py` — add `repo_name=...` to all
  `dispatch_workflow(...)` test calls; assert `LABEL` in the workflow-verb
  guard test.
- `tests/cli/commands/coordinator/test_commands.py` — assert the
  `repo_name` kwarg reaches `dispatch_workflow` from
  `execute_coordinator_run()`; assert `LABEL` in the expected params dict
  for `execute_coordinator_test()`.

## Steps

1. [step_1.md](./step_1.md) — `dispatch_workflow()`: add `repo_name` param
   and `LABEL`, update its caller and its tests.
2. [step_2.md](./step_2.md) — `execute_coordinator_test()`: add `LABEL`,
   update its test.

Each step is one commit: tests + implementation + passing checks.
