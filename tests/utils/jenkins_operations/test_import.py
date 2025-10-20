"""Test if models can be imported."""


def test_import_models() -> None:
    """Test that models can be imported."""
    from mcp_coder.utils.jenkins_operations.models import JobStatus, QueueSummary

    assert JobStatus is not None
    assert QueueSummary is not None
