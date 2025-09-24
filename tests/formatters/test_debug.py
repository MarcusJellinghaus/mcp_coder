"""Debug test to check if pytest can find tests."""

import pytest


def test_simple():
    """Simple test to verify pytest works."""
    assert True


@pytest.mark.formatter_integration
def test_simple_with_marker():
    """Simple test with marker to verify pytest works."""
    assert True
