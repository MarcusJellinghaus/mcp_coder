# Issue #1085 — `mcp-coder rebase`: git in Python, LLM only for content work; CLI progress output

## Problem

`mcp-coder rebase` (from #1082) has two defects:

1. **Silent CLI** — progress is logged at INFO, but the CLI default level is OUTPUT (25),
   so users see nothing until an error.
2. **The rebase can never succeed** — the "Automated Rebase" prompt instructs shell git
   commands, but non-interactive LLM sessions have **no shell** (the Claude CLI provider
   hardcodes `--tools ToolSearch`; the langchain provider only exposes MCP tools). Every
   run that needs a rebase burns a full LLM session and ends `REBASE_OUTCOME: aborted`.

## Design change (architecture summary)

**Role inversion.** Today one LLM session owns the whole rebase and self-reports an
outcome marker that Python cross-checks. After this change, **Python executes every git
operation and every check deterministically**; the LLM is a content editor only, invoked
for exactly two jobs, both via MCP file tools with context inlined by Python:

- resolving non-`pr_info/` merge conflicts (Python inlines base/ours/theirs via
  `git show :1:/:2:/:3:<file>` into the prompt), and
- fixing regressions found by the deterministic baseline-vs-verification comparison.

**Python is the judge.** Success is decided purely from repo state (no conflict markers,
clean tree, HEAD moved — existing `_rebase_success_shape`) plus a set-difference of
failure keys (verification − baseline). The `REBASE_OUTCOME:`/`REBASE_REASON:` marker
contract and its parse machinery (`_parse_outcome_marker`, `_evaluate_pre_push`,
`_OUTCOME_RE`, `_REASON_RE`) are **removed**.

**Baseline concept.** Before rebasing, Python runs pytest/pylint/mypy (project defaults,
no marker filter, library-default timeouts) through the shared `mcp_coder.mcp_tools_py`
wrapper and reduces results to a flat `set` of failure keys:

- `("pytest", node_id)` for failing outcomes (`failed`/`error`/unrecognized —
  not `skipped`/`xfailed`, so new self-skipping tests from base are not phantom
  regressions), plus collection errors
- `("pylint", path, message_id, message)` — line numbers never enter the key
- `("mypy", file, code, message)` — line numbers never enter the key

After the rebase the same checks run again; **regression = verification − baseline** (one
set difference). Pre-existing failures never block. A check that fails to *run* (pytest
crash/timeout/`error_info`, pylint target error, mypy exception) raises `CheckRunError`:
at baseline time → exit 2, no git mutation; at verification time → reset + exit 1.

**Conflict loop (Python-driven, per `/rebase` strategy table).** Conflicted files via
`git diff --name-only --diff-filter=U`; binary conflicts (`git diff --numstat` shows `-`)
abort. `pr_info/` files auto-resolve with `git checkout --theirs` (fallback `git rm` for
delete/modify — "keep feature version" = stays deleted), no LLM. Other files go to the
LLM. Python verifies no conflict markers remain, stages with **plain `git add -A`**
(delete/modify + adjacent-edit safety; relies on the existing convention that target
projects gitignore `.mcp-coder/`), and continues with `git -c core.editor=true rebase
--continue` (never blocks on an editor). Abort rules from `/rebase`: binary conflict,
markers remain, same file conflicts 3+ times, unexpected error.

**Regression-fix loop** mirrors implement's `check_and_fix_mypy`: Python feeds concrete
failure text into a fix prompt, the LLM edits, Python runs `run_format_code`, stages
`git add -A`, commits `fix: resolve regressions from rebase onto origin/<base>` (new
commit per attempt, no amend), re-runs checks, re-compares. Max **2** attempts plus an
identical-failure-text stall guard (one remembered string, one `==`). Still failing →
`git reset --hard <pre-rebase>`, exit 1.

**LLM session:** one session for the whole run, resumed via `session_id` across conflict
stops and fix attempts; timeout `LLM_INACTIVITY_TIMEOUT_SECONDS` (600s inactivity) from
`workflow_steps/constants.py` (local `_SESSION_TIMEOUT` removed); every exchange
persisted via `store_session` under `.mcp-coder/rebase_sessions`. Fast path: a
conflict-free, regression-free rebase makes **no LLM call at all**.

**Prompts:** the "Automated Rebase" section is replaced by two sections — "Rebase
Conflict Resolution" and "Rebase Regression Fix" (placeholder pattern like "Mypy Fix
Prompt"). Both reference the read-only `mcp__mcp-workspace__git` tool for reads, never
shell, and carry no outcome-marker or push instructions.

**Permissions:** all ten `Bash(...)` entries in `REBASE_LLM_PERMISSIONS` are pruned
(including read-only ones — the Bash tool does not exist in automated sessions, so they
are dead grants). MCP file/check tools and read-only `mcp__mcp-workspace__git` stay; no
reference-project tools (least privilege). The EPIC #1038/#1054 TODO stays.

**CLI output:** `logger.log(OUTPUT, ...)` at start, at every major step (baseline,
rebase, conflict resolution, verification, fix attempts, push) and at the end
(result/reason). Details stay at INFO/DEBUG.

**Unchanged:** pre-flight guards, base-branch guard, `pr_info/`-on-base guard, no-op
short-circuit, `--force-with-lease` push with restore-on-rejection, `finally` abort
safety net, exit-code contract (0 success/no-op, 1 needs-human, 2 error/push-rejected).

## What stays deliberately simple (KISS)

- Everything lands in the existing `workflows/rebase.py` — no new src modules (file
  stays under the 750-line limit; the marker machinery being deleted frees ~120 lines).
- Check results are plain `set[tuple[str, ...]]`; comparison is one set difference.
- Infrastructure failures are one local exception type (`CheckRunError`).
- The stall guard is a single remembered string compared with `==` (the max-2 cap makes
  `check_and_fix_mypy`'s history-list machinery pointless here).
- The `mcp_coder.mcp_tools_py` wrappers stay dumb pass-throughs returning library types;
  all rebase-specific interpretation lives in `rebase.py`.
- `_run_git`'s signature is untouched; `core.editor=true` is passed as `-c` git args.

## Files created / modified

| File | Change | Step |
|---|---|---|
| `src/mcp_coder/mcp_tools_py.py` | add `run_pytest_check`, `run_pylint_check` | 1 |
| `tests/test_mcp_tools_py.py` | **new** — unit tests for the wrappers | 1 |
| `src/mcp_coder/workflows/rebase.py` | failure keys + `CheckRunError` + `_run_all_checks` | 2 |
| `tests/workflows/rebase/test_checks.py` | **new** — pure unit tests for keys/comparison | 2 |
| `src/mcp_coder/workflows/rebase.py` | git conflict helpers | 3 |
| `tests/workflows/rebase/test_git_helpers.py` | extend with conflict-helper tests | 3 |
| `src/mcp_coder/prompts/prompts.md` | add 2 new prompt sections (old removed in step 6) | 4 |
| `src/mcp_coder/workflows/rebase_permissions.py` | prune all `Bash(...)` grants | 4 |
| `tests/workflows/rebase/test_prompt.py` | rework for new sections | 4 |
| `tests/workflows/rebase/test_rebase_permissions.py` | assert no Bash grants | 4 |
| `src/mcp_coder/workflows/rebase.py` | LLM session helper + prompt builders | 5 |
| `tests/workflows/rebase/test_llm_steps.py` | **new** — tests for session/prompt helpers | 5 |
| `src/mcp_coder/workflows/rebase.py` | orchestrator rewrite, delete marker machinery, OUTPUT logging | 6 |
| `src/mcp_coder/prompts/prompts.md` | delete old "Automated Rebase" section | 6 |
| `tests/workflows/rebase/test_workflow.py` | rework orchestrator tests | 6 |
| `tests/workflows/rebase/test_decision.py` | **delete** (covers removed functions only) | 6 |

No new source modules, no new constants files, no CLI/parser changes (the `rebase`
command wiring in `cli/` is untouched — only the workflow behind it changes).

## Step order rationale

Steps 1–3 build deterministic, independently testable foundations (wrappers → failure
keys → git helpers). Step 4 adds the new prompts/permissions *without* removing the old
prompt section (its consumer `_run_rebase_session` still exists until step 6, so every
intermediate commit stays consistent). Step 5 adds the LLM-facing helpers. Step 6 rewires
the orchestrator and deletes the old machinery atomically with its prompt section and
tests. Each step is exactly one commit with pylint/pytest/mypy green.

## References

- Issue #1085 (this plan), #1082 (original implementation)
- Behavioral reference: `.claude/skills/rebase/SKILL.md`
- Pattern reference: `check_and_fix_mypy` in `src/mcp_coder/workflows/implement/task_processing.py`
