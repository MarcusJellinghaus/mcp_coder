"""Unit test for the mcp_tools_py shim's resolve_steps re-export."""


def test_resolve_steps_reexported() -> None:
    """resolve_steps is importable from the wrapper module."""
    from mcp_tools_py.formatter.runner import resolve_steps as upstream

    from mcp_coder.mcp_tools_py import resolve_steps

    assert resolve_steps is upstream
