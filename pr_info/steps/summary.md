# Issue #779: BusyIndicator stays Ready while querying LLM

## Problem

When the user submits input to the LLM, the `BusyIndicator` remains on "✓ Ready" until the first `TextChunk` or `ToolStart` stream event arrives. This creates a gap with no visual feedback — the user sees nothing happening while the LLM request is in flight.

## Root Cause

In `ICoderApp.on_input_area_input_submitted()` (`src/mcp_coder/icoder/ui/app.py`), the `send_to_llm` branch calls `self.run_worker(...)` without first updating the `BusyIndicator`. The indicator only transitions out of "✓ Ready" when `_handle_stream_event` receives the first `TextChunk` (→ "Thinking...") or `ToolStart` (→ tool display name).

## Solution

Add a single `show_busy("Querying LLM...")` call immediately before `self.run_worker(...)` in the `send_to_llm` branch. No new methods, classes, or files needed.

## Architectural / Design Changes

**None.** This change uses the existing `BusyIndicator.show_busy()` API exactly as it's already used elsewhere in the same file. The busy indicator lifecycle remains unchanged:

1. **NEW** → "Querying LLM..." — set on submit, before worker starts
2. "Thinking..." — on first `TextChunk` (existing)
3. Tool display name — on `ToolStart` (existing)
4. "✓ Ready" — on `StreamDone` or error (existing)

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/icoder/ui/app.py` | Add `show_busy("Querying LLM...")` before `run_worker()` |
| `tests/icoder/test_app_pilot.py` | Add test verifying indicator shows "Querying LLM..." on submit |
