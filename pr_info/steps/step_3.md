# Step 3: New fix loop in `check_loop.py` with a shared cap

Adds the grouped, capped loop returning `CheckOutcome`, with its own unit tests. The old `check_and_fix_mypy` in `task_processing.py` and both callers stay unchanged in this step; step 4 switches the callers and deletes the old code.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement step 3 only. Write the tests in `tests/workflows/implement/test_check_loop.py` and `test_check_loop_fix_turns.py` first, then create `check_loop.py` and move `_build_fix_prompt` / `_CHECK_OUTPUT_HEADING` there. Do not change `process_single_task`, `core.py` or the old `check_and_fix_mypy` in `task_processing.py` beyond the import of `_build_fix_prompt`. Run pylint, mypy and the fast pytest suite; all must pass. Format, then make one commit.

## WHERE
- Create `src/mcp_coder/workflows/implement/check_loop.py`.
- Modify `src/mcp_coder/workflows/implement/task_processing.py` (import `_build_fix_prompt` from `.check_loop` only).
- Tests: create `tests/workflows/implement/test_check_loop.py`, `tests/workflows/implement/test_check_loop_fix_turns.py`.

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
    fragment: str, fix_text: str, project_dir: Path, provider: str, turn: int,
    step_num: int, env_vars, mcp_config, settings_file,
) -> CheckOutcome | None:
    """One LLM fix turn: compute the grants and check instructions, build the
    prompt, call the LLM. None when the turn went through; otherwise the
    outcome that ends the loop. Never raises."""

def _build_fix_prompt(fix_fragment: str, fix_text: str, check_instructions: str) -> str:
    """Moved unchanged from task_processing (heading "Check output:")."""
```

## HOW
- Move `_build_fix_prompt` and `_CHECK_OUTPUT_HEADING` from `task_processing.py` to `check_loop.py`; `task_processing.py` imports `_build_fix_prompt` from `.check_loop` so its old `check_and_fix_mypy` keeps working until step 4. `check_loop.py` must not import `task_processing` (step 4 makes `task_processing` import `check_loop`).
- `check_loop.py` imports: `load_toolkit`, `run_request`, `get_fragment`, `llm_permissions`, `bash_grants_of`, `LoadedToolkit` from `mcp_coder.utils.toolkit_runner`; `resolve_prompt_slots`, `toolkit_declares_bash_grants` from `mcp_coder.utils.prompt_slots`; `prompt_llm`, `LLMTimeoutError` from `mcp_coder.llm.interface`; `McpServersUnavailableError`; `llm_failure_reason`; `store_session`; `get_branch_name_for_logging`; `read_and_clear_blocked` from `.blocked`; `LLM_INACTIVITY_TIMEOUT_SECONDS` from `.constants`.
- `get_fragment` already returns the raw fragment, or `""` when missing or when `prompt_fragments()` raises. A falsy fragment counts as missing.
- `bash_grants` and `check_instructions` are computed inside `_fix_turn`, under its catch-all (see rules): `bash_grants = bash_grants_of(llm_permissions(project_dir, provider))`; `check_instructions` is the filled `[check_instructions]` slot when `toolkit_declares_bash_grants(project_dir)`, else `""`. Recomputing them per turn is cheap and keeps every exception inside `_fix_turn`.
- Session step name stays `f"step_{step_num}_mypy_{turn}"`.

### `_fix_turn` rules
One `try` covers the grant / instruction computation, `_build_fix_prompt` and `prompt_llm`:
- `LLMTimeoutError` / `McpServersUnavailableError` → `blocked = read_and_clear_blocked(...)`; return `CheckOutcome(llm_failure_reason(e) or "timeout", blocked or "")`.
- Any other exception (including from `llm_permissions`, `toolkit_declares_bash_grants` or `resolve_prompt_slots`), or an empty / whitespace response → `read_and_clear_blocked`; if it returned a reason, return `blocked` with it, else return `CheckOutcome("cap", "Fix turn failed: <short reason>")`. Use `# pylint: disable=broad-exception-caught`.
- Success: store the session (failures logged, as today), then `blocked = read_and_clear_blocked(...)`; return `CheckOutcome("blocked", blocked)` if set, else `None`.

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
    turn += 1
    ended = _fix_turn(fragment, text, dir, provider, turn, ...)   # never raises
    if ended: return ended
```

## DATA
- `CheckOutcome(status, detail)` as above.

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
- `_fix_turn` returning `cap` / `blocked` / `timeout` ends the loop with that outcome.
- `check_type_hints=False` with `implement_final = ("check@standard", "test@quick")` → only `test@quick` runs; the dropped requests are logged.
- `check_type_hints=False` with only check requests → logs "skipped", returns `clean`.
- `load_toolkit` is called once per pass.

`test_check_loop_fix_turns.py` — test `_fix_turn` with `prompt_llm`, `store_session`, `read_and_clear_blocked`, `llm_permissions`, `toolkit_declares_bash_grants` and `resolve_prompt_slots` patched in `check_loop`:
- success, no marker → `None`.
- success with a marker → `blocked` with the reason.
- empty response → `cap`; untyped exception from `prompt_llm` → `cap`.
- `llm_permissions`, `toolkit_declares_bash_grants` or `resolve_prompt_slots` raising → `cap`, `prompt_llm` not called, nothing raised (parametrised).
- `LLMTimeoutError` → `timeout`; `McpServersUnavailableError` → `mcp_unavailable`; with a marker present the status is kept and `detail` is the marker text.
- bash grants and filled `check_instructions` reach `prompt_llm` / the prompt when the toolkit declares Bash grants.
- branch name is forwarded to `prompt_llm` and `store_session`.

These tests call `check_loop` directly, so step 4's conftest fixture (which patches `task_processing.check_and_fix_mypy`) does not affect them.
