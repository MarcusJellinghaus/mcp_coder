"""Tests for the grouped, capped fix loop in check_loop."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.toolkit import ActionResult, Finding
from mcp_coder.utils.toolkit_runner import get_fragment as real_get_fragment
from mcp_coder.workflows.implement.check_loop import (
    MAX_FIX_TURNS,
    CheckOutcome,
    check_and_fix_mypy,
)

_PROJECT = Path("/test/project")
_CL = "mcp_coder.workflows.implement.check_loop"
_OK = ActionResult(status="ok", summary="clean")


def _findings(fix_text: str = "", summary: str = "1 error") -> ActionResult:
    return ActionResult(
        status="findings",
        summary=summary,
        findings=[Finding(key="k", message="m")],
        fix_text=fix_text,
    )


def _loaded(*requests: str, entry: str = "implement_final") -> MagicMock:
    loaded = MagicMock()
    loaded.config.bindings = {entry: tuple(requests)}
    return loaded


class _Env:
    """Patched collaborators of check_and_fix_mypy."""

    def __init__(
        self,
        load: MagicMock,
        run: MagicMock,
        fragment: MagicMock,
        fix_turn: MagicMock,
    ) -> None:
        self.load = load
        self.run = run
        self.fragment = fragment
        self.fix_turn = fix_turn

    def binding(self, *requests: str, entry: str = "implement_final") -> None:
        self.load.return_value = _loaded(*requests, entry=entry)

    def results(self, *passes: dict[str, ActionResult]) -> None:
        """One dict per pass mapping request -> result; the last one repeats."""
        state = {"pass": 0}
        seen: set[str] = set()

        def run(_loaded: Any, _dir: Path, request: str) -> ActionResult:
            if request in seen:
                state["pass"] += 1
                seen.clear()
            seen.add(request)
            current = passes[min(state["pass"], len(passes) - 1)]
            return current.get(request, _OK)

        self.run.side_effect = run

    def requests_run(self) -> list[str]:
        return [c.args[2] for c in self.run.call_args_list]


@pytest.fixture
def env() -> Iterator[_Env]:
    with (
        patch(f"{_CL}.load_toolkit") as load,
        patch(f"{_CL}.run_request") as run,
        patch(f"{_CL}.get_fragment") as fragment,
        patch(f"{_CL}._fix_turn", return_value=None) as fix_turn,
    ):
        fragment.side_effect = lambda _loaded, key: f"FRAG {key}"
        run.return_value = _OK
        yield _Env(load, run, fragment, fix_turn)


def _run(**kwargs: Any) -> CheckOutcome:
    return check_and_fix_mypy(_PROJECT, 1, "claude", **kwargs)


class TestCleanAndGrouping:
    def test_all_clean_returns_clean_without_fix_turn(self, env: _Env) -> None:
        env.binding("check@standard", "test@quick")

        assert _run() == CheckOutcome("clean")
        env.fix_turn.assert_not_called()
        assert env.requests_run() == ["check@standard", "test@quick"]

    def test_checks_run_before_tests(self, env: _Env) -> None:
        env.binding("test@quick", "check@quick")

        assert _run().status == "clean"
        assert env.requests_run() == ["check@quick", "test@quick"]

    def test_tests_not_run_while_check_has_findings(self, env: _Env) -> None:
        env.binding("test@quick", "check@quick")
        env.results({"check@quick": _findings("a.py:1")}, {})

        assert _run().status == "clean"
        assert env.requests_run() == ["check@quick", "check@quick", "test@quick"]

    def test_entry_selects_binding(self, env: _Env) -> None:
        env.binding("check@quick", entry="implement_task")

        assert _run(entry="implement_task").status == "clean"
        assert env.requests_run() == ["check@quick"]

    def test_load_toolkit_called_once_per_pass(self, env: _Env) -> None:
        env.binding("check@quick")
        env.results(
            {"check@quick": _findings("x")}, {"check@quick": _findings("y")}, {}
        )

        assert _run().status == "clean"
        assert env.load.call_count == 3


class TestFixTurns:
    def test_check_findings_use_fix_check_fragment(self, env: _Env) -> None:
        env.binding("check@quick", "test@quick")
        env.results({"check@quick": _findings("a.py:1: error")}, {})

        assert _run().status == "clean"
        env.fix_turn.assert_called_once()
        args = env.fix_turn.call_args.args
        assert args[0] == "FRAG fix.check"
        assert args[1] == "a.py:1: error"
        assert args[4] == 1  # turn

    def test_findings_without_fix_text_use_summary(self, env: _Env) -> None:
        env.binding("check@quick", "check@standard")
        env.results(
            {
                "check@quick": _findings(summary="3 errors"),
                "check@standard": _findings("b.py:2"),
            },
            {},
        )

        assert _run().status == "clean"
        assert env.fix_turn.call_args.args[1] == "3 errors\n\nb.py:2"

    def test_test_findings_use_fix_test_and_rerun_checks(self, env: _Env) -> None:
        env.binding("check@quick", "test@quick")
        env.results({"test@quick": _findings("test_a failed")}, {})

        assert _run().status == "clean"
        env.fix_turn.assert_called_once()
        assert env.fix_turn.call_args.args[0] == "FRAG fix.test"
        assert env.fix_turn.call_args.args[1] == "test_a failed"
        assert env.requests_run() == [
            "check@quick",
            "test@quick",
            "check@quick",
            "test@quick",
        ]

    def test_cap_after_three_fix_turns(self, env: _Env) -> None:
        env.binding("check@quick")
        env.results({"check@quick": _findings("x")})

        outcome = _run()

        assert outcome.status == "cap"
        assert env.fix_turn.call_count == MAX_FIX_TURNS == 3
        assert "fix.check" in outcome.detail
        assert "3" in outcome.detail
        # One last pass runs after the third turn
        assert env.run.call_count == 4

    def test_clean_after_third_fix_turn_is_clean(self, env: _Env) -> None:
        env.binding("check@quick")
        bad = {"check@quick": _findings("x")}
        env.results(bad, bad, bad, {})

        assert _run() == CheckOutcome("clean")
        assert env.fix_turn.call_count == 3

    def test_cap_is_shared_by_checks_and_tests(self, env: _Env) -> None:
        env.binding("check@quick", "test@quick")
        check_bad = {"check@quick": _findings("c")}
        test_bad = {"test@quick": _findings("t")}
        env.results(check_bad, check_bad, test_bad, test_bad)

        outcome = _run()

        assert outcome.status == "cap"
        assert env.fix_turn.call_count == 3
        fragments = [c.args[0] for c in env.fix_turn.call_args_list]
        assert fragments == ["FRAG fix.check", "FRAG fix.check", "FRAG fix.test"]
        assert [c.args[4] for c in env.fix_turn.call_args_list] == [1, 2, 3]

    @pytest.mark.parametrize(
        "ended",
        [
            CheckOutcome("cap", "Fix turn failed: boom"),
            CheckOutcome("blocked", "need input"),
            CheckOutcome("timeout", ""),
            CheckOutcome("mcp_unavailable", "marker"),
        ],
    )
    def test_fix_turn_outcome_ends_loop(self, env: _Env, ended: CheckOutcome) -> None:
        env.binding("check@quick")
        env.results({"check@quick": _findings("x")})
        env.fix_turn.return_value = ended

        assert _run() == ended
        env.fix_turn.assert_called_once()

    def test_forwards_llm_params_to_fix_turn(self, env: _Env) -> None:
        env.binding("check@quick")
        env.results({"check@quick": _findings("x")}, {})

        check_and_fix_mypy(
            _PROJECT,
            7,
            "copilot",
            env_vars={"A": "1"},
            mcp_config="mcp.json",
            settings_file="s.json",
        )

        assert env.fix_turn.call_args.args == (
            "FRAG fix.check",
            "x",
            _PROJECT,
            "copilot",
            1,
            7,
            {"A": "1"},
            "mcp.json",
            "s.json",
        )


class TestErrors:
    def test_error_result_returns_error_without_fix_turn(self, env: _Env) -> None:
        env.binding("check@quick", "check@standard")
        env.results({"check@quick": ActionResult(status="error", summary="crashed")})

        outcome = _run()

        assert outcome.status == "error"
        assert "check@quick" in outcome.detail
        assert "crashed" in outcome.detail
        env.fix_turn.assert_not_called()

    def test_error_in_test_group(self, env: _Env) -> None:
        env.binding("check@quick", "test@quick")
        env.results({"test@quick": ActionResult(status="error", summary="no pytest")})

        outcome = _run()

        assert outcome == CheckOutcome("error", "test@quick: no pytest")

    def test_load_toolkit_value_error_first_pass(self, env: _Env) -> None:
        env.load.side_effect = ValueError("bad config in pyproject.toml")

        outcome = _run()

        assert outcome == CheckOutcome("error", "bad config in pyproject.toml")
        env.fix_turn.assert_not_called()

    def test_load_toolkit_value_error_after_fix_turn(self, env: _Env) -> None:
        env.load.side_effect = [_loaded("check@quick"), ValueError("edited config")]
        env.run.return_value = _findings("x")

        outcome = _run()

        assert outcome == CheckOutcome("error", "edited config")
        env.fix_turn.assert_called_once()

    def test_skipped_result_is_logged_and_clean(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.binding("check@quick")
        env.run.return_value = ActionResult(status="skipped", summary="no files")

        with caplog.at_level("INFO"):
            assert _run().status == "clean"
        assert "check@quick skipped: no files" in caplog.text


class TestMissingFragment:
    @pytest.mark.parametrize("fragments", [{}, {"fix.check": ""}])
    def test_missing_or_empty_fragment_is_cap_without_turn(
        self, env: _Env, fragments: dict[str, str]
    ) -> None:
        """Real get_fragment returns "" for both a missing and an empty fragment."""
        loaded = _loaded("check@quick")
        loaded.toolkit.prompt_fragments.return_value = fragments
        env.load.return_value = loaded
        env.run.return_value = _findings("x")
        env.fragment.side_effect = real_get_fragment

        outcome = _run()

        assert outcome.status == "cap"
        assert "fix.check" in outcome.detail
        assert "0" in outcome.detail
        env.fix_turn.assert_not_called()

    def test_prompt_fragments_raising_is_cap_without_turn(self, env: _Env) -> None:
        """Real get_fragment returns "" when prompt_fragments() raises."""
        loaded = _loaded("check@quick")
        loaded.toolkit.prompt_fragments.side_effect = RuntimeError("boom")
        env.load.return_value = loaded
        env.run.return_value = _findings("x")
        env.fragment.side_effect = real_get_fragment

        outcome = _run()

        assert outcome.status == "cap"
        env.fix_turn.assert_not_called()

    def test_missing_fix_test_fragment(self, env: _Env) -> None:
        env.binding("check@quick", "test@quick")
        env.results({"test@quick": _findings("t")})
        env.fragment.side_effect = lambda _l, key: "" if key == "fix.test" else "F"

        outcome = _run()

        assert outcome.status == "cap"
        assert "fix.test" in outcome.detail
        env.fix_turn.assert_not_called()


class TestCheckTypeHints:
    def test_false_drops_check_requests_and_logs(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.binding("check@standard", "test@quick")

        with caplog.at_level("INFO"):
            assert _run(check_type_hints=False).status == "clean"

        assert env.requests_run() == ["test@quick"]
        assert "check@standard" in caplog.text

    def test_false_with_only_checks_skips(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.binding("check@quick")

        with caplog.at_level("INFO"):
            assert _run(check_type_hints=False) == CheckOutcome("clean")

        env.run.assert_not_called()
        assert "implement_final skipped" in caplog.text

    def test_empty_binding_skips(
        self, env: _Env, caplog: pytest.LogCaptureFixture
    ) -> None:
        env.binding(entry="implement_task")

        with caplog.at_level("INFO"):
            assert _run(entry="implement_task") == CheckOutcome("clean")

        env.run.assert_not_called()
        assert "implement_task skipped" in caplog.text

    def test_other_actions_are_ignored(self, env: _Env) -> None:
        env.binding("format@apply", "check@quick")

        assert _run().status == "clean"
        assert env.requests_run() == ["check@quick"]
