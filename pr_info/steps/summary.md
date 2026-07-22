# Summary — Automated `mcp-coder rebase` command (Issue #1066)

## Goal

Add a top-level **`mcp-coder rebase`** LLM-workflow command: rebase the current
feature branch onto its base branch, resolve conflicts + verify via a single LLM
session, and force-push with `--force-with-lease` — fully automated, no
confirmation. It is the automated counterpart of the interactive `/rebase` skill
and the dependency consumed by #1072 through a fixed three-way exit-code contract.

## Exit-code contract (public API for #1072)

| Code | Meaning | Branch state |
|------|---------|--------------|
| `0` | Success (rebased + pushed) **or** no-op (already current) | rebased & pushed, or unchanged |
| `1` | Aborted → needs-human (unresolvable conflict / regression / unregenerable lockfile / session failure) | `git rebase --abort` run; retry-safe |
| `2` | Error (bad repo/args, non-standard base, `pr_info/` on base, push/lease rejected) | restored to pre-rebase state; retry-safe |

## Architecture / design

**Python owns the deterministic shell; the LLM works inside it.** Structural
precedent is `workflows/implement/core.py` (pre-flight → protected region →
`finally` safety net around a git-mutating `prompt_llm` session). The `prompt_llm`
+ `settings_file` + inactivity-timeout call pattern follows `workflows/create_plan/core.py`.

### Python owns (in `workflows/rebase.py`)
- **Pre-flight** (fail → `2`): clean tree, not mid-rebase/merge, not on
  main/master, `origin` exists.
- **Base-branch guard** (fail → `2`): auto-detect; proceed automatically only for
  `main`/`master`; other bases require explicit `--base-branch`.
- **`pr_info/`-on-base guard** (fail → `2`).
- **No-op short-circuit**: `needs_rebase` false → `0` **without** an LLM call.
- **Single `prompt_llm` session** (one prompt, ~600s inactivity budget) using a
  dedicated least-privilege settings file.
- **Outcome → exit code** (hybrid, worst-case-wins): parse the LLM outcome marker,
  cross-check git state; git state is authoritative and neither signal is trusted
  alone.
- **The final force-push** (`git_push(force_with_lease=True)`) — see design note
  below.
- **`finally` safety net**: if still mid-rebase after the session, Python runs
  `git rebase --abort` itself.
- **No GitHub side-effects** (no labels/comments/issue lookup) — #1072 owns routing.

### LLM owns (inside the session, driven by the prompt)
Per-file-type conflict resolution (additive merge; `pr_info/` → `--theirs`;
conservative-abort on unknowns), lockfile **regeneration** (`uv lock` for this
repo's ecosystem; abort-with-reason otherwise), no-regression verification
(baseline checks captured **before** the rebase, re-run after), self-cancel with
an authored human-readable reason, and emitting the outcome marker. On any
unresolvable case it restores the original branch state and reports `aborted`.

### Key simplifications vs. a literal reading (KISS)
1. **Single module `workflows/rebase.py`**, not a multi-file package — no
   `WorkflowFailure`/label/comment machinery, because GitHub side-effects are out
   of scope.
2. **Single prompt, single `prompt_llm` call** — no session-continuation loop.
3. **Python executes the force-push** (LLM stops after rebase+verify). This makes
   lease-rejection a *direct* `git_push` return (clean `2` + restore) instead of a
   fragile inference from git state, and further narrows the least-privilege
   settings (no `push` grant for the LLM). It preserves the requirements
   "no confirmation prompt" and "Python owns lease-rejection + restore / branch
   pushed". *(This reassigns execution of the push step from LLM to Python — the
   deliberate, flagged deviation.)*
4. **No new upstream git primitives**: mid-rebase = filesystem check
   (`.git/rebase-merge` / `.git/rebase-apply`); a tiny local `_run_git`
   subprocess helper covers `rebase --abort`, `reset --hard`, and read-only
   guards. Avoids a cross-repo dependency on `mcp-workspace`.
5. **Any push failure → restore + `2`** (not only lease-rejection) — a safe
   superset that removes error-string sniffing and never leaves unpushed rebased
   commits.
6. **Git state is authoritative for the exit code**; the marker mainly carries the
   reason and blocks a push when it says `aborted`.

### Instruction sources (accepted two-file duplication)
- New least-privilege **settings JSON** under `resources/` (SKILL.md
  `allowed-tools` minus push, plus `uv lock`), bypassing the broad
  `settings.local.json` auto-detect.
- New **`## Automated Rebase` prompt** in `prompts.md` (SKILL.md minus the
  confirmation step). A drift test keeps the conflict-strategy table in sync
  between SKILL.md and the prompt.

## Folders / modules / files

### Created
- `src/mcp_coder/resources/claude/settings/rebase_settings.json` (least-privilege permissions)
- `src/mcp_coder/workflows/rebase.py` (deterministic shell + orchestrator)
- `src/mcp_coder/cli/commands/rebase.py` (`execute_rebase` + settings resolution)
- `tests/workflows/rebase/__init__.py`
- `tests/workflows/rebase/test_settings_resource.py`
- `tests/workflows/rebase/test_prompt.py`
- `tests/workflows/rebase/test_decision.py`
- `tests/workflows/rebase/test_git_helpers.py`
- `tests/workflows/rebase/test_guards.py`
- `tests/workflows/rebase/test_workflow.py`
- `tests/cli/commands/test_rebase.py`

### Modified
- `src/mcp_coder/prompts/prompts.md` (add `## Automated Rebase`)
- `src/mcp_coder/cli/command_catalog.py` (description + category)
- `src/mcp_coder/cli/parsers.py` (`add_rebase_parser`)
- `src/mcp_coder/cli/main.py` (import `execute_rebase` + route)
- `tests/cli/test_help_anti_drift.py` (include the new command, if it enumerates commands)

### Unchanged (already covers the new resource)
- `pyproject.toml` — `[tool.setuptools.package-data]` already declares
  `resources/claude/**/*`, so the settings JSON is bundled automatically.

## Reused primitives (no wrappers)
`needs_rebase(project_dir) -> (bool, reason)`, `detect_base_branch`,
`is_working_directory_clean`, `get_current_branch_name`, `get_latest_commit_sha`,
`fetch_remote`, `git_push(force_with_lease=True)` (all via `mcp_workspace_git`),
`prepare_llm_environment`, `prompt_llm`, `get_prompt`, `find_data_file`,
`resolve_claude_settings_path`, `get_branch_name_for_logging`.

## Step overview (one commit each, TDD)
1. Least-privilege settings resource + locator test.
2. `## Automated Rebase` prompt + loader test + SKILL-drift test.
3. Pure decision logic (`_parse_outcome_marker`, `_evaluate_pre_push`).
4. Low-level git helpers (`_run_git`, rebase-in-progress, abort, reset, success-shape).
5. Guards (`_preflight`, `_resolve_base_branch`, `_check_pr_info_absent_on_base`).
6. Orchestrator `run_rebase_workflow` (ties it together; mocks the LLM in tests).
7. CLI wiring (`command_catalog`, `add_rebase_parser`, `execute_rebase`, `main` route).
