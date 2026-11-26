"""The verify_render shim re-exports mcp-coder-utils' objects unchanged."""

import mcp_coder_utils.verify_render as upstream
import pytest

from mcp_coder.utils import verify_render as shim


@pytest.mark.parametrize("name", upstream.__all__)
def test_shim_reexports_upstream_object(name: str) -> None:
    """Each upstream public name is the very same object in the shim."""
    assert getattr(shim, name) is getattr(upstream, name)
