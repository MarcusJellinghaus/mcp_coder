# Step 7 — Trust negative title result after launch grace (Item #3)

## LLM Prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_7.md`) in
> full. Steps 1 (PID-bound titles) and 2 (`create_time` identity) are
> prerequisites — without them this change would regress legitimately-running
> sessions. Follow TDD. One commit at the end.

## Goal

Remove the second-chance acceptance path that lets ghost PIDs and unrelated
cmdlines override a clean negative title signal. For sessions older than the
60s launch grace, a negative title match is authoritative. Within the grace
window, fall through to today's PID + cmdline chain — covers VSCode
cold-start and extension reinstalls.

## WHERE

- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `tests/workflows/vscodeclaude/test_sessions.py`

## WHAT — function signatures

```python
# sessions.py — module-level constant
LAUNCH_GRACE_SECONDS = 60.0

# is_session_active signature unchanged
def is_session_active(session: VSCodeClaudeSession) -> bool: ...
```

## HOW — integration points

Inside `is_session_active`, the Windows-with-issue title block becomes
conditional on session age:

```python
if HAS_WIN32GUI and issue_num is not None and repo is not None:
    started_at_str = session.get("started_at", "")
    try:
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(started_at_str)).total_seconds()
    except (ValueError, TypeError):
        age = float("inf")  # malformed timestamp → treat as established

    if age >= LAUNCH_GRACE_SECONDS:
        if is_vscode_window_open_for_folder(folder, issue_number=issue_num, repo=repo):
            logger.info("is_session_active #%s: active (window-title match)", issue_num)
            return True
        logger.info(
            "is_session_active #%s: inactive (no title match, age=%.0fs)",
            issue_num, age,
        )
        return False
    logger.debug(
        "is_session_active #%s: within launch grace (age=%.0fs), using fallback chain",
        issue_num, age,
    )
    # fall through to existing PID + cmdline checks (today's behavior)
```

The existing PID + cmdline fallback path is kept verbatim for:
- non-Windows (`HAS_WIN32GUI is False`),
- sessions missing `issue_number` or `repo`,
- sessions still inside the launch grace window.

## ALGORITHM

```
age = compute_age_seconds(session["started_at"])  # +inf on parse error
if windows and issue_num and repo:
    if age >= 60.0:
        return is_vscode_window_open_for_folder(...)
    # else: fall through to fallback chain
# fallback chain (unchanged):
if check_vscode_running(stored_pid, create_time):
    return True
is_open, found_pid = is_vscode_open_for_folder(folder)
if is_open: ... return True
return False
```

## DATA

- `LAUNCH_GRACE_SECONDS: float = 60.0` (module constant).
- `age: float` — seconds since `started_at`; `inf` on parse error.
- Return: `bool` (unchanged).

## Tests (write first)

In `tests/workflows/vscodeclaude/test_sessions.py`:

1. **Established + no title → False**: Windows path, session age 120s, title
   check returns `False`. Stored PID alive, cmdline match exists. Expect
   `is_session_active` returns `False`.
2. **Grace + no title + cmdline match → True**: age 10s, title check `False`,
   cmdline match exists. Expect `True`.
3. **Established + title match → True**: age 120s, title check `True` →
   `True` (no fallback queried).
4. **Malformed `started_at`**: `session["started_at"] = "not-a-date"` → age
   treated as `inf` → established branch (title authoritative).
5. **Non-Windows path unaffected**: monkeypatch `HAS_WIN32GUI=False` →
   fallback chain runs regardless of age.

For tests 1–4, freeze `datetime.now(timezone.utc)` to a fixed value and set
`session["started_at"]` relative to it.

## Done when

- All tests pass.
- mypy, pylint clean.
- One commit: tests + implementation.
