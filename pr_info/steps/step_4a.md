# Step 4a — `prompt_llm` takes a required `project_dir`; retarget the direct callers

**Context:** [summary.md](./summary.md), sections 1 and 3. Step 4 is two commits: **4a** here,
**4b** in [step_4b.md](./step_4b.md).

4a rewrites `prompt_llm` / `prompt_llm_stream` (section A) and retargets every site that calls
them (section E1) to pass `project_dir=` plus the mapped `inject_prompts`. The 23 workflow
`execution_dir` parameters stay in place; 4b deletes them. **Behaviour is final once 4a lands** —
4b changes no behaviour.

**Why 4a is still green.** Seven of those 23 parameters become *unused* after 4a
(`create_plan/core.py:190`, `create_pr/core.py:205`, `task_tracker_prep.py:31`, `rebase.py:304`,
`task_processing.py:138`, `verify.py:73`, `workflow_utils/commit_operations.py:68`) — their only
job was to feed `prompt_llm`. That does not fail the gate because pylint's `W0613`
(unused-argument) is disabled project-wide (`pyproject.toml:207`,
`[tool.pylint.messages_control]`). `icoder/env_setup.py:88` is **not** in that set: 4a passes
`project_dir=execution_dir` there, so it stays used until 4b.

## WHERE — checklist

### A. The interface (`src/mcp_coder/llm/interface.py`)

`prompt_llm` (`:72`) and `prompt_llm_stream` (`:287`).

### E1. Direct `prompt_llm` / `prompt_llm_stream` callers

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
unknown keyword to a signature 4b keeps until then (`workflow_steps/commit.py:64`,
`workflow_utils/commit_operations.py:68`) — mypy error and `TypeError` at runtime, i.e. a red 4a:

| Site | Actually calls |
|---|---|
| `workflows/implement/core.py:280` | `commit_changes(...)` |
| `workflows/review/core.py:425` | `commit_changes(...)` |
| `workflows/implement/task_processing.py:543` | `commit_changes(...)` |
| `workflow_steps/ci.py:251` | `commit_changes(...)` |
| `workflows/implement/finalisation.py:147` | `generate_commit_message_with_llm(...)` |
| `workflow_steps/commit.py:104` | `generate_commit_message_with_llm(...)` |

They are handled in **4b, section E2**, when the parameters they feed are deleted.

The `execution_dir=str(execution_dir) if execution_dir else None` sites become
`project_dir=str(project_dir)` — `project_dir` is in scope at every one of them, and the `None`
half was the #1113 bug.

### F. Docstrings mentioning the removed concept

The public examples at `mcp_coder/__init__.py:10-11`, `llm/interface.py:128`, `:133` (all call
`prompt_llm` without `project_dir`) are fixed here, with the signature they document. The
remaining docstrings are fixed in 4b, with the parameters they mention.

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

`LLMResponseDict` / `StreamEvent` unchanged. `metadata["working_directory"]` stays a `str`, and
is now never `None`.

`RealLLMService.project_dir` becomes **required** (`str | Path`) — **in 4a, not 4b.** It is
`str | None` today (`llm_service.py:58`, stored at `:69`), so the moment `:114` passes
`project_dir=self._project_dir` into a required `str | Path`, mypy reports an incompatible
argument type; narrowing the constructor parameter is what makes 4a pass its own gate. The
`execution_dir` parameter beside it (`:52`, `self._execution_dir` at `:63`) goes in 4b.

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

### Tests that pin the removed semantics — delete or rewrite, do not rename

Handle these six sites **before** applying the mechanical rules below; the rules would turn each
of them into `project_dir=None` against a required `str | Path`.

| Site | Action |
|---|---|
| `tests/llm/test_interface.py:339` `test_execution_dir_none_uses_default` (call at `:352`) | Delete. It pins the cwd fallback #1132 removes. |
| `tests/llm/test_interface.py:759` `test_execution_dir_none_defaults_to_cwd` (call at `:773`) | Delete, same reason. Its class `TestPromptLLMExecutionDir` (`:722`) then holds only `test_execution_dir_with_cli` — rename the class and the surviving test onto `project_dir`. |
| `tests/llm/test_interface.py:1343` `test_metadata_defaults_to_none_values` (`:1346`, `:1359`, `:1363`) | Rewrite. `metadata["working_directory"]` can no longer be `None`; assert `branch_name is None` and `working_directory == str(project_dir)`. |
| `tests/llm/test_interface.py:1622` `TestPromptLlmProjectDir` — `:1626` (`prompt_llm("Test question", project_dir=None)`), `:1657` (`:1684`), `:1710` (`:1733`) | Rewrite onto `inject_prompts`. The class tests today's `project_dir`-as-prompt-switch, which is exactly what 4a splits: the `None` case becomes `inject_prompts=False` (no prompts loaded) and the two loading cases become `project_dir=…, inject_prompts=True`. Rename the class accordingly. |

### Then the mechanical test updates

Three rules:

1. `execution_dir=<x>` in a call or mock assertion → `project_dir=<x>`; delete it outright
   where a sibling `project_dir=<same value>` already asserts it.
2. Leftover `execution_dir=None` attributes on `argparse.Namespace` fixtures → delete the line.
   **(4b — see [step_4b.md](./step_4b.md).)**
