"""Tests for config_hints module."""

from collections.abc import Iterable

import pytest

from mcp_coder.utils import config_hints
from mcp_coder.utils.config_hints import suggest, unknown_key_hint

LANGCHAIN_KEYS = ["backend", "model", "api_key", "base_url", "api_version"]
GITHUB_KEYS = ["token", "test_repo_url"]


class TestSuggest:
    """Tests for suggest function."""

    def test_suggest_returns_closest_candidate(self) -> None:
        """Typo close to a candidate -> that candidate."""
        assert suggest("modell", ["model", "backend"]) == "model"

    def test_suggest_returns_none_when_nothing_close(self) -> None:
        """Unrelated name -> None."""
        assert suggest("zzz", ["model", "backend"]) is None

    def test_suggest_with_empty_candidates(self) -> None:
        """No candidates -> None."""
        assert suggest("model", []) is None

    def test_suggest_accepts_any_iterable(self) -> None:
        """Candidates may be any iterable, not just a list."""
        assert suggest("tokenn", iter(GITHUB_KEYS)) == "token"

    def test_suggest_exact_match_returns_name(self) -> None:
        """An exact match is its own closest candidate."""
        assert suggest("model", LANGCHAIN_KEYS) == "model"


class TestUnknownKeyHint:
    """Tests for unknown_key_hint function."""

    def test_rename_hint_for_retired_endpoint_key(self) -> None:
        """[llm.langchain] endpoint -> explicit rename text."""
        assert (
            unknown_key_hint("llm.langchain", "endpoint", LANGCHAIN_KEYS)
            == "renamed to base_url"
        )

    def test_rename_hint_does_not_consult_edit_distance(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The rename table short-circuits before suggest() is called."""

        def _fail(name: str, candidates: Iterable[str]) -> str | None:
            raise AssertionError("suggest() must not be called for a known rename")

        monkeypatch.setattr(config_hints, "suggest", _fail)

        assert (
            config_hints.unknown_key_hint("llm.langchain", "endpoint", LANGCHAIN_KEYS)
            == "renamed to base_url"
        )

    def test_rename_hint_is_section_scoped(self) -> None:
        """endpoint in an unrelated section gets no rename text."""
        assert unknown_key_hint("github", "endpoint", GITHUB_KEYS) is None

    def test_near_miss_hint_for_other_section(self) -> None:
        """Typo'd key in another section -> did you mean."""
        assert (
            unknown_key_hint("github", "tokenn", GITHUB_KEYS) == "did you mean token?"
        )

    def test_no_hint_when_key_is_unrelated(self) -> None:
        """Unknown key close to nothing -> None."""
        assert unknown_key_hint("llm.langchain", "zzz", LANGCHAIN_KEYS) is None
