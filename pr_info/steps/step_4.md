# Step 4 — `prompt_llm` takes `project_dir`; delete `execution_dir` from every workflow

**Context:** [summary.md](./summary.md), sections 1, 3 and 6.

**Two commits: 4a then 4b.** They split along a line that keeps both green:

- **4a — the interface and its direct callers.** Rewrite `prompt_llm` / `prompt_llm_stream`
  (section A) and retarget every site that calls them (section E1) to pass `project_dir=` plus
  the mapped `inject_prompts`. The 23 workflow `execution_dir` parameters (section B) **stay in
  place and stay used** — each one still supplies the value now handed over as `project_dir` —
  so nothing goes unused, pylint/mypy/pytest pass, and behaviour is already final.
- **4b — the parameter sweep.** Delete the 23 `execution_dir` parameters (section B), the dead
  `cwd = …` fallbacks (section C), `CIFixConfig.cwd` (section D) and the duplicated arguments at
  the forwarding call sites (section E2). Pure signature work: no behaviour changes.

After 4b, `grep -r execution_dir src/` returns nothing.

## WHERE — checklist

### A. The interface (`src/mcp_coder/llm/interface.py`) — 4a

`prompt_llm` (`:72`) and `prompt_llm_stream` (`:287`).

### B. The 23 signatures that carry the parameter (deleted in 4b)

| File | Line(s) |
|---|---|
| `cli/commands/check_branch_status.py` | `:379` (`_run_auto_fixes`) |
| `cli/commands/verify.py` | `:73` (`_run_mcp_edit_smoke_test`) |
| `icoder/env_setup.py` | `:88` (`_probe_exposed_mcp_tools` — **rename** to `project_dir`, not delete) |
| `icoder/services/llm_service.py` | `:52` (`RealLLMService.__init__` — the `execution_dir` parameter goes in 4b, but **`project_dir` must become required in 4a**, see below) |
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

**`generate_commit_message_with_llm` is not a pure deletion.** Its signature is
`(project_dir, provider, execution_dir, mcp_config, settings_file)` (`commit_operations.py:66-70`),
so `execution_dir` sits in the *middle*: removing it shifts `mcp_config` and `settings_file` one
position left, and any caller passing them positionally would silently bind the wrong value —
the same hazard step 1 calls out for langchain. Search the project for
`generate_commit_message_with_llm(` (`cli/commands/commit.py:95`, `workflow_steps/commit.py:100-106`,
and the tests) and confirm every argument after `provider` is passed by keyword before deleting
the parameter; convert any positional caller found.

### C. Dead branches that disappear with the parameter (4b)

`task_processing.py:394`, `review/reviewer.py:132`, `:210`, `workflow_steps/ci.py:549` —
all `cwd = str(execution_dir) if execution_dir else str(project_dir)`. `resolve_claude_cwd`
never returns `None`, so the fallback was dead; the surviving half proves `project_dir` is
already in scope at every leaf.

### D. `CIFixConfig` (`workflow_steps/ci.py:52`) — 4b

Delete the `cwd: str` field (`:58`). Uses at `:131`, `:211`, `:251` become
`str(config.project_dir)`. Delete `cwd=cwd` from the constructor call (`:552-562`).

### E1. Direct `prompt_llm` / `prompt_llm_stream` callers — retargeted in 4a

Each passes `project_dir=` (the value it passed as `execution_dir`, except where the two rows
below say otherwise) plus the `inject_prompts` value from the mapping table below:

`cli/commands/prompt.py:150`, `:190`, `:213`; `cli/commands/verify.py:97-105` and `:498-507`;
`icoder/services/llm_service.py:104-115`; `icoder/env_setup.py:112-119`;
`workflow_utils/commit_operations.py:166`; `workflows/implement/task_processing.py:221`, `:439`;
`workflows/rebase.py:319`; `workflows/implement/finalisation.py:89`;
`workflows/implement/task_tracker_prep.py:78`; `workflows/create_plan/core.py:250`, `:312`,
`:361`; `workflows/create_pr/core.py:270`; `workflows/review/reviewer.py:161`, `:228`;
`workflow_steps/ci.py:125-131`, `:205-211`.

**Two sites must pass their own `project_dir` parameter, not the value they passed as
`execution_dir`** — following the general rule at either one makes 4a red:

