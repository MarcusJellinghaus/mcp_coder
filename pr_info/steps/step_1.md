# Step 1 — EventLog: `current_path`, `rotate()`, `iter_events()`

## LLM Prompt

> Read `pr_info/steps/summary.md` for context, then implement this step
> (`pr_info/steps/step_1.md`) with strict TDD. Write the tests in
> `tests/icoder/test_event_log.py` first; then add the minimal code in
> `src/mcp_coder/icoder/core/event_log.py` to make them pass. Run
> `pylint`, `pytest -m "not <integration markers>"`, and `mypy` (all via the
> mandatory MCP tools) and ensure all pass before producing the single
> commit for this step. Do not change behaviour outside what this step
> specifies.

## WHERE

- Modify: `src/mcp_coder/icoder/core/event_log.py`
- Add tests to: `tests/icoder/test_event_log.py`

## WHAT

```python
class EventLog:
    @property
    def current_path(self) -> Path: ...

    def rotate(self) -> Path:
        """Close current JSONL file, open a fresh one with new timestamp.

        Resets monotonic clock and clears in-memory entries. Returns the
        new file path. Subsequent emit() calls write to the new file.
        """

# module-level
def iter_events(path: Path | str) -> Iterator[dict[str, Any]]:
    """Yield each JSONL event as a dict. Skips blank lines.

    Raises FileNotFoundError if path does not exist.
    Raises json.JSONDecodeError on malformed lines (no swallowing).
    """
```

## HOW

- Track the active file path as `self._path: Path` set in `__init__` and
  updated by `rotate()`.
- `current_path` is a simple property returning `self._path`.
- `rotate()`:
  1. flushes + closes the current handle,
  2. computes a new ISO timestamp filename in the same `logs_dir`,
  3. opens the new file in append mode,
  4. sets `self._start = time.monotonic()`,
  5. clears `self._entries`,
  6. updates `self._path`,
  7. returns the new path.
- Keep `__exit__` working with the (possibly rotated) handle.

## ALGORITHM

```
rotate():
    self._file.flush(); self._file.close()
    new_name = f"icoder_{utc_iso_timestamp()}.jsonl"
    new_path = logs_dir / new_name
    self._file = open(new_path, "a", encoding="utf-8")
    self._start = time.monotonic()
    self._entries.clear()
    self._path = new_path
    return new_path

iter_events(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
```

## DATA

- `EventLog.current_path` → `Path`
- `EventLog.rotate()` → new `Path`
- `iter_events(path)` → `Iterator[dict[str, Any]]`

## Test Cases

1. `current_path` exposes the file `__init__` opened (matches the single
   file written by `glob("icoder_*.jsonl")`).
2. After `rotate()`, `current_path` differs from the prior path.
3. After `rotate()`, both files exist on disk.
4. After `rotate()`, the old file handle is closed (writing through the
   internal handle goes to the new file; assert via `emit()` then read
   both files).
5. After `rotate()`, `entries` is empty and the next emit's `t` is small
   (≈0) — i.e. the monotonic clock was reset.
6. `iter_events(path)` returns a list matching the JSONL contents (event
   types and data).
7. `iter_events` skips blank lines.
8. `iter_events` raises `FileNotFoundError` for a missing path.

## Out of Scope

- No callers updated yet. (Other steps wire this up.)
- No changes to filename format beyond reusing the existing pattern.
