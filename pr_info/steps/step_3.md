# Step 3: Fix loop with a shared cap, and both callers on the new result type

Replaces `check_and_fix_mypy`'s `bool` result and identical-output counter with a grouped, capped loop returning `CheckOutcome`. Both callers switch to it. Rescue commits come in step 4; in this step check-stage aborts fail directly.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 only. Write the tests in `tests/workflows/implement/test_check_loop.py`, `test_check_loop_fix_turns.py`, `test_task_processing_checks.py` and `test_core_final_check.py` first, then create `check_loop.py`, move the fix-loop code there and update `task_processing.py`, `core.py` and `__init__.py`. Delete `tests/workflows/implement/test_task_processing_mypy.py` once its useful cases are covered in the new files. Keep every file under 750 lines. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- Create `src/mcp_coder/workflows/implement/check_loop.py`.
- Modify `task_processing.py`, `core.py`, `__init__.py` in `src/mcp_coder/workflows/implement/`.
- Tests: create `test_check_loop.py`, `test_check_loop_fix_turns.py`, `test_task_processing_checks.py`, `test_core_final_check.py`; delete `test_task_processing_mypy.py`; update `test_task_processing.py`, `test_task_processing_branch_name.py`, `test_core.py`, `test_core_failure_categories.py`, `test_core_failure_routing.py`, `test_core_workflow.py` (all in `tests/workflows/implement/`).

## WHAT

```python
# check_loop.py
MAX_FIX_TURNS = 3

CheckStatus = Literal["clean", "cap", "error", "blocked", "timeout", "mcp_unavailable"]

@dataclass(frozen=True)
class CheckOutcome:
    """Result of one binding run with its fix loop."""
    status: CheckStatus
    detail: str = ""   # error/config message, blocked reason, cap summary,
                       # or the blocked text for timeout / mcp_unavailable

class _CheckAbort(Exception):
    """A config error or an `error` result; aborts the binding run."""

def check_and_fix_mypy(
    project_dir: Path,
    step_num: int,
    provider: str,
    env_vars: dict[str, str] | None = None,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    entry: str = "implement_final",
    check_type_hints: bool = True,
) -> CheckOutcome: ...

def _split_requests(
    binding: Sequence[str], check_type_hints: bool
) -> tuple[list[str], list[str]]:
    """(check requests, test requests); drops check@* when check_type_hints is False
    and logs one line naming the dropped requests. Other actions are ignored."""

def _run_group(loaded: LoadedToolkit, project_dir: Path, requests: list[str]) -> str | None:
    """Run each request with run_request. Raise _CheckAbort on an `error` result
    (message "<request>: <summary>"); log skipped; return the joined
    fix_text-or-summary of results with findings, or None."""

def _fix_turn(
    prompt: str, project_dir: Path, provider: str, turn: int, step_num: int,
    env_vars, mcp_config, settings_file, bash_grants: list[str],
) -> CheckOutcome | None:
    """One LLM fix turn. None when the turn went through; otherwise the outcome
    that ends the loop."""

def _build_fix_prompt(fix_fragment: str, fix_text: str, check_instructions: str) -> str:
    """Moved unchanged from task_processing (heading "Check output:")."""
```

