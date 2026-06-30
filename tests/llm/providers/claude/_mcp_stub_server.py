"""Throwaway stdio MCP server for the cold-start integration tests (#999).

A minimal FastMCP stdio server exposing ONE tool, ``reveal_sentinel``, that
returns an unguessable sentinel string. Both the sentinel and an artificial
startup delay are supplied via environment variables so the driving test
controls them:

- ``MCP_STUB_SENTINEL``: the exact string the tool returns. The model cannot
  guess it, so its appearance in a real ``tool_result`` (and in the final text)
  proves a genuine MCP tool call happened — not a hallucination.
- ``MCP_STUB_STARTUP_DELAY_SECONDS``: seconds to sleep *before* the server
  starts serving. The sleep runs before ``mcp.run()`` connects stdio, so the
  server's ``initialize`` is delayed and the Claude CLI reports it ``pending``
  at the init event (past the ~5 s ``alwaysLoad`` cap). With a large enough
  delay (or one exceeding ``MCP_TIMEOUT``) the server never connects in time.

This module is intentionally tiny and dependency-light: it relies only on the
``mcp`` SDK (FastMCP) already used by the project's own MCP servers. It is run
as a script via ``python -m`` / ``python <path>`` from a generated ``.mcp.json``
using ``sys.executable``.
"""

import os
import sys
import time

from mcp.server.fastmcp import FastMCP

# Read configuration from the environment BEFORE constructing the server so the
# startup delay can take effect prior to any stdio handshake.
_SENTINEL = os.environ.get("MCP_STUB_SENTINEL", "NO_SENTINEL_SET")
_STARTUP_DELAY_SECONDS = float(os.environ.get("MCP_STUB_STARTUP_DELAY_SECONDS", "0"))

mcp = FastMCP("mcp-stub")


@mcp.tool()
def reveal_sentinel() -> str:
    """Return the secret sentinel value configured for this test run.

    The value is an unguessable token injected via ``MCP_STUB_SENTINEL``; a
    matching ``tool_result`` proves the model really invoked this MCP tool.

    Returns:
        The sentinel string from the environment.
    """
    return _SENTINEL


def main() -> None:
    """Delay startup (to force a ``pending`` init), then serve over stdio."""
    if _STARTUP_DELAY_SECONDS > 0:
        # Sleep before connecting stdio so the Claude CLI sees this server as
        # still cold-starting (``pending``) at the init event.
        print(
            f"[mcp-stub] delaying startup by {_STARTUP_DELAY_SECONDS}s",
            file=sys.stderr,
            flush=True,
        )
        time.sleep(_STARTUP_DELAY_SECONDS)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
