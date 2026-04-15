# Step 2: Add cache tracking to `TokenUsage` + display

> **Context**: See `pr_info/steps/summary.md` for full issue context. This is step 2 of 5.

## LLM Prompt

```
Implement step 2 of issue #819 (pr_info/steps/summary.md).
Add cache_read fields to TokenUsage dataclass and update display_text() to show cache%.
Write tests first (TDD), then implement. Run all three checks after.
```

## WHERE

- **Modify**: `src/mcp_coder/icoder/core/types.py`
- **Modify**: `tests/icoder/test_types.py`

## WHAT

### `TokenUsage` dataclass changes

Add two new fields:
```python
last_cache_read: int = 0
total_cache_read: int = 0
```

Update `update()` signature:
```python
def update(self, input_tokens: int, output_tokens: int, cache_read_input_tokens: int = 0) -> None:
```

Update `display_text()` to append `cache:XX%` when cache data exists.

## ALGORITHM — `update()`

```
self.last_cache_read = cache_read_input_tokens
self.total_cache_read += cache_read_input_tokens
# (existing input/output logic unchanged)
```

## ALGORITHM — `display_text()`

```
last = "↓{input} ↑{output}"
if last_input > 0 and last_cache_read > 0:
    last += " cache:{pct}%"  where pct = round(last_cache_read / last_input * 100)
total = "↓{input} ↑{output}"
if total_input > 0 and total_cache_read > 0:
    total += " cache:{pct}%"  where pct = round(total_cache_read / total_input * 100)
return f"{last} | total: {total}"
```

## DATA

```python
# With cache:
"↓1.2k ↑800 cache:45% | total: ↓5k ↑3k cache:52%"

# Without cache (cache_read_input_tokens=0 or not provided):
"↓1.2k ↑800 | total: ↓5k ↑3k"
```

## TESTS (`tests/icoder/test_types.py`)

Add these tests:

1. **`test_token_usage_update_with_cache`** — call `update(1000, 500, cache_read_input_tokens=450)`, verify `last_cache_read=450`, `total_cache_read=450`
2. **`test_token_usage_cumulative_cache`** — two updates with cache, verify totals sum correctly
3. **`test_token_usage_display_text_with_cache`** — `update(1200, 800, 540)` → display contains `cache:45%` for both last and total sections
4. **`test_token_usage_display_text_without_cache`** — `update(1200, 800)` → display does NOT contain `cache:` (backward compat)
5. **`test_token_usage_display_text_mixed_cache`** — first update without cache, second with cache → last section has cache%, total section has cache% (based on totals)
6. **`test_token_usage_cache_percentage_rounding`** — verify rounding: `update(1000, 500, 333)` → `cache:33%`

## COMMIT

```
feat(icoder): add cache tracking to TokenUsage display (#819)
```
