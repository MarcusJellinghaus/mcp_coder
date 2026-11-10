"""Tests for the [language_context] slot of the create_plan plan request."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.workflows.create_plan import run_planning_prompts
from tests.workflows.create_plan.test_prompt_execution import _make_issue_data

_CORE = "mcp_coder.workflows.create_plan.core"

_PROMPTS = {
    "Initial Analysis": "Prompt 1",
    "Simplification Review": "Prompt 2",
    "Implementation Plan Creation": "## Plan Request\n[language_context]\nCreate it.",
}


def _run(tmp_path: Path, slot_value: str) -> tuple[str, MagicMock]:
    """Run the planning prompts; return the plan request and the slot mock."""
    response = {"text": "Response", "session_id": "test-session-123"}
    with (
        patch(f"{_CORE}.get_prompt", side_effect=lambda _, header: _PROMPTS[header]),
        patch(
            f"{_CORE}.resolve_prompt_slots",
            return_value={"language_context": slot_value},
        ) as mock_slots,
        patch(f"{_CORE}.prompt_llm", return_value=response) as mock_prompt_llm,
        patch(f"{_CORE}.store_session", return_value="/fake/path.json"),
    ):
        assert run_planning_prompts(tmp_path, _make_issue_data(), "claude") == (
            True,
            None,
        )
    prompt: str = mock_prompt_llm.call_args_list[2].args[0]
    return prompt, mock_slots


@pytest.mark.parametrize(
    ("slot_value", "expected"),
    [
        ("Python project.", "## Plan Request\nPython project.\nCreate it."),
        ("", "## Plan Request\nCreate it."),
    ],
)
def test_plan_request_fills_language_context(
    tmp_path: Path, slot_value: str, expected: str
) -> None:
    """The slot is filled, or its line removed for an empty value."""
    prompt, mock_slots = _run(tmp_path, slot_value)

    assert prompt == expected
    assert mock_slots.call_args.args == (
        _PROMPTS["Implementation Plan Creation"],
        tmp_path,
        "claude",
        None,
    )
