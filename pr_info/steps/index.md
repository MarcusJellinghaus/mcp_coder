# Implementation Steps Index

## Issue #400: Fix vscodeclaude Status Display, Cleanup Order, and Blocked Issue Handling

### Overview Documents
- [summary.md](summary.md) - Architecture changes, file list, design decisions
- [Decisions.md](Decisions.md) - Decisions log from plan review discussion

### Implementation Steps (TDD Order)

| Step | File | Description | Est. Lines |
|------|------|-------------|------------|
| [Step 1](step_1.md) | `labels.json`, `issues.py` | Config + ignore-label helpers | ~20 |
| [Step 2](step_2.md) | `sessions.py` | Session status update helper | ~10 |
| [Step 3](step_3.md) | `status.py` | `get_next_action()` blocked support | ~10 |
| [Step 4](step_4.md) | `cleanup.py`, `commands.py` | Cleanup order + blocked in cleanup | ~30 |
| [Step 5](step_5.md) | `orchestrator.py` | Skip blocked in restart, update status | ~20 |
| [Step 6](step_6.md) | `commands.py` | Status command display fixes | ~40 |

**Total estimated: ~130 lines of new/modified code**

### Dependency Graph

```
Step 1 (helpers) 
    ↓
Step 2 (session update)
    ↓
Step 3 (get_next_action)
    ↓
Step 4 (cleanup) ←── uses Step 1 helpers
    ↓
Step 5 (restart) ←── uses Step 1, 2 helpers
    ↓
Step 6 (status) ←── uses Step 1, 2, 3
```

### Files Modified

**Source Files:**
- `src/mcp_coder/config/labels.json`
- `src/mcp_coder/workflows/vscodeclaude/issues.py`
- `src/mcp_coder/workflows/vscodeclaude/sessions.py`
- `src/mcp_coder/workflows/vscodeclaude/status.py`
- `src/mcp_coder/workflows/vscodeclaude/cleanup.py`
- `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py`

**Test Files:**
- `tests/workflows/vscodeclaude/test_issues.py`
- `tests/workflows/vscodeclaude/test_sessions.py`
- `tests/workflows/vscodeclaude/test_status.py`
- `tests/workflows/vscodeclaude/test_cleanup.py`
- `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`
- `tests/cli/commands/coordinator/test_commands.py`

### Quick Reference: New Functions

```python
# issues.py
def get_ignore_labels() -> set[str]: ...
def get_matching_ignore_label(issue_labels: list[str], ignore_labels: set[str]) -> str | None: ...

# sessions.py  
def update_session_status(folder: str, new_status: str) -> bool: ...

# status.py (modified)
def get_next_action(..., blocked_label: str | None = None) -> str: ...
```
