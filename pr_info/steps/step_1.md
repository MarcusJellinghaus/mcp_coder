# Step 1: TokenUsage Dataclass + format_token_count()

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #808).

## Goal

Add the `TokenUsage` dataclass and `format_token_count()` helper to `icoder/core/types.py` with full test coverage. This is the foundational data layer — no UI or AppCore changes yet.

## LLM Prompt

```
Implement Step 1 of Issue #808 (see pr_info/steps/summary.md for context).

Add `TokenUsage` dataclass and `format_token_count()` to `src/mcp_coder/icoder/core/types.py`.
Add tests to `tests/icoder/test_types.py`.
Follow TDD: write tests first, then implementation.
Run all three code quality checks after changes.
```

## WHERE

- **Modify**: `src/mcp_coder/icoder/core/types.py`
- **Modify**: `tests/icoder/test_types.py`

## WHAT

### `format_token_count(n: int) -> str`

Module-level helper. Compact token formatting.

**Signature**:
```python
def format_token_count(n: int) -> str:
    """Format token count with compact suffix (k/M)."""
```

### `TokenUsage` dataclass

Mutable dataclass tracking last-request and cumulative token counts.

**Signature**:
```python
@dataclass
class TokenUsage:
    last_input: int = 0
    last_output: int = 0
    total_input: int = 0
    total_output: int = 0
    _ever_updated: bool = field(default=False, repr=False)

    def update(self, input_tokens: int, output_tokens: int) -> None: ...
    def display_text(self) -> str: ...

    @property
    def has_data(self) -> bool: ...
```

## HOW

- Add to existing `types.py` alongside `Response`, `Command`, `EventEntry`
- `_ever_updated` uses `field(default=False, repr=False)` to keep it internal
- No new imports needed beyond what's already in `types.py`

## ALGORITHM

### `format_token_count(n)`
```
if n < 1000:        return str(n)           # "0", "999"
if n < 1_000_000:
    k = n / 1000
    if k < 9.95:    return f"{k:.1f}k"      # "1.2k" .. "9.9k"
    else:           return f"{round(k)}k"   # "10k", "123k"
if n < 1_000_000_000:
    m = n / 1_000_000
    if m < 9.95:    return f"{m:.1f}M"      # "1.2M" .. "9.9M"
    else:           return f"{round(m)}M"   # "10M", "123M"
return f"{n // 1_000_000_000}B"
```

> **Boundary note**: The threshold `9.95` ensures that values which round to 10.0
> at one decimal place (e.g., 9999 → 9.999 → "10.0k") use the integer path instead.
> `round(k)` is used instead of `int(k)` so that 9999 → `round(9.999)` = `10` → `"10k"`.

### `TokenUsage.update(input_tokens, output_tokens)`
```
self.last_input = input_tokens
self.last_output = output_tokens
self.total_input += input_tokens
self.total_output += output_tokens
self._ever_updated = True
```

### `TokenUsage.display_text()`
```
last = f"↓{format_token_count(self.last_input)} ↑{format_token_count(self.last_output)}"
total = f"↓{format_token_count(self.total_input)} ↑{format_token_count(self.total_output)}"
return f"{last} | total: {total}"
```

### `TokenUsage.has_data`
```
return self._ever_updated and (self.total_input > 0 or self.total_output > 0)
```

## DATA

- `format_token_count(0)` → `"0"`
- `format_token_count(999)` → `"999"`
- `format_token_count(1000)` → `"1.0k"`
- `format_token_count(1200)` → `"1.2k"`
- `format_token_count(9999)` → `"10k"` (9999/1000 = 9.999, which is ≥ 9.95 so uses integer path: `round(9.999)` = `10` → `"10k"`)
- `format_token_count(10000)` → `"10k"`
- `format_token_count(123456)` → `"123k"`
- `format_token_count(999999)` → `"999k"`
- `format_token_count(1000000)` → `"1.0M"`
- `format_token_count(1200000)` → `"1.2M"`
- `format_token_count(12000000)` → `"12M"`

### Tests to write (in `test_types.py`)

1. `test_format_token_count_zero` — `0` → `"0"`
2. `test_format_token_count_small` — `999` → `"999"`
3. `test_format_token_count_k_range` — parametrize `(1200, "1.2k"), (5400, "5.4k"), (9949, "9.9k"), (9999, "10k"), (10000, "10k"), (123456, "123k")`
4. `test_format_token_count_m_range` — parametrize `(1_000_000, "1.0M"), (1_200_000, "1.2M"), (9_949_999, "9.9M"), (9_999_999, "10M"), (12_000_000, "12M")`
5. `test_token_usage_initial_state` — all zeros, `has_data` is False, `display_text()` returns `"↓0 ↑0 | total: ↓0 ↑0"`
6. `test_token_usage_single_update` — update(100, 50) → last and total match, `has_data` True
7. `test_token_usage_cumulative` — two updates accumulate totals, last reflects most recent
8. `test_token_usage_has_data_false_after_zero_update` — update(0, 0) → `_ever_updated` True but `has_data` False
9. `test_token_usage_display_text` — after update(1200, 800) → `"↓1.2k ↑800 | total: ↓1.2k ↑800"`
