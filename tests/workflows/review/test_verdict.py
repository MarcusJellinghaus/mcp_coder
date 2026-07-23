"""Table-driven tests for the verdict parser (Step 5)."""

import pytest

from mcp_coder.workflows.review.verdict import Verdict, parse_verdict


class TestParseVerdictValid:
    """Well-formed verdicts of each decision kind."""

    def test_dismiss(self) -> None:
        text = 'prose\n```json\n{"decision": "dismiss"}\n```\nmore prose'
        result = parse_verdict(text)
        assert result == Verdict(decision="dismiss")

    def test_tasks_with_list(self) -> None:
        text = '```json\n{"decision": "tasks", "tasks": ["fix foo", "fix bar"]}\n```'
        result = parse_verdict(text)
        assert result == Verdict(decision="tasks", tasks=["fix foo", "fix bar"])

    def test_escalate_with_reason(self) -> None:
        text = '```json\n{"decision": "escalate", "escalate_reason": "unclear"}\n```'
        result = parse_verdict(text)
        assert result == Verdict(decision="escalate", escalate_reason="unclear")

    def test_escalate_without_reason(self) -> None:
        text = '```json\n{"decision": "escalate"}\n```'
        result = parse_verdict(text)
        assert result == Verdict(decision="escalate", escalate_reason=None)

    def test_fenced_block_surrounded_by_prose(self) -> None:
        text = (
            "Here is my triage of the findings.\n\n"
            '```json\n{"decision": "dismiss"}\n```\n\n'
            "Let me know if you need anything else."
        )
        assert parse_verdict(text) == Verdict(decision="dismiss")

    def test_last_fenced_block_wins(self) -> None:
        text = (
            '```json\n{"decision": "escalate"}\n```\n'
            "on reflection:\n"
            '```json\n{"decision": "dismiss"}\n```'
        )
        assert parse_verdict(text) == Verdict(decision="dismiss")

    def test_bare_object_fallback(self) -> None:
        text = 'no fence here {"decision": "dismiss"} trailing'
        assert parse_verdict(text) == Verdict(decision="dismiss")

    def test_extra_keys_ignored(self) -> None:
        text = '```json\n{"decision": "dismiss", "confidence": 0.9, "notes": "x"}\n```'
        assert parse_verdict(text) == Verdict(decision="dismiss")

    def test_tasks_normalized_strips_empties(self) -> None:
        text = (
            "```json\n"
            '{"decision": "tasks", "tasks": ["keep", "  ", "", "  trim  "]}\n'
            "```"
        )
        result = parse_verdict(text)
        assert result == Verdict(decision="tasks", tasks=["keep", "trim"])


class TestParseVerdictInvalid:
    """Malformed or invalid input returns None."""

    def test_malformed_json(self) -> None:
        text = '```json\n{"decision": "dismiss",}\n```'
        assert parse_verdict(text) is None

    def test_no_json_at_all(self) -> None:
        assert parse_verdict("just some prose with no verdict") is None

    def test_empty_string(self) -> None:
        assert parse_verdict("") is None

    def test_unknown_decision(self) -> None:
        text = '```json\n{"decision": "maybe"}\n```'
        assert parse_verdict(text) is None

    def test_missing_decision(self) -> None:
        text = '```json\n{"tasks": ["x"]}\n```'
        assert parse_verdict(text) is None

    def test_tasks_with_missing_list(self) -> None:
        text = '```json\n{"decision": "tasks"}\n```'
        assert parse_verdict(text) is None

    def test_tasks_with_empty_list(self) -> None:
        text = '```json\n{"decision": "tasks", "tasks": []}\n```'
        assert parse_verdict(text) is None

    def test_tasks_with_only_blank_entries(self) -> None:
        text = '```json\n{"decision": "tasks", "tasks": ["", "  "]}\n```'
        assert parse_verdict(text) is None

    def test_non_object_json(self) -> None:
        text = '```json\n["decision", "dismiss"]\n```'
        assert parse_verdict(text) is None

    def test_decision_not_a_string(self) -> None:
        text = '```json\n{"decision": 3}\n```'
        assert parse_verdict(text) is None


class TestVerdictDataclass:
    """The Verdict dataclass is frozen with sensible defaults."""

    def test_defaults(self) -> None:
        verdict = Verdict(decision="dismiss")
        assert verdict.tasks == []
        assert verdict.escalate_reason is None

    def test_frozen(self) -> None:
        verdict = Verdict(decision="dismiss")
        with pytest.raises(AttributeError):
            verdict.decision = "tasks"  # type: ignore[misc]
