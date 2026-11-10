# Step 3 — Launch grace also covers restarts (`restarted_at`)

## LLM prompt

> Read `pr_info/steps/summary.md` and this file (`pr_info/steps/step_3.md`), then implement Step 3 only. Add `restarted_at` to the session, record it on restart through `update_session_pid`, and measure session age and grace from the later of `started_at` and `restarted_at`. Write the tests first, then the implementation. Run the checks from the summary, then make one commit.

## Rationale

`restart_closed_sessions` does not reset `started_at`, so a restarted session is never within grace. Once the title becomes authoritative (Step 4), the not-yet-drawn window would count as an authoritative miss. `started_at` keeps its meaning (original launch).

## WHERE / WHAT

**`src/mcp_coder/workflows/vscodeclaude/types.py`**
```python
from typing import Any, NotRequired, TypedDict

class VSCodeClaudeSession(TypedDict):
    ...
    restarted_at: NotRequired[str]  # ISO 8601 UTC, set on each restart
```
Do **not** add a `setdefault` for it in `load_sessions`.

**`src/mcp_coder/workflows/vscodeclaude/sessions.py`**
```python
def update_session_pid(folder: str, pid: int, *, restarted_at: str | None = None) -> None:
```
- In the same loop and the same `save_sessions` call: `if restarted_at is not None: session["restarted_at"] = restarted_at`.
- Docstring: document the argument. Existing callers are unaffected.

**`src/mcp_coder/workflows/vscodeclaude/session_restart.py`**
- `update_session_pid(session["folder"], new_pid, restarted_at=datetime.now(UTC).isoformat())`.
- Add `from datetime import UTC, datetime`. This is the same format as `started_at` in `helpers.py`.

**`src/mcp_coder/workflows/vscodeclaude/detection.py`**
- `_session_age_seconds(session, now) -> float`: age since the later of `started_at` / `restarted_at`, or `inf` if neither is usable. `within_grace` already derives from `age_seconds` in `gather_signals`, so no change is needed there.

## ALGORITHM

```
def _age_since(timestamp, now) -> float:
    try: return (now - datetime.fromisoformat(timestamp)).total_seconds()
    except (ValueError, TypeError): return inf      # None, garbage, naive-vs-aware mismatch
return min(_age_since(session.get("started_at"), now),
           _age_since(session.get("restarted_at"), now))
```

- `_age_since` is a private helper next to `_session_age_seconds`.
- Taking the smaller *age* (not comparing datetimes) avoids `TypeError` on mixed naive/aware values.
- Absent or unparsable `restarted_at` is ignored.
- A valid `restarted_at` wins when `started_at` is unparsable.
- Update the docstring accordingly.

## Tests (write first)

**`test_detection.py`** (`gather_signals` with a fixed `snapshot.captured_at`; pin `HAS_WIN32GUI`):
- old `started_at` + `restarted_at` 10 s before `captured_at` → `age_seconds ≈ 10`, `within_grace is True`
- no `restarted_at` → unchanged behaviour (age from `started_at`)
- unparsable `restarted_at` → age from `started_at`
- unparsable `started_at` + valid recent `restarted_at` → small age, within grace
- naive `started_at` (as in `conftest.make_session`) + aware `restarted_at` → no exception, age from `restarted_at`

**`test_sessions_pid_identity.py`** (or wherever `update_session_pid` is tested):
- `update_session_pid(folder, pid, restarted_at="…")` writes `restarted_at` and the PID in one save.
- Without the kwarg, no `restarted_at` key is written.

**`test_session_restart_closed_sessions.py`**:
- In an existing successful-restart test, assert `update_session_pid` was called with a `restarted_at` kwarg.
- That value must parse with `datetime.fromisoformat` and have `tzinfo` equal to UTC offset 0.

## Commit

`feat(vscodeclaude): apply launch grace after session restart`
