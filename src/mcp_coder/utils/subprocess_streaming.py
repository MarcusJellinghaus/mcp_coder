"""Streaming subprocess execution — thin shim over mcp-coder-utils."""

from mcp_coder_utils.subprocess_streaming import StreamResult, stream_subprocess

__all__ = ["StreamResult", "stream_subprocess"]
