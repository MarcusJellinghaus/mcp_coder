"""Tests for the IssueData test factory."""

import pytest

from tests.github_factories import make_issue_data


def test_unknown_key_raises_type_error() -> None:
    """Typo'd keys raise; NotRequired keys are accepted."""
    with pytest.raises(TypeError):
        make_issue_data(lable=["x"])
    assert make_issue_data(base_branch="main")["base_branch"] == "main"


def test_title_and_url_follow_number_unless_overridden() -> None:
    """Title and url derive from number unless explicitly overridden."""
    issue = make_issue_data(number=7)
    assert issue["title"] == "Issue 7"
    assert issue["url"] == "https://github.com/owner/repo/issues/7"
    assert issue["state"] == "open"

    overridden = make_issue_data(number=7, title="T", url="")
    assert overridden["title"] == "T"
    assert overridden["url"] == ""
