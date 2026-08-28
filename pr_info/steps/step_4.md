# Step 4 — `prompt_llm` takes `project_dir`; delete `execution_dir` from every workflow

**Context:** [summary.md](./summary.md), sections 1, 3 and 6.

The atomic core. Every `prompt_llm` caller breaks at once, and leaving a workflow parameter
unused would fail pylint — so this cannot be split further. It is kept mechanical by the
per-file checklist below.

After this step, `grep -r execution_dir src/` returns nothing.

## WHERE — checklist

### A. The interface (`src/mcp_coder/llm/interface.py`)

`prompt_llm` (`:72`) and `prompt_llm_stream` (`:287`).

### B. The 23 signatures that carry the parameter (pure deletion)

| File | Line(s) |
|---|---|
| `cli/commands/check_branch_status.py` | `:379` (`_run_auto_fixes`) |
| `cli/commands/verify.py` | `:73` (`_run_mcp_edit_smoke_test`) |
| `icoder/env_setup.py` | `:88` (`_probe_exposed_mcp_tools` — **rename** to `project_dir`, not delete) |
| `icoder/services/llm_service.py` | `:52` (`RealLLMService.__init__`) |
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
| `workflow_utils/commit_operations.py` | `:68` |

### C. Dead branches that disappear with the parameter

`task_processing.py:394`, `review/reviewer.py:132`, `:210`, `workflow_steps/ci.py:549` —
all `cwd = str(execution_dir) if execution_dir else str(project_dir)`. `resolve_claude_cwd`
never returns `None`, so the fallback was dead; the surviving half proves `project_dir` is
already in scope at every leaf.

### D. `CIFixConfig` (`workflow_steps/ci.py:52`)

Delete the `cwd: str` field (`:58`). Uses at `:131`, `:211`, `:251` become
`str(config.project_dir)`. Delete `cwd=cwd` from the constructor call (`:552-562`).

### E. Callers left holding one value instead of two

- `cli/commands/*` — drop the duplicated `project_dir` argument introduced in step 3.
- `icoder.py:202` — drop `execution_dir=`; `project_dir=` (`:208`) already present.
- `verify.py` — drop the `str(project_dir)` argument to `_run_mcp_edit_smoke_test`.
- `icoder/env_setup.py:197` — already passes `str(project_dir)`; only the keyword name changes.

### F. Docstrings mentioning the removed concept

`llm/providers/claude/claude_mcp_guard.py:166`, `workflow_utils/commit_operations.py:21`,
`cli/commands/commit.py:98`, and the public examples at `mcp_coder/__init__.py:10-11`,
`llm/interface.py:128`, `:133` (all call `prompt_llm` without `project_dir`).

## WHAT

```python
def prompt_llm(
    question: str,
    *,
    project_dir: str | Path,
    provider: str | None = None,
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    branch_name: str | None = None,
    inject_prompts: bool = False,
) -> LLMResponseDict: ...


def prompt_llm_stream(
    question: str,
    *,
    project_dir: str | Path,
    provider: str | None = None,
    session_id: str | None = None,
    timeout: int = LLM_DEFAULT_TIMEOUT_SECONDS,
    env_vars: dict[str, str] | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    branch_name: str | None = None,
    tools: list[Any] | None = None,
    inject_prompts: bool = False,
) -> Iterator[StreamEvent]: ...
```

Three deliberate properties, each with a reason in the summary: **required** (its `None`
fallback was the #1113 bug), **keyword-only after `question`** (a required positional at
position 2 would silently reinterpret `prompt_llm("q", "claude")`), **`str | Path`** (avoids
~20 mechanical conversions at call sites).

Document `project_dir` as *"Project directory. Used as the working directory (cwd) of the LLM
subprocess."* and `inject_prompts` as *"When True, load the system and project prompts from
project_dir and pass them to the provider. Default False: headless runs inject nothing."*

## ALGORITHM (inside both functions)

```
validate question / timeout                    # unchanged
provider = provider or env var or "claude"     # unchanged
project_path = Path(project_dir)               # normalise once, do NOT resolve again
if inject_prompts:                             # was: if project_dir:
    system_prompt, project_prompt, prompts_config = load_prompts(project_path)
cwd = str(project_path)                        # every provider branch uses this
metadata = {"branch_name": …, "working_directory": cwd}   # stays a str
```

Resolution stays in `resolve_claude_cwd` alone — do not add a second `.resolve()` here.
`_build_claude_system_prompts` keeps its current signature; pass `str(project_path)` where the
old code passed the `project_dir` string.

## DATA

`LLMResponseDict` / `StreamEvent` unchanged. `metadata["working_directory"]` stays a `str`.
`CIFixConfig` loses one field. `RealLLMService.project_dir` becomes **required** (`str | Path`),
since `prompt_llm_stream` can no longer accept `None`.

## The `inject_prompts` mapping — decide each site, never take the default blindly

