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
