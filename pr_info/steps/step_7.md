# Step 7 — `list_icoder_logs()` inventory function

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_7.md`) with strict TDD. Write the tests first
> (use real JSONL fixtures via `tmp_path`), then the implementation.
> Run pylint, pytest, mypy via the mandatory MCP tools. Single commit.

## WHERE

- Create: `src/mcp_coder/icoder/core/log_inventory.py`
- Modify: `src/mcp_coder/icoder/core/types.py` — add `LogSummary` dataclass
- Create tests: `tests/icoder/test_log_inventory.py`

## WHAT

```python
# core/types.py
@dataclass(frozen=True)
class LogSummary:
    path: Path
    timestamp: datetime          # from filename or file mtime
    provider: str | None         # None when session_start absent
    n_turns: int                 # count of input_received events
    first_prompt: str            # truncated to 80 chars; "" if no inputs

# core/log_inventory.py
def list_icoder_logs(
    logs_dir: Path | str,
    provider: str | None = None,
) -> list[LogSummary]:
    """Scan logs_dir for icoder_*.jsonl files. Sorted newest first.

    If provider is given, filters out logs whose session_start.provider
    does not match. Logs without a session_start are included only when
    provider is None.
    """
```

## HOW

- Glob `logs_dir / "icoder_*.jsonl"`.
- For each file, iterate via `iter_events(path)` (Step 1):
  - first event whose `event == "session_start"` → take `provider`.
  - count events whose `event == "input_received"`.
  - first such event → take `text`, truncate to `FIRST_PROMPT_MAX = 80`.
- Timestamp source: parse the filename (`icoder_<ISO>.jsonl`); on
  parse failure fall back to `path.stat().st_mtime`.
- Filter by `provider` argument.
- Sort by `timestamp` descending.

## ALGORITHM

```
list_icoder_logs(logs_dir, provider):
    out = []
    for path in glob("icoder_*.jsonl"):
        ts = parse_iso_from_name(path) or mtime_dt(path)
        prov, turns, first = None, 0, ""
        for ev in iter_events(path):
            if ev["event"] == "session_start":
                prov = ev.get("provider")
            elif ev["event"] == "input_received":
                turns += 1
                if not first:
                    first = (ev.get("text") or "")[:80]
        if provider is not None and prov != provider:
            continue
        out.append(LogSummary(path, ts, prov, turns, first))
    out.sort(key=lambda s: s.timestamp, reverse=True)
    return out
```

## DATA

- `LogSummary` dataclass (frozen, hashable).
- Module-level constant `FIRST_PROMPT_MAX = 80`.

## Test Cases

1. Empty `logs_dir` → `[]`.
2. One log with `session_start{provider="claude"}`, two `input_received`
   events ("hello world", "second") → returned `LogSummary` has
   `provider="claude"`, `n_turns=2`, `first_prompt="hello world"`.
3. First prompt longer than 80 chars → truncated to first 80 chars.
4. Two logs in different files; provider filter `"claude"` excludes the
   `"langchain"` one; the `"claude"` one is returned.
5. Filename `icoder_2026-05-01T10-00-00.jsonl` and another
   `icoder_2026-05-02T10-00-00.jsonl` → sorted newest first regardless
   of OS-listing order.
6. Log with no `session_start` and no `input_received` → still listed
   (with `provider=None`, `n_turns=0`, `first_prompt=""`) when
   `provider is None`; excluded when `provider="claude"`.
7. Log with corrupt JSON line — `iter_events` raises; the function lets
   it propagate (no swallowing). (Verify behaviour matches.)
8. Slash command counts as a turn (`first_prompt` may be `"/help"`) —
   the function does no special-casing.

## Out of Scope

- UI rendering — Step 9.
- Provider resolution from CLI — already done in Step 11 wiring.
