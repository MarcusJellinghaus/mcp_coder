# Step 1: Rename method, add SSH guard, update message and unit tests

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #792

## LLM Prompt
> Implement step 1 of `pr_info/steps/summary.md`. Rename `_check_ssh_dumb_terminal` to `_check_ssh_terminal_capabilities` in `src/mcp_coder/utils/tui_preparation.py`, add an early return when `SSH_CONNECTION` is not set, update the warning message to prefix with "SSH", update the caller in `run_all_checks`, and update all unit tests in `TestCheckSshDumbTerminal` to match. Run all code quality checks (pylint, mypy, pytest) and fix any issues before committing.

## WHERE
- `src/mcp_coder/utils/tui_preparation.py` — method rename + logic change
- `tests/utils/test_tui_preparation.py` — `TestCheckSshDumbTerminal` class

## WHAT

### Source: `_check_ssh_terminal_capabilities(self) -> None`
Renamed from `_check_ssh_dumb_terminal`. Same signature.

### Caller: `run_all_checks(self) -> None`
Update call from `self._check_ssh_dumb_terminal()` → `self._check_ssh_terminal_capabilities()`.

### Tests updated:
- `TestCheckSshDumbTerminal` → `TestCheckSshTerminalCapabilities`
- `test_check_ssh_dumb_terminal_detected` → `test_warns_when_ssh_and_term_dumb` — sets `SSH_CONNECTION`
- `test_check_ssh_dumb_terminal_unset` → `test_warns_when_ssh_and_term_unset` — sets `SSH_CONNECTION`
- `test_check_ssh_dumb_terminal_ok` → `test_no_warning_when_ssh_and_term_ok` — sets `SSH_CONNECTION`
- **New**: `test_no_warning_when_not_ssh` — sets `TERM=dumb`, no `SSH_CONNECTION`, expects 0 warnings

## HOW
- Method is called from `run_all_checks` — just update the name there.
- Tests call the method directly — update all references.

## ALGORITHM (updated method)
```
def _check_ssh_terminal_capabilities(self):
    if not os.environ.get("SSH_CONNECTION"):
        return
    term = os.environ.get("TERM")
    if term is None or term == "dumb":
        self._warnings.append("SSH terminal type is 'dumb' or unset — ...")
```

## DATA
- No change to return values or data structures. Method appends to `self._warnings` list as before.
- Warning message changes from `"Terminal type is 'dumb'..."` to `"SSH terminal type is 'dumb'..."`.

## Commit
```
fix: suppress false TERM warning on non-SSH terminals (#792)

- Rename _check_ssh_dumb_terminal → _check_ssh_terminal_capabilities
- Guard: return early if SSH_CONNECTION is not set
- Update warning message to prefix with "SSH"
- Update unit tests for renamed method and SSH guard
```