3. **Every remaining `prompt_llm` / `prompt_llm_stream` call in `tests/` must gain a
   `project_dir=` argument** (a `tmp_path` or a literal). Rule 1 only rewrites calls that
   already pass a directory; roughly 90 calls pass *neither* `execution_dir` nor `project_dir`
   and raise `TypeError` the moment 4a lands. Known clusters: `tests/llm/test_interface.py`
   (~70 — `:31`, `:62`, `:108`, `:174`, `:203`, `:502`, `:574`, `:651`, `:1091`, `:1359`,
   `:1403`, `:1476`, …), `tests/llm/providers/claude/test_llm_sessions.py` (~20),
   `tests/llm/providers/claude/test_claude_integration.py:29`, `:46`, `:53`, `:122`,
   `tests/llm/providers/claude/test_claude_code_cli_streaming_integration.py:71`,
   `tests/test_input_validation.py:73`, `:78`, and
   `tests/workflows/review/test_prototype_session_interleave.py:88`.

Rules 1 and 3 apply to `prompt_llm` / `prompt_llm_stream` call and assertion sites in **4a**
(`tests/llm/test_interface.py`, the `prompt_llm` assertions under `tests/workflows/**`,
`tests/workflow_utils/`, `tests/icoder/`, `tests/cli/commands/test_verify*.py`,
`tests/cli/commands/test_prompt.py`). Rule 1's workflow-signature keywords and rule 2 belong
to 4b.

**Grep instruction — do not rely on the fast gate to find these.** Several of the rule-3 sites
sit behind `claude_api_integration` / `claude_cli_integration` markers, which the mandated fast
gate excludes, so a missed call fails only in CI. Before committing, search
`prompt_llm(` and `prompt_llm_stream(` across **all** of `tests/` — including marker-excluded
files — and confirm every hit passes `project_dir=`.

**Implementation order** (keeps mypy useful as the driver): `interface.py` first — then run
mypy and work the error list bottom-up (providers → workflows → commands). mypy names every
stale keyword, so treat its output as the worklist rather than re-reading each file. mypy will
**not** flag the rule-3 sites in tests that lack `project_dir` if the file is untyped, so the
grep above is the safety net.

## Verification beyond the gate

- `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])` — the mandated fast gate
  excludes this marker, but `tests/integration/test_claude_cwd_integration.py`'s two retained
  tests carry it (`TestSubprocessCwdParameter`, plus the `require_claude_cli` fixture) and they
  are the *only* end-to-end pin of "subprocess `cwd` equals the resolved `project_dir`". This
  step rewrites every layer they span (`execute_prompt` → `prompt_llm_stream` →
  `stream_subprocess`), so without this run the file ships unverified. If the tests skip because
  the Claude CLI is absent, say so explicitly rather than treating the skip as a pass.
- `prompt_llm("q")` raises `TypeError`, not a run in the process cwd.
- Run `mcp-coder verify` and one headless workflow from an unrelated shell cwd if credentials
  allow; otherwise rely on the injection tests above.

## Commit

```
Give prompt_llm a required project_dir and an explicit inject_prompts switch

prompt_llm/prompt_llm_stream now take a required keyword-only project_dir
(the subprocess cwd) plus inject_prompts, so prompt injection stays exactly
where it is today instead of riding on whether project_dir was passed. All
direct callers pass project_dir; the workflow-level execution_dir parameters
still feed it and are removed next. Part of #1132.

BREAKING: prompt_llm requires project_dir.
```

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4a.md`, then implement **step 4a only**.
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
> dangling name). **Do not touch the 23 workflow signatures, the dead `cwd = …` fallbacks or
> `CIFixConfig` — that is 4b (`pr_info/steps/step_4b.md`).** In particular, leave the six
> `execution_dir=` keywords named under E1 as "not in this list" alone: they call
> `commit_changes` / `generate_commit_message_with_llm`, whose parameters still exist until 4b,
> so renaming them here would be an unknown keyword argument.
>
> One workflow signature does change in 4a: make `RealLLMService.__init__`'s `project_dir`
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
> the source change, then sweep the test call sites. Handle the six delete-or-rewrite tests in
> the TDD table **before** the mechanical rules — they pin the removed `None` semantics and
> cannot be renamed into the new signature. Then apply rules 1 and 3: rule 3 requires that
> **every** remaining `prompt_llm` / `prompt_llm_stream` call in `tests/` gains a `project_dir=`
> argument, including the ~90 that pass no directory today. Finish that sweep with a search for
> `prompt_llm(` / `prompt_llm_stream(` across all of `tests/`, **including marker-excluded
> files** — several of these sites sit behind `claude_api_integration` /
> `claude_cli_integration` and the fast gate would hide them. Use
> `mcp__tools-py__run_mypy_check` output as the worklist for the source side.
>
> Use MCP tools exclusively. Finish with `mcp__tools-py__run_pylint_check`,
> `mcp__tools-py__run_pytest_check` (with `extra_args=["-n","auto","-m","not git_integration
> and not claude_cli_integration and not claude_api_integration and not formatter_integration
> and not github_integration and not langchain_integration"]`) and
> `mcp__tools-py__run_mypy_check`; all three must pass. Also run
> `mcp__tools-py__run_pytest_check(markers=["claude_cli_integration"])` — the fast gate excludes
> the marker carried by `tests/integration/test_claude_cwd_integration.py`, the only end-to-end
> pin of the subprocess cwd. One commit for this step.