| Site | 4a passes | Why |
|---|---|---|
| `workflow_utils/commit_operations.py:166` (`:171` is the keyword) | `project_dir=str(project_dir)` | its `execution_dir` is `Optional[str] = None` (`commit_operations.py:68`), so `project_dir=execution_dir` feeds `str \| None` into the now-required `project_dir: str \| Path` → mypy incompatible-argument error. `project_dir: Path` is the function's first parameter (`:66`). Same fix class as `RealLLMService.project_dir` below. |
| `cli/commands/verify.py:97-105` (`:103` is the keyword) | `project_dir=project_dir` | `project_dir: Path` is already `_run_mcp_edit_smoke_test`'s first parameter (`verify.py:70`). Passing `project_dir=execution_dir` instead would leave an undefined name in the body once 4b deletes the `execution_dir` parameter (`verify.py:73`) — pylint `E0602` / mypy `name-defined`, i.e. a red 4b. |

**Not in this list — do not touch them in 4a.** Six sites carry an `execution_dir=` keyword but
call something other than `prompt_llm`, so retargeting them to `project_dir=` would pass an
unknown keyword to a signature section B keeps until 4b (`workflow_steps/commit.py:64`,
`workflow_utils/commit_operations.py:68`) — mypy error and `TypeError` at runtime, i.e. a red 4a:

| Site | Actually calls |
|---|---|
| `workflows/implement/core.py:280` | `commit_changes(...)` |
| `workflows/review/core.py:425` | `commit_changes(...)` |
| `workflows/implement/task_processing.py:543` | `commit_changes(...)` |
| `workflow_steps/ci.py:251` | `commit_changes(...)` |
| `workflows/implement/finalisation.py:147` | `generate_commit_message_with_llm(...)` |
| `workflow_steps/commit.py:104` | `generate_commit_message_with_llm(...)` |

They are handled in **4b/E2**, when the parameters they feed are deleted.

The `execution_dir=str(execution_dir) if execution_dir else None` sites become
`project_dir=str(project_dir)` — `project_dir` is in scope at every one of them, and the `None`
half was the #1113 bug.

### E2. Forwarding call sites that lose an argument — 4b

Deleting a parameter in section B breaks every call that still supplies it. Command-level:

- `cli/commands/*` — drop the duplicated `project_dir` argument introduced in step 3.
- `icoder.py:202` — drop `execution_dir=`; `project_dir=` (`:208`) already present.
- `verify.py` — drop the `str(project_dir)` argument at the call site (`:476-484`) **and** the
  `execution_dir: str` parameter plus its docstring line from `_run_mcp_edit_smoke_test`
  (`:73`, `:84`). Its body needs no edit: 4a already made the `prompt_llm` call pass
  `project_dir=project_dir`, the function's own first parameter (see E1).
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

The six sites held back from E1 land here — they pass `execution_dir=` to `commit_changes`
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

The public examples at `mcp_coder/__init__.py:10-11`, `llm/interface.py:128`, `:133` (all call
`prompt_llm` without `project_dir`) are fixed in **4a**, with the signature they document.
`llm/providers/claude/claude_mcp_guard.py:166`, `workflow_utils/commit_operations.py:21` and
`cli/commands/commit.py:98` are fixed in **4b**, with the parameters they mention.

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
`CIFixConfig` loses one field (4b).

`RealLLMService.project_dir` becomes **required** (`str | Path`) — **in 4a, not 4b.** It is
`str | None` today (`llm_service.py:58`, stored at `:69`), so the moment `:114` passes
`project_dir=self._project_dir` into a required `str | Path`, mypy reports an incompatible
argument type; narrowing the constructor parameter is what makes 4a pass its own gate. The
`execution_dir` parameter beside it (`:52`, `self._execution_dir` at `:63`) still goes in 4b.

**Mechanism — do not just delete the default.** `project_dir` is the *ninth* parameter
(`llm_service.py:48-60`) and every parameter before it has a default, so dropping its `= None`
is a `SyntaxError` (non-default argument follows default argument). **Keep the parameter where
it is and insert a `*` keyword-only marker immediately before it**, which is the smallest change
and reorders no call site:

```python
def __init__(
    self,
    provider: str = "claude",
    session_id: str | None = None,
    execution_dir: str | None = None,          # deleted in 4b
    mcp_config: str | None = None,
    settings_file: str | None = None,
    env_vars: dict[str, str] | None = None,
    timeout: int = ICODER_LLM_TIMEOUT_SECONDS,
    mcp_manager: MCPManager | None = None,
    *,
    project_dir: str | Path,                   # required, keyword-only
    gateway: LangchainEnforcementGateway | None = None,
) -> None: ...
```

