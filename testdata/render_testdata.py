#!/usr/bin/env python3
"""Render each tool_*.json as the full iCoder block: header + args + output + footer.

Produces _raw.txt showing exactly what iCoder displays today.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    _render_tool_output,
)
from mcp_coder.llm.formatting.render_actions import ToolResult, ToolStart

TESTDATA = Path(__file__).resolve().parent


def render_full_block(data: dict) -> list[str]:
    """Render a tool call exactly as app.py does: header + args + output + footer."""
    renderer = StreamEventRenderer(format_tools=True)
    lines: list[str] = []

    call = data["tool_call"]
    name = call.get("name", "")
    args = call.get("input", {})

    # --- Header (ToolStart) --- same as app.py:214-223
    action = renderer.render({"type": "tool_use_start", "name": name, "args": args})
    if isinstance(action, ToolStart):
        if action.inline_args is not None:
            lines.append(f"┌ {action.display_name}({action.inline_args})")
        else:
            lines.append(f"┌ {action.display_name}")
            for key, value in action.block_args:
                lines.append(f"│  {key}: {value}")

    # --- Output + Footer (ToolResult) --- same as app.py:224-234
    tr = data.get("tool_result", {})
    output = tr.get("content", "") if isinstance(tr, dict) else str(tr)

    action = renderer.render({"type": "tool_result", "name": name, "output": output})
    if isinstance(action, ToolResult):
        for ln in action.output_lines:
            lines.append(f"│  {ln}")
        if action.truncated:
            lines.append(
                f"└ done ({action.total_lines} lines, "
                f"truncated to {len(action.output_lines)})"
            )
        else:
            lines.append("└ done")

    return lines


def main() -> None:
    for json_file in sorted(TESTDATA.glob("tool_*.json")):
        data = json.loads(json_file.read_text(encoding="utf-8"))
        if "tool_call" not in data:
            continue

        lines = render_full_block(data)

        out_file = json_file.with_name(json_file.stem + "_raw.txt")
        out_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"{out_file.name} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
