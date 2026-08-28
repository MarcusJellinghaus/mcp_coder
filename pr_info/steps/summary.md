# Remove `--execution-dir`: collapse Claude's working directory onto `project_dir`

Implements issue **#1132**. Completes the fix started in #1113 (shipped as PR #1137, commit
`26748dc`), building on #977 (`.mcp.json` anchored to `project_dir`) and #981 (`--settings`).

## Goal

`--execution-dir` was introduced (#185) to separate "where the Claude subprocess runs" from
"where the project lives", because MCP config discovery keyed off the subprocess cwd. #977,
#981 and #1113 each removed one part of that job; nothing is left. This change deletes the
flag and every `execution_dir` identifier in `src/`, leaving exactly one directory concept:
`project_dir`.

## Architectural / design changes

### 1. One directory concept instead of two

Before, three layers each carried a second directory that always held the same value:

```
CLI flag --execution-dir ─► resolve_execution_dir() ─► workflow(execution_dir=…)
                                                    ─► prompt_llm(execution_dir=…) ─► subprocess cwd
```

After, the value the subprocess needs is derived from the one directory that was always in
scope anyway:

```
--project-dir ─► resolve_project_dir() ─► resolve_claude_cwd() ─► workflow(project_dir=…)
                                                               ─► prompt_llm(project_dir=…) ─► subprocess cwd
```

Every leaf call site already held `project_dir`; three of them even contained the provably
dead fallback `cwd = str(execution_dir) if execution_dir else str(project_dir)`
(`task_processing.py`, `review/reviewer.py`, `workflow_steps/ci.py`). Removing the parameter
deletes that dead branch rather than replacing it.

### 2. `resolve_execution_dir` → `resolve_claude_cwd(project_dir) -> Path`

The resolver is **replaced, not deleted**. Two of its jobs outlive the flag:

- it calls `report_context_root`, which has no other production caller — deleting the resolver
  would silently remove #1113's per-run context reporting from all nine commands;
- it `.resolve()`s the path, which matters for `commit.py`, the one command that builds
  `project_dir` without resolving it.

`report_context_root`'s two parameters collapse into one: the directory Claude runs in and the
directory used for the "is this file inside the project?" test are now the same directory.

Every command adopts the same one-line idiom, so there is a single thing to remember:

```python
project_dir = resolve_claude_cwd(project_dir)
```

In eight of nine commands this is provably idempotent (`resolve_project_dir` already resolves);
in `commit.py` it supplies the resolve that the issue calls out by name.

### 3. `prompt_llm`: a path plus an explicit switch, not one overloaded parameter

This is the subtle part of the change. At `prompt_llm`, today's `project_dir` is **not** a
location — it is an opt-in *prompt-loading* switch feeding `load_prompts` and
`--append-system-prompt`. Headless workflows pass `execution_dir` and deliberately no
`project_dir`, which is exactly why they inject no system or project prompt.

Reading "cwd becomes `project_dir`" literally would switch prompt injection on for every
headless `implement` / `create-plan` / `review` run. Splitting the path from the boolean is
what keeps behaviour identical:

```python
def prompt_llm(
    question: str,
    *,
    project_dir: str | Path,          # required — the subprocess cwd
    inject_prompts: bool = False,     # was: the side effect of passing project_dir
    provider: str | None = None,
    ...
) -> LLMResponseDict: ...
```

- **Required**, because the old optional parameter's `None` fallback to the process working
  directory *is* the #1113 bug.
- **Keyword-only** after `question`, because inserting a required positional at position 2
  would silently reinterpret `prompt_llm("q", "claude")` as `project_dir="claude"`. Every
  existing call site already passes by keyword, so nothing else changes.
- `str | Path`, normalised internally, matching `resolve_mcp_config_path` /
  `resolve_claude_settings_path` and avoiding ~20 mechanical conversions at call sites.
- No compatibility shim: `prompt_llm` is public API (`mcp_coder/__init__.py`), so this is a
  loud, intentional breaking change in a package whose only consumer is this repo.

`inject_prompts` is **mapped per call site, never defaulted blindly**:

| Call site | Value | Why |
|---|---|---|
| `verify.py` LLM check | `True` | passes `project_dir` today, deliberately (comment at `:491-492`) |
| iCoder `RealLLMService` | `True` | passes `project_dir` today |
| `prompt.py` (3 sites) | `args.add_system_prompts` | stays conditional — not hard-coded |
| `verify.py` MCP edit smoke test | `False` (default) | passes no `project_dir` today |
| `icoder/env_setup.py` tool probe | `False` (default) | passes no `project_dir` today |
| all workflow sites | `False` (default) | headless runs inject nothing, as before |

### 4. Provider layer: the honest name at each layer

- **Claude** keeps `cwd` on `ask_claude_code_cli` / `..._stream` — already correct.
- **Copilot** loses its second parameter: `execution_dir` collapses into the existing `cwd`,
  which `prompt_llm` fed with the identical value.
- **Langchain** loses it outright. It runs in-process and has no subprocess to place; the
  parameter was already annotated `# pylint: disable=unused-argument`.

### 5. Error handling stops mislabelling

Five commands wrap their whole body in `except ValueError: "Invalid execution directory"`.
Once `resolve_claude_cwd` cannot raise, those handlers catch only `resolve_project_dir`
failures — which they already mislabelled. They are **relabelled**, not deleted, so the exit
path for a bad `--project-dir` is unchanged (`rebase.py` keeps its exit code 2). Three narrower
blocks become genuinely dead and are deleted (`commit.py`, `prompt.py`, `icoder.py`).

### 6. `CIFixConfig.cwd` deleted

Once the `execution_dir`-or-`project_dir` fallback collapses, `cwd: str` is a pure duplicate of
the dataclass's existing `project_dir: Path`. Its three uses become `str(config.project_dir)`.

### Behaviour deliberately preserved

- Headless `implement` / `create-plan` / `review` still inject no system or project prompt.
- `mcp-coder verify`'s LLM check still sends the merged system + project prompt; its MCP edit
  smoke test still sends none. iCoder still injects both.
- Each run still reports the Claude working directory and the project instructions in effect,
  and still warns when none lies inside `project_dir`.

### The one behaviour lost, and staying lost

A project with no `.mcp.json` of its own could previously pick up a workspace-level one via
Claude's own cwd discovery. It fires only when mcp-coder resolves no config from any of its
four sources; since #977 made every other path project-anchored, this is a leftover, not a
feature. If it ever needs restoring, add a fifth fallback inside `resolve_mcp_config_path` —
do not reintroduce cwd plumbing.

## Step order (and why it is forced)

Steps 1 and 2 are independent. Steps 3 and 4 cannot be swapped:

- **Not swappable.** Several workflow sites pass `execution_dir=str(execution_dir) if
  execution_dir else None` — a `None` cwd, i.e. the #1113 bug. So the flag can only be removed
  (step 3) while the workflow parameter still receives a real path; the parameter can only be
  deleted (step 4b) once `prompt_llm` derives cwd from a required `project_dir`.
- **Step 4 splits into two green commits.** 4a rewrites `prompt_llm` / `prompt_llm_stream` and
  retargets only the *direct* callers to pass `project_dir=` plus the `inject_prompts` mapping.
  The 23 workflow `execution_dir` parameters stay in place and stay **used** — each one still
  supplies the value that is now passed as `project_dir` — so no parameter goes unused and
  pylint, mypy and pytest all stay green. 4b then deletes those parameters, the dead
  `cwd = str(execution_dir) if … else str(project_dir)` fallbacks and `CIFixConfig.cwd`.

  The direct callers retargeted in 4a: `cli/commands/prompt.py` (3 sites),
  `cli/commands/verify.py:97-105` and `:506`, `icoder/services/llm_service.py:114`,
  `icoder/env_setup.py:112`, `workflow_utils/commit_operations.py:166`,
  `workflows/implement/task_processing.py:221`, `:439`, `:543`, `workflows/rebase.py:319`,
  `workflows/implement/finalisation.py`, `workflows/implement/task_tracker_prep.py:78`,
  `workflows/create_plan/core.py`, `workflows/create_pr/core.py`, `workflows/review/core.py:425`,
  `workflows/review/reviewer.py`, `workflow_steps/ci.py`.

Step 3 leaves one intentional, temporary artefact: commands pass the same `project_dir` value
twice (once as itself, once as the workflow's `execution_dir` argument). Step 4b deletes the
duplicate. This is what makes the commits green.

| Step | Scope | Size |
|---|---|---|
| [1](./step_1.md) | Langchain: delete `execution_dir` from 6 functions | small |
| [2](./step_2.md) | Copilot: collapse `execution_dir` into `cwd` | small |
| [3](./step_3.md) | CLI flag removal + `resolve_claude_cwd` + test/marker cleanup | medium |
| [4a](./step_4.md) | `prompt_llm` collapse + retarget the direct callers | medium |
| [4b](./step_4.md) | delete `execution_dir` from the 23 workflow signatures + `CIFixConfig.cwd` | medium |
| [5](./step_5.md) | Documentation | small |

## Files created / modified

### Created

| Path | Note |
|---|---|
| `tests/integration/test_claude_cwd_integration.py` | git-mv of `test_execution_dir_integration.py`, trimmed to 2 tests (step 3) |

### Deleted

| Path | Note |
|---|---|
| `tests/integration/test_execution_dir_integration.py` | renamed (step 3) |

### Modified — `src/` (34 files, 224 references)

| Folder / module | Files | Step |
|---|---|---|
| `src/mcp_coder/llm/providers/langchain/` | `__init__.py`, `agent.py` | 1 |
| `src/mcp_coder/llm/providers/copilot/` | `copilot_cli.py`, `copilot_cli_streaming.py` | 2 |
| `src/mcp_coder/llm/providers/claude/` | `claude_mcp_guard.py` (docstring only) | 4b |
| `src/mcp_coder/llm/` | `interface.py` | 1, 2, 4a |
| `src/mcp_coder/cli/` | `shared_args.py`, `parsers.py`, `utils.py` | 3 |
| `src/mcp_coder/cli/commands/` | `prompt.py`, `commit.py`, `implement.py`, `create_plan.py`, `create_pr.py`, `review.py`, `rebase.py`, `check_branch_status.py`, `icoder.py`, `verify.py` | 3, 4a, 4b |
| `src/mcp_coder/workflows/` | `rebase.py`, `create_plan/core.py`, `create_pr/core.py`, `implement/core.py`, `implement/finalisation.py`, `implement/task_processing.py`, `implement/task_tracker_prep.py`, `review/core.py`, `review/reviewer.py`, `review/steps.py` | 4a, 4b |
| `src/mcp_coder/workflow_steps/` | `ci.py`, `commit.py` | 4a, 4b |
| `src/mcp_coder/workflow_utils/` | `commit_operations.py` | 4a, 4b |
| `src/mcp_coder/icoder/` | `env_setup.py`, `services/llm_service.py` | 4a, 4b |
| `src/mcp_coder/` | `__init__.py` (docstring example) | 4a |

### Modified — `tests/` (37 files, ~537 references)

`tests/cli/` (`test_utils.py`, `test_utils_context_root.py`, `test_main.py`,
`test_shared_args.py`), `tests/cli/commands/` (10 files), `tests/icoder/`
(`conftest.py`, `test_cli_icoder_parser.py`), `tests/integration/` (2 files),
`tests/llm/` (`test_interface.py`, copilot + langchain provider tests),
`tests/workflows/` (8 files), `tests/workflow_steps/`, `tests/workflow_utils/`.

Roughly 470 of those references are mock keyword arguments and reduce to two mechanical rules
(see step 4); the sweep splits across 4a and 4b along the same line as the source change —
`prompt_llm` call/assertion sites in 4a, workflow-signature keywords in 4b. Per-site handling
of the ~15 flag-specific tests is enumerated in step 3.

### Modified — docs & config

`docs/cli-reference.md`, `docs/architecture/architecture.md`,
`docs/configuration/claude-code.md`, `docs/environments/environments.md`,
`docs/repository-setup/claude-code.md`, `.claude/CLAUDE.md` (step 5);
`pyproject.toml` (pytest marker, step 3).

## Acceptance criteria → step

| Criterion | Step |
|---|---|
| `mcp-coder <cmd> --execution-dir X` fails with "unrecognized argument" | 3 |
| No `execution_dir` identifier remains in `src/` | 4b |
| Subprocess `cwd` equals resolved `project_dir` for every command, from any shell cwd | 3 + 4a |
| Each run still reports Claude cwd + project instructions, and still warns | 3 |
| Headless `implement`/`create-plan`/`review` inject no prompt | 4a |
| `verify` LLM check injects prompts; its smoke test does not | 4a |
| iCoder still injects system + project prompts | 4a |
| `prompt_llm(...)` without `project_dir` raises `TypeError` | 4a |
| Suite green; `test_claude_cwd_integration.py` keeps 2 tests; marker gone | 3 |
| No documentation references `--execution-dir` | 5 |

## Quality gate (every step)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

All three must pass before the step is committed. Use MCP tools only (see `.claude/CLAUDE.md`).