## HOW
- Move `_build_fix_prompt` and `_CHECK_OUTPUT_HEADING` from `task_processing.py` to `check_loop.py`. Delete `_run_check`, `_fix_check_text` and the old `check_and_fix_mypy` from `task_processing.py`; remove now-unused imports there (`get_binding`, `load_toolkit`, `run_binding`, `toolkit_declares_bash_grants`, etc. — keep what `process_single_task` still uses).
- `check_loop.py` imports: `load_toolkit`, `run_request`, `get_fragment`, `llm_permissions`, `bash_grants_of`, `LoadedToolkit` from `mcp_coder.utils.toolkit_runner`; `resolve_prompt_slots`, `toolkit_declares_bash_grants` from `mcp_coder.utils.prompt_slots`; `prompt_llm`, `LLMTimeoutError` from `mcp_coder.llm.interface`; `McpServersUnavailableError`; `llm_failure_reason`; `store_session`; `get_branch_name_for_logging`; `read_and_clear_blocked` from `.blocked`; `LLM_INACTIVITY_TIMEOUT_SECONDS` from `.constants`.
- `get_fragment` already returns the raw fragment, or `""` when missing or when `prompt_fragments()` raises. A falsy fragment counts as missing.
- Compute `bash_grants` and `check_instructions` once, lazily, before the first fix turn, exactly as the old code did.
- `__init__.py` re-exports `check_and_fix_mypy` from `.check_loop`; also export `CheckOutcome`.
- Session step name stays `f"step_{step_num}_mypy_{turn}"`.

### `_fix_turn` rules
- `prompt_llm` raises `LLMTimeoutError` / `McpServersUnavailableError` → `blocked = read_and_clear_blocked(...)`; return `CheckOutcome(llm_failure_reason(e) or "timeout", blocked or "")`.
- Any other exception, or an empty / whitespace response → `read_and_clear_blocked`; if it returned a reason, return `blocked` with it, else return `CheckOutcome("cap", "Fix turn failed: <short reason>")`.
- Success: store the session (failures logged, as today), then `blocked = read_and_clear_blocked(...)`; return `CheckOutcome("blocked", blocked)` if set, else `None`.

### `process_single_task` (replace Step 7)
Remove the `if not check_type_hints` / `get_binding` block. Then:
```python
try:
    checks = check_and_fix_mypy(project_dir, step_num, provider, env_vars, mcp_config,
                                settings_file, entry="implement_task",
                                check_type_hints=check_type_hints)
finally:
    marker = read_and_clear_blocked(project_dir)   # safety net
if checks.status in ("clean", "cap") and marker:
    checks = CheckOutcome("blocked", marker)
if checks.status == "cap":
    logger.warning("Per-task checks still report findings - committing and continuing")
elif checks.status != "clean":
    return TaskOutcome(False, checks.status, checks.detail)
```
`error` maps to the existing `"error"` reason (core routes it to `general` with `outcome.detail`); `blocked`, `timeout`, `mcp_unavailable` are existing reasons. Update the docstring's reason list.

### `core.py` final check (Step 5 block)
- Remove the `get_binding` try block and `final_binding`; the gate becomes `if progress.completed > 0:` (step 5 removes that too). Drop the `get_binding` import.
- Call `check_and_fix_mypy(..., entry="implement_final", check_type_hints=implement_config.check_type_hints)` inside the existing `try/finally: read_and_clear_blocked`, capturing the marker; promote `clean` + marker to `blocked`.
- Map a non-clean outcome to `fail` with stage `"Final mypy check"`:

| status | reason | message |
|---|---|---|
| `cap` | `checks_exhausted` | `f"Checks still report findings after {MAX_FIX_TURNS} fix turns"` + `: detail` if any |
| `error` | `general` | `detail` |
| `blocked` | `blocked` | `detail` (log at ERROR like the task path) |
| `timeout` / `mcp_unavailable` | same | `append_detail("LLM failure during final mypy check", detail)` |

- Delete the inner `try/except (LLMTimeoutError, McpServersUnavailableError)` and the "continuing anyway" warning. Formatting, commit and push of a clean run stay as they are.

## ALGORITHM (`check_and_fix_mypy`)
```
turn = 0
loop:
    try: loaded = load_toolkit(dir); checks, tests = _split_requests(loaded.config.bindings[entry], cth)
         if not checks and not tests: log "<entry> skipped"; return clean
         text, key = _run_group(loaded, dir, checks), "fix.check"
         if text is None: text, key = _run_group(loaded, dir, tests), "fix.test"
    except ValueError / _CheckAbort as e: return CheckOutcome("error", str(e))
    if text is None: return clean
    fragment = get_fragment(loaded, key)
    if turn == MAX_FIX_TURNS or not fragment: return CheckOutcome("cap", <key and turn count>)
    turn += 1; ended = _fix_turn(_build_fix_prompt(fragment, text, instr), ...); if ended: return ended
```

