# Step 2: Event Log

## References
- **Summary**: `pr_info/steps/summary.md`
- **Issue**: #617 — iCoder initial setup
- **Depends on**: Step 1 (types)

## Goal
Implement the structured event log that records all meaningful actions to an in-memory list and a JSONL file in `logs/`.

## WHERE — Files

### New files
- `src/mcp_coder/icoder/core/event_log.py`
- `tests/icoder/test_event_log.py`

## WHAT — Main Functions and Signatures

### `core/event_log.py`

```python
class EventLog:
    """Structured event log: in-memory list + JSONL file output."""

    def __init__(self, logs_dir: str | Path = "logs") -> None:
        """Initialize event log. Creates JSONL file in logs_dir.
        
        Filename: icoder_<ISO_timestamp>.jsonl
        e.g.: icoder_2026-03-29T14-30-00.jsonl
        """

    def emit(self, event: str, **data: object) -> EventEntry:
        """Record a structured event.
        
        Args:
            event: Event type name (e.g. "input_received")
            **data: Arbitrary key-value pairs for this event
            
        Returns:
            The created EventEntry (with auto-computed timestamp).
        """

    @property
    def entries(self) -> list[EventEntry]:
        """Return copy of all recorded events (for testing/inspection)."""

    def close(self) -> None:
        """Flush and close the JSONL file handle."""
```

## HOW — Integration Points

- Uses `EventEntry` from `core/types.py`
- `t` field = `time.monotonic() - self._start_time` (seconds since session start)
- JSONL line format: `{"t": 0.01, "event": "input_received", "text": "/help"}`
- File created in constructor, one JSON line per `emit()` call
- `logs/` directory created if it doesn't exist (`os.makedirs(exist_ok=True)`)

## ALGORITHM — Core Logic

```
__init__(logs_dir):
    self._start = time.monotonic()
    self._entries = []
    self._file = open(logs_dir / f"icoder_{iso_timestamp()}.jsonl", "a")

emit(event, **data):
    entry = EventEntry(t=monotonic() - self._start, event=event, data=data)
    self._entries.append(entry)
    self._file.write(json.dumps({"t": entry.t, "event": entry.event, **entry.data}) + "\n")
    self._file.flush()
    return entry
```

## DATA — Return Values

- `emit()` returns `EventEntry` with computed `t` and the event name + data
- `entries` property returns `list[EventEntry]` (copy of internal list)
- JSONL file: one JSON object per line, flat keys

## Tests — `tests/icoder/test_event_log.py`

```python
# Test emit records event in memory
def test_emit_records_event(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    log.emit("input_received", text="/help")
    assert len(log.entries) == 1
    assert log.entries[0].event == "input_received"
    assert log.entries[0].data["text"] == "/help"
    log.close()

# Test timestamps are monotonically increasing
def test_timestamps_monotonic(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    log.emit("first")
    log.emit("second")
    assert log.entries[1].t >= log.entries[0].t
    log.close()

# Test JSONL file is written
def test_jsonl_file_written(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    log.emit("input_received", text="hello")
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    lines = jsonl_files[0].read_text().strip().split("\n")
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["event"] == "input_received"
    assert data["text"] == "hello"
    assert "t" in data

# Test JSONL filename format
def test_jsonl_filename_format(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    assert len(jsonl_files) == 1
    name = jsonl_files[0].stem  # e.g. "icoder_2026-03-29T14-30-00"
    assert name.startswith("icoder_")

# Test logs_dir is created if missing
def test_creates_logs_dir(tmp_path):
    new_dir = tmp_path / "subdir" / "logs"
    log = EventLog(logs_dir=new_dir)
    log.emit("test")
    log.close()
    assert new_dir.exists()

# Test multiple events produce multiple JSONL lines
def test_multiple_events_multiple_lines(tmp_path):
    log = EventLog(logs_dir=tmp_path)
    log.emit("first")
    log.emit("second")
    log.emit("third")
    log.close()
    jsonl_files = list(tmp_path.glob("icoder_*.jsonl"))
    lines = jsonl_files[0].read_text().strip().split("\n")
    assert len(lines) == 3
```

## LLM Prompt

```
You are implementing Step 2 of the iCoder TUI feature (#617).
Read pr_info/steps/summary.md for full context, then implement this step.

Tasks:
1. Implement core/event_log.py with the EventLog class
2. Write tests in tests/icoder/test_event_log.py
3. Run pylint, mypy, pytest to verify all checks pass

Key details:
- EventLog uses time.monotonic() for relative timestamps
- JSONL filename: icoder_<ISO_timestamp>.jsonl (e.g. icoder_2026-03-29T14-30-00.jsonl)
- emit() writes one JSON line per call and flushes immediately
- logs_dir is created if missing (os.makedirs exist_ok=True)
- Tests use tmp_path fixture for isolation

Use MCP tools for all file operations. Run all three code quality checks after changes.
```
