# Copilot CLI Response Structure

## Overview

The Copilot CLI outputs JSONL (one JSON object per line).

## JSONL Message Types

Each line is a JSON object with a `type` field. Key types:

| Type | Purpose |
|------|---------|
| `message` | Assistant text content |
| `tool_use` | Tool invocation request |
| `tool_result` | Tool execution result |
| `error` | Error information |

## Implementation

Parsing is implemented in:
- [`src/mcp_coder/llm/providers/copilot/copilot_cli.py`](../../src/mcp_coder/llm/providers/copilot/copilot_cli.py) — `parse_copilot_jsonl_line()`, `parse_copilot_jsonl_output()`
- [`src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py`](../../src/mcp_coder/llm/providers/copilot/copilot_cli_streaming.py) — Streaming variant

## Key Differences vs Claude SDK

| Aspect | Claude SDK | Copilot CLI |
|--------|-----------|-------------|
| Format | Typed Python objects | JSONL (line-delimited JSON) |
| Session info | `SystemMessage` with `session_id` | Extracted from JSONL stream |
| Cost tracking | `ResultMessage.total_cost_usd` | Not available |
| Token usage | Detailed breakdown in `ResultMessage` | Limited |