| Call site | Value |
|---|---|
| `verify.py:498-507` (LLM check — the comment at `:491-492` says the injection is deliberate) | `inject_prompts=True` |
| `icoder/services/llm_service.py:104-115` (`RealLLMService.stream`) | `inject_prompts=True` |
| `prompt.py:150, 190, 213` | `inject_prompts=getattr(args, "add_system_prompts", False)` — replaces the `prompt_project_dir` variable at `:132-134`; **stays conditional** |
| `verify.py:97-105` (`_run_mcp_edit_smoke_test`) | default `False` |
| `icoder/env_setup.py:112-119` (tool probe) | default `False` |
| every workflow / `workflow_steps` / `workflow_utils` site | default `False` |

Getting one of these wrong silently changes what the model is told — this table is the
acceptance criteria "headless runs inject no prompt", "verify still sends the merged prompt",
"iCoder still injects".

## TDD

**New tests first** (they encode the acceptance criteria):

```python
def test_prompt_llm_requires_project_dir() -> None:
    with pytest.raises(TypeError):
        prompt_llm("hi")                      # no silent cwd fallback

def test_prompt_llm_uses_project_dir_as_cwd(...) -> None:
    # patch ask_claude_code_cli; assert cwd == str(project_dir)

def test_workflow_call_does_not_inject_prompts(...) -> None:
    # patch prompt_llm; assert inject_prompts is False / load_prompts not called

def test_verify_llm_check_injects_prompts(...) -> None:
    # assert inject_prompts is True
```

**Then the ~470 mechanical test updates**, which reduce to two rules:

1. `execution_dir=<x>` in a call or mock assertion → `project_dir=<x>`; delete it outright
   where a sibling `project_dir=<same value>` already asserts it.
2. Leftover `execution_dir=None` attributes on `argparse.Namespace` fixtures → delete the line.

Files: `tests/llm/test_interface.py`, `tests/workflows/**` (8 files), `tests/workflow_steps/`,
`tests/workflow_utils/`, `tests/icoder/`, and the residual assertions in
`tests/cli/commands/**` left by step 3.

**Implementation order** (keeps mypy useful as the driver): `interface.py` first — then run
mypy and work the error list bottom-up (providers → workflows → commands). mypy names every
stale keyword, so treat its output as the worklist rather than re-reading each file.

## Verification beyond the gate

- `grep -rn "execution_dir" src/` → no hits (acceptance criterion).
- `prompt_llm("q")` raises `TypeError`, not a run in the process cwd.
- Run `mcp-coder verify` and one headless workflow from an unrelated shell cwd if credentials
  allow; otherwise rely on the injection tests above.

## Commit

```
Collapse execution_dir onto project_dir in prompt_llm and all workflows

prompt_llm/prompt_llm_stream now take a required keyword-only project_dir
(the subprocess cwd) plus an explicit inject_prompts switch, so prompt
injection stays exactly where it is today. Removes execution_dir from 23
signatures, three dead cwd fallbacks and CIFixConfig. Closes the src half
of #1132.

BREAKING: prompt_llm requires project_dir.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`, then implement step 4 only.
>
> Rewrite `prompt_llm` and `prompt_llm_stream` in `src/mcp_coder/llm/interface.py` to take a
> **required, keyword-only** `project_dir: str | Path` (used as the subprocess `cwd`) plus
> `inject_prompts: bool = False`, making every parameter after `question` keyword-only. Gate the
> `load_prompts` block on `inject_prompts`, normalise the path once with `Path(project_dir)`
> and do **not** resolve again — resolution belongs to `resolve_claude_cwd`. Then delete the
> `execution_dir` parameter from the 23 signatures listed in the step document, delete the
> three dead `cwd = str(execution_dir) if execution_dir else str(project_dir)` fallbacks, and
> delete `CIFixConfig.cwd` (its three uses become `str(config.project_dir)`). Rename
> `_probe_exposed_mcp_tools`'s parameter to `project_dir`. Make `RealLLMService.project_dir`
> required. Update the docstring examples in `src/mcp_coder/__init__.py` and `interface.py`
> that call `prompt_llm` without `project_dir`.
>
> Apply the `inject_prompts` table in the step document **site by site** — `verify.py`'s LLM
> check and iCoder's `RealLLMService` get `True`; `prompt.py` gets
> `getattr(args, "add_system_prompts", False)` and must stay conditional; verify's MCP edit
> smoke test, iCoder's tool probe and every workflow keep the `False` default. Do not
> hard-code any of them.
>
> Follow TDD: write the four new behaviour tests first (required `project_dir` raises
> `TypeError`; cwd equals `project_dir`; workflows inject nothing; verify injects), then make
> the source change, then sweep the remaining test references with the two mechanical rules in
> the step. Use `mcp__tools-py__run_mypy_check` output as the worklist for the sweep rather
> than re-reading every file.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass, and
> `grep -r execution_dir src/` must return nothing. One commit for this step.
