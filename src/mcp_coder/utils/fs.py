"""Line-ending and path-containment shim — re-exports from mcp_coder_utils."""

from mcp_coder_utils.fs import check_path_within, dominant_newline, write_text

__all__ = ["check_path_within", "dominant_newline", "write_text"]
