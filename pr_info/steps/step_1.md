# Step 1: Add `UsageInfo` TypedDict to `llm/types.py`

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 1 of 5.

## LLM Prompt

```
Implement step 1 of issue #819 (pr_info/steps/summary.md).
Add the UsageInfo TypedDict to llm/types.py, export it in __all__ and llm/__init__.py.
Write tests first (TDD), then implement. Run all three checks after.
```

## WHERE

- **Modify**: `src/mcp_coder/llm/types.py`
- **Modify**: `src/mcp_coder/llm/__init__.py`
- **Modify**: `tests/llm/test_types.py`

## WHAT

### `src/mcp_coder/llm/types.py` — new TypedDict

```python
class UsageInfo(TypedDict, total=False):
    """Provider-agnostic token usage. All fields optional (total=False)."""
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
```

- Add `"UsageInfo"` to existing `__all__` list
- `total=False` because not every provider supplies every field

### `src/mcp_coder/llm/__init__.py` — re-export

- Add `UsageInfo` to the import from `mcp_coder.llm.types`
- Add `"UsageInfo"` to `__all__`

## HOW

- `UsageInfo` is a plain `TypedDict` — no runtime behavior, just a type contract
- Existing `StreamEvent` is `dict[str, object]` so it can carry `UsageInfo` in the `"usage"` key without changes

## DATA

```python
# Example usage (already works with Claude CLI done events):
usage: UsageInfo = {
    "input_tokens": 1200,
    "output_tokens": 800,
    "cache_read_input_tokens": 540,
}
# cache_creation_input_tokens omitted — total=False allows this
```

## TESTS (`tests/llm/test_types.py`)

Add these tests:

1. **`test_usage_info_is_typed_dict`** — verify `UsageInfo` is a `TypedDict` subclass
2. **`test_usage_info_fields`** — verify all 4 field names exist with `int` type via `get_type_hints()`
3. **`test_usage_info_total_false`** — verify all fields are optional (`total=False`): create `UsageInfo` with only `input_tokens` set, confirm it's valid
4. **`test_usage_info_importable_from_llm_package`** — `from mcp_coder.llm import UsageInfo` works

## COMMIT

```
feat(llm): add UsageInfo TypedDict for provider-agnostic token usage (#819)
```
