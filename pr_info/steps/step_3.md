# Step 3: Fix Vulture Warning

## LLM Prompt

```
Read pr_info/steps/summary.md for context. Implement Step 3: Fix the vulture warning for __getattr__ in workflow_utils/__init__.py.

This step adds a whitelist entry for the lazy import pattern that vulture cannot detect.
```

## WHERE: File Paths

- `vulture_whitelist.py`

## WHAT: Changes Required

### Add Whitelist Entry

Vulture reports:
```
src/mcp_coder/workflow_utils/__init__.py:49: unused function '__getattr__' (60% confidence)
```

The `__getattr__` function is used for lazy imports to avoid circular dependencies. Python calls it implicitly when an attribute is not found, so vulture cannot detect its usage.

### Current `__getattr__` Function

```python
def __getattr__(name: str) -> Any:
    """Lazy import for commit_operations to avoid circular imports."""
    if name in (
        "generate_commit_message_with_llm",
        "parse_llm_commit_response",
        "strip_claude_footers",
    ):
        from . import commit_operations
        return getattr(commit_operations, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

## HOW: Whitelist Format

Check existing `vulture_whitelist.py` format and add:

```python
# workflow_utils/__init__.py - lazy import pattern
__getattr__  # Used by Python for lazy imports
```

Or if the whitelist uses a different format:

```python
from mcp_coder.workflow_utils import __getattr__  # noqa: F401
```

## ALGORITHM: N/A

This is a configuration change, not logic.

## DATA: N/A

No data structures involved.

## Success Criteria

- [ ] `vulture_whitelist.py` updated
- [ ] `vulture` check passes (no unused code warnings)
