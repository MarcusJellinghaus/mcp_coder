# Step 4b — delete `execution_dir` from every workflow signature

**Context:** [summary.md](./summary.md), sections 1 and 6. Step 4 is two commits: **4a** in
[step_4a.md](./step_4a.md), **4b** here. 4a must already be committed.

Pure signature work: **no behaviour changes**, so no new tests. Delete the 23 `execution_dir`
parameters (section B), the dead `cwd = …` fallbacks (section C), `CIFixConfig.cwd` (section D)
and the duplicated arguments at the forwarding call sites (section E2). Seven of the 23 have
been unused since 4a (see step_4a.md); the rest are still forwarding.

After 4b, `grep -r execution_dir src/` returns nothing.

## WHERE — checklist

### B. The 23 signatures that carry the parameter

| File | Line(s) |
|---|---|
| `cli/commands/check_branch_status.py` | `:379` (`_run_auto_fixes`) |
| `cli/commands/verify.py` | `:73` (`_run_mcp_edit_smoke_test`) |
| `icoder/env_setup.py` | `:88` (`_probe_exposed_mcp_tools` — **rename** to `project_dir`, not delete) |
| `icoder/services/llm_service.py` | `:52` (`RealLLMService.__init__` — only the `execution_dir` parameter; `project_dir` was already made required in 4a) |
| `workflows/rebase.py` | `:304`, `:404` |
| `workflows/create_plan/core.py` | `:190`, `:438` |
| `workflows/create_pr/core.py` | `:205`, `:457` |
| `workflows/implement/core.py` | `:66` |
| `workflows/implement/finalisation.py` | `:40` |
| `workflows/implement/task_processing.py` | `:138`, `:358`, `:561` |
| `workflows/implement/task_tracker_prep.py` | `:31` |
| `workflows/review/core.py` | `:78` |
| `workflows/review/reviewer.py` | `:86`, `:173` |
| `workflows/review/steps.py` | `:64` |
| `workflow_steps/ci.py` | `:482` (`check_and_fix_ci` — positional; the two call sites in `check_branch_status.py:432, :463` just lose their last argument) |
| `workflow_steps/commit.py` | `:64` |
| `workflow_utils/commit_operations.py` | `:68` (`generate_commit_message_with_llm` — **third positional parameter**, see below) |

**Each deleted parameter takes its docstring `Args:` entry with it** — 17 lines, listed here
because section F below carries only the docstrings that have *no* parameter to delete:
`create_plan/core.py:200`, `:450`, `create_pr/core.py:214`, `:468`, `implement/core.py:77`,
`finalisation.py:49`, `task_processing.py:149`, `:370`, `:575`, `task_tracker_prep.py:40`,
`review/core.py:91`, `review/reviewer.py:112`, `:198`, `review/steps.py:90`,
`workflow_steps/ci.py:496`, `workflow_steps/commit.py:74`, `workflow_utils/commit_operations.py:77`.
(`check_branch_status.py:392` is in F; `verify.py:84` is in E2.) Nothing flags a stale entry —
ruff's `DOC` rules do not check argument lists — so only this step's final
`grep -rn "execution_dir" src/` catches a miss.

**`generate_commit_message_with_llm` is not a pure deletion.** Its signature is
`(project_dir, provider, execution_dir, mcp_config, settings_file)` (`commit_operations.py:66-70`),
so `execution_dir` sits in the *middle*: removing it shifts `mcp_config` and `settings_file` one
position left, and any caller passing them positionally would silently bind the wrong value —
the same hazard step 1 calls out for langchain. Search the project for
`generate_commit_message_with_llm(` (`cli/commands/commit.py:95`, `workflow_steps/commit.py:100-106`,
and the tests) and confirm every argument after `provider` is passed by keyword before deleting
the parameter; convert any positional caller found.

### C. Dead branches that disappear with the parameter

`task_processing.py:394`, `review/reviewer.py:132`, `:210`, `workflow_steps/ci.py:549` —
all `cwd = str(execution_dir) if execution_dir else str(project_dir)`. `resolve_claude_cwd`
never returns `None`, so the fallback was dead; the surviving half proves `project_dir` is
already in scope at every leaf.

### D. `CIFixConfig` (`workflow_steps/ci.py:52`)

Delete the `cwd: str` field (`:58`). The uses at `:131` and `:211` become
`str(config.project_dir)`; the use at `:251` is `commit_changes(..., execution_dir=config.cwd)`,
whose parameter this step deletes, so that argument is **dropped**, not rewritten (section E2).
Delete `cwd=cwd` from the constructor call (`:552-562`).

### E2. Forwarding call sites that lose an argument

Deleting a parameter in section B breaks every call that still supplies it. Command-level:

- `cli/commands/*` — drop the duplicated `project_dir` argument introduced in step 3.
- `icoder.py:202` — drop `execution_dir=`; `project_dir=` (`:208`) already present.
- `verify.py` — drop the `str(project_dir)` argument at the call site (`:476-484`) **and** the
  `execution_dir: str` parameter plus its docstring line from `_run_mcp_edit_smoke_test`
  (`:73`, `:84`). Its body needs no edit: 4a already made the `prompt_llm` call pass
  `project_dir=project_dir`, the function's own first parameter.
- `icoder/env_setup.py:197` — already passes `str(project_dir)`; only the keyword name changes.

Intra-workflow forwards, which are just as numerous and easy to miss:

