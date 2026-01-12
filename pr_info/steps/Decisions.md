# Decisions Log

## Decision 1: Extra Fields Console Output Format

**Discussion**: What format to use when appending extra fields to console log messages.

**Options Considered**:
- A: JSON array of objects `[{"key": "value"}, ...]`
- B: Single JSON object `{"key": "value", "count": 42}`
- C: Hybrid format `[{key="value"}, ...]`

**Decision**: **Option B - Single JSON object using `json.dumps()`**

**Rationale**: 
- Simplest to implement (just `json.dumps(extra_dict)`)
- Automatic type handling (strings quoted, numbers unquoted, bools as true/false)
- Standard JSON format

**Example Output**:
```
2024-01-15 10:30:00 - module - INFO - Action performed {"user_id": "123", "count": 42, "enabled": true}
```

---

## Decision 2: log_function_call Decorator

**Discussion**: Whether to convert the `log_function_call` decorator in `log_utils.py` from structlog to standard logging.

**Options Considered**:
- A: Leave as-is (decorator stays in log_utils.py which is allowed to use structlog)
- B: Convert to standard logging with `extra={}` for consistency

**Decision**: **Option A - Leave as-is**

**Rationale**: The decorator resides in `log_utils.py`, which is the designated module for structlog usage. No change needed.

---

## Decision 3: Fix Pre-existing Numbering Bug

**Discussion**: The search result logging in `data_files.py` has inconsistent method numbering (e.g., "2/4 ImportLib" should be "2/5 ImportLib").

**Options Considered**:
- A: Fix the numbering to `/5` while converting to standard logging
- B: Leave numbering as-is, only change logging mechanism

**Decision**: **Option A - Fix numbering during refactor**

**Rationale**: Since we're touching all log calls anyway, fix the inconsistency for correctness.

---

## Decision 4: Log Merging Policy

**Discussion**: How aggressive should log call merging be when converting from structlog to standard logging.

**Options Considered**:
- A: No merging at all - convert each call 1:1 mechanically
- B: Merge only identical messages that are literally adjacent lines
- C: Merge where "obviously cleaner" using implementer judgment

**Decision**: **Option B - Merge only identical messages on adjacent lines**

**Rationale**: Clear criteria with minimal risk. Preserves debuggability while allowing obvious improvements.

---

## Decision 5: Empty Extra Dict Handling

**Discussion**: What should the console output show when `extra={}` (empty dict) is passed.

**Options Considered**:
- A: Show nothing (no suffix)
- B: Show empty object `{}`

**Decision**: **Option A - Show nothing**

**Rationale**: Cleaner output, avoids visual noise for empty extra dicts.

---

## Decision 6: Non-JSON-Serializable Values

**Discussion**: How to handle extra fields containing values that `json.dumps()` can't serialize (e.g., `Path` objects).

**Options Considered**:
- A: Auto-convert with `str()` via custom JSON encoder
- B: Let it fail (catches bugs early)
- C: Fallback to `repr()` for the whole dict

**Decision**: **Option A - Auto-convert with `str()`**

**Rationale**: Most user-friendly approach, prevents logging from ever crashing at runtime.