`gateway` becomes keyword-only too, which is why the constructions must be audited: **search
`RealLLMService(` across `src/` and `tests/` and fix two things** — any construction that passes
arguments *positionally* (a positional `gateway` or a positional argument reaching past
`mcp_manager` now fails), and any construction that **omits `project_dir`**, which is now a
`TypeError`. The production caller `icoder.py:199-208` already passes everything by keyword
including `project_dir=str(project_dir)`, so it needs no change; the work is in
`tests/icoder/test_llm_service.py` (~20 constructions, most of them `RealLLMService(provider=…)`
with no `project_dir`) and `tests/icoder/test_icoder_permission_wiring.py:273`, `:320`. Give them
a `tmp_path`-based or literal project dir. Without this sweep 4a's pytest run is red even though
mypy is clean.

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

All four new tests and the whole `inject_prompts` mapping belong to **4a** — behaviour is final
once 4a lands. 4b changes no behaviour, so it adds no new tests; it only sweeps the remaining
`execution_dir=` keywords out of the workflow-level mocks.

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

Rule 1 applies to `prompt_llm` / `prompt_llm_stream` call and assertion sites in **4a**
(`tests/llm/test_interface.py`, the `prompt_llm` assertions under `tests/workflows/**`,
`tests/workflow_utils/`, `tests/icoder/`, `tests/cli/commands/test_verify*.py`,
`tests/cli/commands/test_prompt.py`) and to workflow-signature keywords in **4b**
(the remaining `tests/workflows/**` (8 files), `tests/workflow_steps/`, `tests/icoder/`, and the
residual assertions in `tests/cli/commands/**` left by step 3). Rule 2 belongs to 4b.

**Implementation order** (keeps mypy useful as the driver): `interface.py` first — then run
mypy and work the error list bottom-up (providers → workflows → commands). mypy names every
stale keyword, so treat its output as the worklist rather than re-reading each file. The same
applies to 4b, where mypy's "unexpected keyword argument" / "too many arguments" list is the
complete worklist for sections B, C, D and E2.

## Verification beyond the gate

Run after **both** 4a and 4b:

- `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])` — the mandated fast gate
  excludes this marker, but `tests/integration/test_claude_cwd_integration.py`'s two retained
  tests carry it (`TestSubprocessCwdParameter`, plus the `require_claude_cli` fixture) and they
  are the *only* end-to-end pin of "subprocess `cwd` equals the resolved `project_dir`". This
  step rewrites every layer they span (`execute_prompt` → `prompt_llm_stream` →
  `stream_subprocess`), so without this run the file ships unverified. If the tests skip because
  the Claude CLI is absent, say so explicitly rather than treating the skip as a pass.
- `grep -rn "execution_dir" src/` → no hits after 4b (acceptance criterion).
- `prompt_llm("q")` raises `TypeError`, not a run in the process cwd.
- Run `mcp-coder verify` and one headless workflow from an unrelated shell cwd if credentials
  allow; otherwise rely on the injection tests above.

## Commits

**4a:**

```
Give prompt_llm a required project_dir and an explicit inject_prompts switch

prompt_llm/prompt_llm_stream now take a required keyword-only project_dir
(the subprocess cwd) plus inject_prompts, so prompt injection stays exactly
where it is today instead of riding on whether project_dir was passed. All
direct callers pass project_dir; the workflow-level execution_dir parameters
still feed it and are removed next. Part of #1132.

BREAKING: prompt_llm requires project_dir.
```

**4b:**

```
Delete execution_dir from the workflow signatures

With prompt_llm deriving cwd from project_dir, the execution_dir parameter
threaded through 23 signatures only forwarded a value the callee already had.
Removes it, the three dead `cwd = str(execution_dir) if ...` fallbacks and
CIFixConfig.cwd. Closes the src half of #1132.
```