## DATA
- `CheckOutcome(status, detail)` as above.
- `TaskOutcome` unchanged in this step.

## Tests (write first)

`test_check_loop.py` — patch `load_toolkit`, `run_request`, `get_fragment` and `_fix_turn` in `check_loop`; build a fake `LoadedToolkit` whose `config.bindings[entry]` is the binding under test:
- all clean → `clean`, no fix turn.
- grouping: binding `["test@quick", "check@quick"]` runs `check@quick` first; tests not run while a check has findings.
- check findings → `fix.check` fragment used; tests clean afterwards → `clean`.
- test findings after clean checks → `fix.test` used; next pass re-runs the checks first.
- cap: findings every pass → exactly 3 fix turns, then `cap`.
- clean after the third fix turn → `clean` (not the cap).
- shared cap: 2 check turns + 1 test turn, still findings → `cap` with 3 turns total.
- `error` result → `error`, no fix turn, detail contains the request and summary.
- `load_toolkit` raising `ValueError` on the first pass, and on a re-run after a fix turn → `error` with the config message.
- missing fragment, empty fragment (`""`) and `get_fragment` returning `""` because `prompt_fragments()` raised → `cap` with 0 fix turns.
- `check_type_hints=False` with `implement_final = ("check@standard", "test@quick")` → only `test@quick` runs; the dropped requests are logged.
- `check_type_hints=False` with only check requests → logs "skipped", returns `clean`.
- `load_toolkit` is called once per pass.

`test_check_loop_fix_turns.py` — test `_fix_turn` with `prompt_llm`, `store_session`, `read_and_clear_blocked` patched:
- success, no marker → `None`.
- success with a marker → `blocked` with the reason.
- empty response → `cap`; untyped exception → `cap`.
- `LLMTimeoutError` → `timeout`; `McpServersUnavailableError` → `mcp_unavailable`; with a marker present the status is kept and `detail` is the marker text.
- branch name forwarding (move the useful case from `test_task_processing_branch_name.py`; that file then tests the new module or is reduced accordingly).

`test_task_processing_checks.py` — `process_single_task` with `check_and_fix_mypy` patched:
- `clean` and `cap` → commit, push, `completed`.
- `error` → `TaskOutcome(False, "error", detail)`; no commit.
- `blocked` → `blocked` outcome; no commit.
- `timeout` / `mcp_unavailable` → same reason, detail kept; no commit.
- a marker found in the `finally` after a `clean` result → `blocked`.
- `check_type_hints` is forwarded and `entry="implement_task"`.
Move the four check-gate tests out of `test_task_processing.py` (the `check_type_hints` / binding-empty / binding-error tests around lines 431–620) — they test removed behaviour; delete them. Update `TestIntegration` to patch `check_and_fix_mypy` with `return_value=CheckOutcome("clean")` and assert the new call (`check_type_hints=True`, no `get_binding` patch).

`test_core_final_check.py` — `run_implement_workflow` with one completed task and `check_and_fix_mypy` patched:
- `cap` → `_fail` reason `checks_exhausted`, stage "Final mypy check".
- `error` → `general` with the detail as message.
- `blocked` → `blocked`; a marker read in the `finally` after `clean` → `blocked`.
- `timeout` / `mcp_unavailable` → their reasons, message includes the appended marker text.
- `check_type_hints` from `ImplementConfig` is forwarded.

Existing core tests: replace `return_value=True` with `return_value=CheckOutcome("clean")`; tests that set `side_effect=LLMTimeoutError(...)` become `return_value=CheckOutcome("timeout")`; tests asserting the final check is skipped when `check_type_hints=False` now assert it is called with `check_type_hints=False`.