| Call site | Form |
|---|---|
| `workflows/implement/core.py:128` | positional (last of five: `project_dir, provider, mcp_config, settings_file, execution_dir`) |
| `workflows/implement/core.py:156`, `:306` | positional |
| `workflows/implement/core.py:240`, `:326` | keyword `execution_dir=` |
| `workflows/create_pr/core.py:526` | positional (last of five) |
| `workflows/create_plan/core.py:613` | positional |
| `workflows/review/core.py:178`, `:232`, `:280`, `:384`, `:485` | positional |
| `workflows/implement/task_processing.py:523` | positional |
| `workflows/implement/task_processing.py:591` | keyword `execution_dir=` |
| `workflows/rebase.py:547`, `:587` | keyword `execution_dir=` |
| `workflows/review/steps.py:127` | keyword `execution_dir=` |
| `cli/commands/check_branch_status.py:432`, `:463` | positional (last argument to `check_and_fix_ci`) |

The six sites held back from 4a land here — they pass `execution_dir=` to `commit_changes`
(`workflow_steps/commit.py:64`) or `generate_commit_message_with_llm`
(`commit_operations.py:68`), so they can only change when those parameters are deleted:

| Call site | Form |
|---|---|
| `workflows/implement/core.py:280` | keyword `execution_dir=str(execution_dir) if … else None` → drop |
| `workflows/review/core.py:425` | keyword, same form → drop |
| `workflows/implement/task_processing.py:543` | keyword `execution_dir=cwd` → drop (`cwd` disappears with section C) |
| `workflow_steps/ci.py:251` | keyword `execution_dir=config.cwd` → drop (section D) |
| `workflows/implement/finalisation.py:147` | keyword, `generate_commit_message_with_llm` → drop |
| `workflow_steps/commit.py:104` | keyword, `generate_commit_message_with_llm` → drop |

The positional ones are the risk: dropping the wrong argument still type-checks in some cases.
Work from the mypy error list rather than by eye, and re-read each call after editing.

### F. Docstrings mentioning the removed concept

`llm/providers/claude/claude_mcp_guard.py:166`, `workflow_utils/commit_operations.py:21`,
`cli/commands/commit.py:98` and the `_run_auto_fixes` `Args:` entry at
`check_branch_status.py:392` — fixed here, with the parameters they mention. (The public
`prompt_llm` examples were fixed in 4a; the command-level `Args:` entries for the removed
*flag* are step 3's.)

## DATA

`LLMResponseDict` / `StreamEvent` unchanged. `CIFixConfig` loses one field.

## TDD

No new tests — behaviour is unchanged. Sweep the remaining test references with two mechanical
rules (numbered as in step_4a.md):

1. `execution_dir=<x>` in a call or mock assertion → `project_dir=<x>`; delete it outright
   where a sibling `project_dir=<same value>` already asserts it. In 4b this covers the
   **workflow-signature** keywords: the remaining `tests/workflows/**` (8 files),
   `tests/workflow_steps/`, `tests/icoder/`, and the residual assertions in
   `tests/cli/commands/**` left by step 3.
2. Leftover `execution_dir=None` attributes on `argparse.Namespace` fixtures → delete the line.
   Includes `tests/integration/test_mcp_config_integration.py:122`, which falls outside the
   `tests/cli/commands/test_*.py` glob and is listed in no other step.

Use `mcp__tools-py__run_mypy_check`'s "unexpected keyword argument" / "too many arguments" list
as the complete worklist for sections B, C, D and E2.

## Verification beyond the gate

- `grep -rn "execution_dir" src/` → no hits (acceptance criterion).
- `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])` — the mandated fast gate
  excludes this marker, but `tests/integration/test_claude_cwd_integration.py`'s two retained
  tests carry it and they are the only end-to-end pin of "subprocess `cwd` equals the resolved
  `project_dir`". If the tests skip because the Claude CLI is absent, say so explicitly rather
  than treating the skip as a pass.

## Commit

```
Delete execution_dir from the workflow signatures

With prompt_llm deriving cwd from project_dir, the execution_dir parameter
threaded through 23 signatures only forwarded a value the callee already had.
Removes it, the dead `cwd = str(execution_dir) if ...` fallbacks and
CIFixConfig.cwd. Closes the src half of #1132.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4b.md`, then implement **step 4b only**
> (4a must already be committed).
>
> Delete the `execution_dir` parameter from the 23 signatures in section B, delete the dead
> `cwd = str(execution_dir) if execution_dir else str(project_dir)` fallbacks (section C)
> and `CIFixConfig.cwd` (section D — the uses at `ci.py:131` and `:211` become
> `str(config.project_dir)`; the one at `:251` is dropped with its `commit_changes` keyword).
> Rename `_probe_exposed_mcp_tools`'s parameter to `project_dir`. (`RealLLMService.project_dir`
> was already made required in 4a — only its `execution_dir` parameter is left to delete here.)
> Fix the docstrings in section F.
>
> Update every forwarding call site in section E2 — including the six `commit_changes` /
> `generate_commit_message_with_llm` keywords held back from 4a — note which are **positional**,
> and note that `generate_commit_message_with_llm`'s `execution_dir` is a *middle* positional
> parameter, so removing it shifts `mcp_config`/`settings_file` by one for any positional
> caller: audit those call sites before deleting. Then sweep the remaining test references with
> the two mechanical rules in the step (including
> `tests/integration/test_mcp_config_integration.py:122`), using
> `mcp__tools-py__run_mypy_check` output as the worklist.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass, plus
> `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])`, and
> `grep -r execution_dir src/` must return nothing. One commit for this step.
