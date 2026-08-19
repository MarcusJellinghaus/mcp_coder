"""Throwaway FastMCP stdio server for the I3.1 approval spike (#1044) — Tier C.

A minimal ``mcp.server.fastmcp.FastMCP`` stdio server exposing ONE trivial
tool, ``ping``, that returns its ``text`` argument unchanged. It is the single
gated tool the real ``tool_interceptors=[gate.interceptor]`` fires on in
``tier_c.py``.

Shape copied from the proven-on-this-platform template
``tests/llm/providers/claude/_mcp_stub_server.py`` (F7): a tiny, dependency-light
FastMCP server launched as a subprocess via ``sys.executable`` (D4 — no new
dependency; ``mcp.server.fastmcp`` arrives transitively via
``langchain-mcp-adapters``). Lives INSIDE the spike dir and is deleted with it
(D9).

Run as a script (``python spikes/i3-1-approval/server.py``); the driver launches
it over stdio using ``sys.executable`` and this file's absolute path so it is
CWD-independent.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("spike")


@mcp.tool()
def ping(text: str) -> str:
    """Return ``text`` unchanged — the single gated tool.

    Args:
        text: Arbitrary string echoed straight back so a real ``tool_result``
            proves a genuine MCP round-trip through the interceptor happened.

    Returns:
        The input ``text``, verbatim.
    """
    return text


if __name__ == "__main__":
    mcp.run(transport="stdio")
