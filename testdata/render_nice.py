#!/usr/bin/env python3
"""Render each tool_*.json nicely: _nice_compact.txt and _nice_full.txt.

Generic rendering — no tool-specific logic. Rules:
  1. Inline args when few + short (<120 chars total), block otherwise
  2. Two modes: compact (summarized args, truncated output) / full (expanded args, no truncation)
  3. ├── separator between args and output (skipped when no args)
  4. Multiline strings split on newlines (not escaped)
  5. Standard JSON pretty-print, no field filtering
  6. Lists: inline if ≤120 chars, json.dumps(indent=2) otherwise
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp_coder.llm.formatting.stream_renderer import _format_tool_name

TESTDATA = Path(__file__).resolve().parent

_HEAD_LINES = 10
_TAIL_LINES = 5
_TRUNCATION_THRESHOLD = _HEAD_LINES + _TAIL_LINES
_INLINE_MAX_LEN = 120
_VALUE_TRUNCATE_LEN = 120


def _truncate(lines: list[str]) -> tuple[list[str], int]:
    total = len(lines)
    if total > _TRUNCATION_THRESHOLD:
        skipped = total - _HEAD_LINES - _TAIL_LINES
        lines = (
            lines[:_HEAD_LINES]
            + [f"... ({skipped} lines skipped)"]
            + lines[-_TAIL_LINES:]
        )
    return lines, total


# ── Rendering values generically ─────────────────────────────────────

def _render_value_compact(value: object) -> str:
    """Render a value as a single-line summary."""
    if isinstance(value, str):
        if len(value) > 80:
            return f"({len(value)} chars)"
        return repr(value)
    if isinstance(value, list):
        if any(isinstance(item, dict) for item in value):
            return f"({len(value)} items)"
        compact = json.dumps(value)
        if len(compact) <= _INLINE_MAX_LEN:
            return compact
        return f"({len(value)} items)"
    if isinstance(value, dict):
        compact = json.dumps(value)
        if len(compact) <= _INLINE_MAX_LEN:
            return compact
        return f"({len(value)} keys)"
    return repr(value)


def _render_value_full(value: object) -> list[str]:
    """Render a value as multiple lines with detail."""
    if isinstance(value, str):
        if "\n" in value:
            return value.splitlines()
        if len(value) > _VALUE_TRUNCATE_LEN:
            return [f"{value[:_VALUE_TRUNCATE_LEN - 3]}..."]
        return [value]
    if isinstance(value, list):
        compact = json.dumps(value)
        if len(compact) <= _INLINE_MAX_LEN:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    if isinstance(value, dict):
        compact = json.dumps(value)
        if len(compact) <= _INLINE_MAX_LEN:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    return [repr(value)]


# ── Header: tool name + args ────────────────────────────────────────

def _format_header(name: str, args: dict, full: bool = False) -> list[str]:
    display = _format_tool_name(name)

    if not args:
        return [f"┌ {display}"]

    # Try inline — both modes use inline when args are short enough
    parts = [f"{k}={_render_value_compact(v)}" for k, v in args.items()]
    inline = f"┌ {display}({', '.join(parts)})"
    if len(inline) <= _INLINE_MAX_LEN:
        return [inline]

    # Block format
    lines = [f"┌ {display}"]
    for key, value in args.items():
        if full:
            val_lines = _render_value_full(value)
            if len(val_lines) == 1:
                lines.append(f"│  {key}: {val_lines[0]}")
            else:
                lines.append(f"│  {key}:")
                for vl in val_lines:
                    lines.append(f"│    {vl}")
        else:
            lines.append(f"│  {key}: {_render_value_compact(value)}")

    return lines


# ── Output: tool result body ─────────────────────────────────────────

def _render_json_value(value: object) -> list[str]:
    """Render any JSON value generically, splitting multiline strings."""
    if isinstance(value, str):
        if "\n" in value:
            return value.splitlines()
        return [value]
    if isinstance(value, bool):
        return [json.dumps(value)]
    if isinstance(value, (int, float)):
        return [str(value)]
    if isinstance(value, list):
        compact = json.dumps(value)
        if len(compact) <= _INLINE_MAX_LEN:
            return [compact]
        return json.dumps(value, indent=2).splitlines()
    if isinstance(value, dict):
        return _render_dict(value)
    return [str(value)]


def _render_dict(d: dict) -> list[str]:
    """Render a dict, expanding multiline string values."""
    lines: list[str] = []
    for key, value in d.items():
        if isinstance(value, str) and "\n" in value:
            lines.append(f"{key}:")
            for sub in value.splitlines():
                lines.append(f"  {sub}")
        elif isinstance(value, (dict, list)):
            rendered = _render_json_value(value)
            if len(rendered) == 1:
                lines.append(f"{key}: {rendered[0]}")
            else:
                lines.append(f"{key}:")
                for sub in rendered:
                    lines.append(f"  {sub}")
        else:
            lines.append(f"{key}: {json.dumps(value)}")
    return lines


def _render_output(output: str) -> list[str]:
    """Render tool output generically."""
    if not output:
        return []

    try:
        parsed = json.loads(output)
    except (json.JSONDecodeError, ValueError):
        return output.splitlines()

    if not isinstance(parsed, dict):
        return _render_json_value(parsed)

    # Unwrap {"result": ...} envelope
    if "result" in parsed:
        result = parsed["result"]
        result_lines = _render_json_value(result)
        # Render remaining keys as extras
        extras = {k: v for k, v in parsed.items() if k != "result"}
        if extras:
            result_lines.append("")
            result_lines.extend(_render_dict(extras))
        return result_lines

    return _render_dict(parsed)


# ── Full block assembly ──────────────────────────────────────────────

def render_nice_block(data: dict, full: bool = False) -> list[str]:
    call = data["tool_call"]
    name = call.get("name", "")
    args = call.get("input", {})

    tr = data.get("tool_result", {})
    output = tr.get("content", "") if isinstance(tr, dict) else str(tr)

    # Header + args
    lines = _format_header(name, args, full=full)

    # Separator (only when there are args)
    if args:
        lines.append("├──")

    # Output
    output_lines = _render_output(output)
    if not full:
        output_lines, total = _truncate(output_lines)
    else:
        total = len(output_lines)
    for ln in output_lines:
        lines.append(f"│  {ln}")

    # Footer
    if total > len(output_lines):
        lines.append(f"└ done ({total} lines, truncated to {len(output_lines)})")
    else:
        lines.append("└ done")

    return lines


def main() -> None:
    for json_file in sorted(TESTDATA.glob("tool_*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        if "tool_call" not in data:
            continue

        for mode, suffix in [("compact", "_nice_compact.txt"), ("full", "_nice_full.txt")]:
            lines = render_nice_block(data, full=(mode == "full"))
            out_file = json_file.with_name(json_file.stem + suffix)
            out_file.write_text("\n".join(lines), encoding="utf-8")
            print(f"{out_file.name} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
