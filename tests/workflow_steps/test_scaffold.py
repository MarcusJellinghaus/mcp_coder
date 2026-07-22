"""Scaffold tests for the mcp_coder.workflow_steps package.

These verify the empty package exists and ships as a typed package
(mirrors the workflow_utils layout) before any workflow code moves in.
"""

from pathlib import Path


def test_package_importable() -> None:
    """The workflow_steps package can be imported."""
    import mcp_coder.workflow_steps

    assert mcp_coder.workflow_steps is not None


def test_py_typed_present() -> None:
    """A py.typed marker sits next to the package __init__.py."""
    import mcp_coder.workflow_steps

    package_file = mcp_coder.workflow_steps.__file__
    assert package_file is not None
    py_typed = Path(package_file).parent / "py.typed"
    assert py_typed.is_file()
