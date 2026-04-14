# Issue #808: iCoder Token Usage + Version in Status Line

## Summary

Repurpose the `#input-hint` status line at the bottom of the iCoder TUI into a permanent three-zone status bar showing token usage (left), mcp-coder version (center), and the input hint (right). Token counts update after each LLM stream completes using a pull model.

## Architecture / Design Changes

### New: `TokenUsage` dataclass in core layer (`icoder/core/types.py`)

- Mutable dataclass tracking `last_input`, `last_output`, `total_input`, `total_output` (all `int`)
- `update(input_tokens, output_tokens)` sets last-request values and accumulates totals
- `display_text() -> str` builds the formatted string `↓1.2k ↑0.8k | total: ↓5.4k ↑3.1k`
- Module-level `format_token_count(n: int) -> str` helper for compact suffix logic
- Session-scoped (resets on app restart)

### Modified: `AppCore` owns token state (`icoder/core/app_core.py`)

- New `_token_usage: TokenUsage` field, exposed via `token_usage` property
- `stream_llm()` extracts usage from the `"done"` event **inside** the stream for-loop (before yielding) and calls `_token_usage.update(...)`. This avoids a race condition where the UI thread could read `token_usage` on `StreamDone` before post-loop code runs.
- Follows existing core/UI split: core owns state, UI renders

### Modified: Status bar replaces `#input-hint` (`icoder/ui/app.py`, `icoder/ui/styles.py`)

- Single `Static(id="input-hint")` replaced by `Horizontal(id="status-bar")` with three `Static` children: `#status-tokens`, `#status-version`, `#status-hint`
- `on_text_area_changed()` deleted — status bar always visible (decision #5)
- On `StreamDone`, UI reads `app_core.token_usage` and updates `#status-tokens`
- When provider supplies no token data (`_ever_updated` is True but totals are 0), `#status-tokens` is hidden (decision #11)
- Version read once from `app_core.runtime_info.mcp_coder_version` or `importlib.metadata`

### New: Documentation (`docs/icoder/icoder.md`)

- Dedicated TUI documentation covering slash commands, status line, busy indicator, input behavior

## Files Created or Modified

### Created
| File | Purpose |
|------|---------|
| `docs/icoder/icoder.md` | TUI documentation (slash commands, status line, busy indicator, input) |

### Modified
| File | Change |
|------|--------|
| `src/mcp_coder/icoder/core/types.py` | Add `TokenUsage` dataclass + `format_token_count()` |
| `src/mcp_coder/icoder/core/app_core.py` | Add `_token_usage` field, update in `stream_llm()` |
| `src/mcp_coder/icoder/ui/app.py` | Replace `#input-hint` with 3-zone status bar, remove `on_text_area_changed`, update `StreamDone` handler |
| `src/mcp_coder/icoder/ui/styles.py` | Replace `#input-hint` CSS with `#status-bar` + children styles |
| `tests/icoder/test_types.py` | Tests for `TokenUsage` and `format_token_count()` |
| `tests/icoder/test_app_core.py` | Test `stream_llm()` updates `token_usage` |
| `tests/icoder/test_snapshots.py` | Regenerate snapshot SVGs for new status bar |
| `tests/icoder/__snapshots__/*.svg` | Updated snapshot baselines |

## Data Flow

```
LLM stream → events flow through AppCore.stream_llm() for-loop
           → on "done" event: extract usage from event dict
           → AppCore._token_usage.update(input, output) (inside loop, before yield)
           → yield event → UI handles StreamDone → reads app_core.token_usage
           → Updates #status-tokens label text
```

## Key Decisions (from issue)

| # | Decision |
|---|----------|
| 5 | Status line always visible, never hides |
| 6 | Initial state shows zeroes: `↓0 ↑0 \| total: ↓0 ↑0` |
| 7 | `TokenUsage` in core, owned by `AppCore` |
| 8 | Pull on `StreamDone` — read `app_core.token_usage` |
| 10 | Compact format: `↓1.2k`, `↓12k`, `↓123k`, `↓1.2M` |
| 11 | No usage data → hide token zone entirely |
