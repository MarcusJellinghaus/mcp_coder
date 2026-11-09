"""Shim for the mcp_tools_py library.

Sole permitted importer of mcp_tools_py. Re-exports resolve_steps for
cli verify; workflow checks run through the toolkit (utils/toolkit_runner).
"""

from mcp_tools_py.formatter.runner import resolve_steps

__all__ = ["resolve_steps"]