## LLM prompt — 4a

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`, then implement **step 4a only**.
>
> Rewrite `prompt_llm` and `prompt_llm_stream` in `src/mcp_coder/llm/interface.py` to take a
> **required, keyword-only** `project_dir: str | Path` (used as the subprocess `cwd`) plus
> `inject_prompts: bool = False`, making every parameter after `question` keyword-only. Gate the
> `load_prompts` block on `inject_prompts`, normalise the path once with `Path(project_dir)`
> and do **not** resolve again — resolution belongs to `resolve_claude_cwd`. Update the
> docstring examples in `src/mcp_coder/__init__.py` and `interface.py` that call `prompt_llm`
> without `project_dir`.
>
> Then retarget **only the direct callers** listed in section E1 to pass `project_dir=` (the
> value they passed as `execution_dir`; `str(execution_dir) if execution_dir else None` becomes
> `str(project_dir)`). **Two of them take their own `project_dir` parameter instead** — see the
> exception table in E1: `workflow_utils/commit_operations.py:166` passes
> `project_dir=str(project_dir)` (its `execution_dir` is `Optional[str]`, which no longer
> type-checks) and `cli/commands/verify.py:97-105` passes `project_dir=project_dir` (already
> `_run_mcp_edit_smoke_test`'s first parameter, so 4b's deletion of `execution_dir` leaves no
> dangling name). **Do not touch the 23 workflow signatures in section B, the section C
> fallbacks or `CIFixConfig` — that is 4b.** In particular, leave the six `execution_dir=`
> keywords named under E1 as "not in this list" alone: they call `commit_changes` /
> `generate_commit_message_with_llm`, whose parameters still exist until 4b, so renaming them
> here would be an unknown keyword argument.
>
> One section B signature does change in 4a: make `RealLLMService.__init__`'s `project_dir`
> **required** (`str | Path`), since `self._project_dir` is `str | None` today and
> `prompt_llm_stream` no longer accepts `None`. Leave its `execution_dir` parameter for 4b.
> **Do not simply delete its `= None`** — it is the ninth parameter and every parameter before
> it has a default, so that is a `SyntaxError`. Keep its position and insert a `*` keyword-only
> marker immediately before it (see DATA), then search `RealLLMService(` across `src/` and
> `tests/`: fix any positional construction (`gateway` is now keyword-only too) and add
> `project_dir=` to every construction that omits it — ~20 in
> `tests/icoder/test_llm_service.py` and two in `tests/icoder/test_icoder_permission_wiring.py`
> (`:273`, `:320`). Skipping that sweep leaves 4a red at pytest even with mypy clean.
>
> Apply the `inject_prompts` table in the step document **site by site** — `verify.py`'s LLM
> check and iCoder's `RealLLMService` get `True`; `prompt.py` gets
> `getattr(args, "add_system_prompts", False)` and must stay conditional; verify's MCP edit
> smoke test, iCoder's tool probe and every workflow keep the `False` default. Do not
> hard-code any of them.
>
> Follow TDD: write the four new behaviour tests first (required `project_dir` raises
> `TypeError`; cwd equals `project_dir`; workflows inject nothing; verify injects), then make
> the source change, then sweep the `prompt_llm` call and assertion sites in the tests. Use
> `mcp__tools-py__run_mypy_check` output as the worklist rather than re-reading every file.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass. Also run
> `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])` — the fast gate excludes
> the marker carried by `tests/integration/test_claude_cwd_integration.py`, the only end-to-end
> pin of the subprocess cwd. One commit for this step.

## LLM prompt — 4b

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`, then implement **step 4b only**
> (4a must already be committed).
>
> Delete the `execution_dir` parameter from the 23 signatures in section B, delete the three
> dead `cwd = str(execution_dir) if execution_dir else str(project_dir)` fallbacks (section C)
> and `CIFixConfig.cwd` (section D — its three uses become `str(config.project_dir)`). Rename
> `_probe_exposed_mcp_tools`'s parameter to `project_dir`. (`RealLLMService.project_dir` was
> already made required in 4a — only its `execution_dir` parameter is left to delete here.)
> Fix the docstrings in section F.
>
> Update every forwarding call site in section E2 — including the six `commit_changes` /
> `generate_commit_message_with_llm` keywords held back from 4a — note which are **positional**,
> and note that
> `generate_commit_message_with_llm`'s `execution_dir` is a *middle* positional parameter, so
> removing it shifts `mcp_config`/`settings_file` by one for any positional caller: audit those
> call sites before deleting. Then sweep the remaining test references with the two mechanical
> rules in the step, using `mcp__tools-py__run_mypy_check` output as the worklist.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass, plus
> `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])`, and
> `grep -r execution_dir src/` must return nothing. One commit for this step.
