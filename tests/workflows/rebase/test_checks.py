"""Unit tests for the rebase check-baseline failure-key extraction.

Pure unit tests — no git, no subprocesses. Library dataclasses are constructed
directly (tests sit outside the ``mcp_checker_isolation`` import contract, which
only restricts src modules to the ``mcp_coder.mcp_tools_py`` shim).
"""

from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import pytest
from mcp_tools_py.code_checker_mypy import MypyMessage, MypyResult
from mcp_tools_py.code_checker_pylint import PylintMessage, PylintResult
from mcp_tools_py.code_checker_pytest import Collector, PytestReport, Summary, Test

from mcp_coder.workflows.rebase_checks import (
    CheckRunError,
    _mypy_failure_keys,
    _pylint_failure_keys,
    _pytest_failure_keys,
    _run_all_checks,
)


def _make_test(nodeid: str, outcome: str) -> Test:
    """Build a minimal pytest ``Test`` entry."""
    return Test(nodeid=nodeid, lineno=1, keywords=[], outcome=outcome)


def _make_report(
    tests: Optional[list[Test]] = None,
    collectors: Optional[list[Collector]] = None,
) -> PytestReport:
    """Build a minimal ``PytestReport`` around the given tests/collectors."""
    return PytestReport(
        created=0.0,
        duration=0.0,
        exitcode=0,
        root="/project",
        environment={},
        summary=Summary(collected=0, total=0),
        collectors=collectors,
        tests=tests,
    )


def _pytest_results(
    report: PytestReport, error_info: Optional[dict[str, Any]] = None
) -> dict[str, Any]:
    """Wrap a report in the dict shape ``check_code_with_pytest`` returns."""
    return {
        "success": True,
        "summary": {},
        "summary_text": "",
        "failed_tests_prompt": None,
        "test_results": report,
        "error_info": error_info,
    }


def _pylint_message(
    path: str, message_id: str, message: str, line: int = 10
) -> PylintMessage:
    """Build a ``PylintMessage`` with fixed incidental fields."""
    return PylintMessage(
        type="warning",
        module="mod",
        obj="",
        line=line,
        column=0,
        path=path,
        symbol="some-symbol",
        message=message,
        message_id=message_id,
    )


class TestPytestFailureKeys:
    """Keys from pytest results: failing outcomes only, by node ID."""

    def test_failing_outcomes_become_keys(self) -> None:
        """failed/error/unrecognized outcomes are keys; benign outcomes are not."""
        report = _make_report(
            tests=[
                _make_test("tests/test_a.py::test_fails", "failed"),
                _make_test("tests/test_a.py::test_errors", "error"),
                _make_test("tests/test_a.py::test_weird", "exploded"),
                _make_test("tests/test_a.py::test_passes", "passed"),
                _make_test("tests/test_a.py::test_skips", "skipped"),
                _make_test("tests/test_a.py::test_xfails", "xfailed"),
                _make_test("tests/test_a.py::test_xpasses", "xpassed"),
            ]
        )
        keys = _pytest_failure_keys(_pytest_results(report))
        assert keys == {
            ("pytest", "tests/test_a.py::test_fails"),
            ("pytest", "tests/test_a.py::test_errors"),
            ("pytest", "tests/test_a.py::test_weird"),
        }

    def test_failed_collector_becomes_key(self) -> None:
        """A collector with outcome 'failed' (collection error) is a key."""
        report = _make_report(
            collectors=[
                Collector(nodeid="tests/test_broken.py", outcome="failed", result=[]),
                Collector(nodeid="tests/test_ok.py", outcome="passed", result=[]),
            ]
        )
        keys = _pytest_failure_keys(_pytest_results(report))
        assert keys == {("pytest", "tests/test_broken.py")}

    def test_skipped_collector_produces_no_key(self) -> None:
        """A skipped collector (module-level importorskip) is not a regression."""
        report = _make_report(
            collectors=[
                Collector(nodeid="tests/test_optional.py", outcome="skipped", result=[])
            ]
        )
        assert _pytest_failure_keys(_pytest_results(report)) == set()

    def test_empty_report_yields_no_keys(self) -> None:
        """tests=None and collectors=None yield an empty key set."""
        assert _pytest_failure_keys(_pytest_results(_make_report())) == set()

    def test_crash_dict_raises_check_run_error(self) -> None:
        """success=False without test_results (crash path) is infrastructure."""
        crash: dict[str, Any] = {"success": False, "error": "Test run timed out"}
        with pytest.raises(CheckRunError):
            _pytest_failure_keys(crash)

    def test_missing_test_results_raises_check_run_error(self) -> None:
        """success=True but no test_results is still infrastructure."""
        with pytest.raises(CheckRunError):
            _pytest_failure_keys({"success": True, "test_results": None})

    def test_error_info_with_failures_is_not_infrastructure(self) -> None:
        """error_info set for exit 1 (ordinary failures) yields keys, no raise."""
        report = _make_report(
            tests=[_make_test("tests/test_a.py::test_fails", "failed")]
        )
        results = _pytest_results(
            report, error_info={"exit_code": 1, "description": "tests failed"}
        )
        assert _pytest_failure_keys(results) == {
            ("pytest", "tests/test_a.py::test_fails")
        }


class TestPylintFailureKeys:
    """Keys from pylint results: (pylint, path, message_id, message)."""

    def test_message_becomes_key_without_line(self) -> None:
        """A message maps to a key carrying path/id/message but no line/column."""
        result = PylintResult(
            return_code=4,
            messages=[_pylint_message("src/mod.py", "W0611", "Unused import os")],
        )
        assert _pylint_failure_keys(result) == {
            ("pylint", "src/mod.py", "W0611", "Unused import os")
        }

    def test_line_insensitive(self) -> None:
        """Two messages identical except line number collapse to one key."""
        result = PylintResult(
            return_code=4,
            messages=[
                _pylint_message("src/mod.py", "W0611", "Unused import os", line=3),
                _pylint_message("src/mod.py", "W0611", "Unused import os", line=99),
            ],
        )
        assert len(_pylint_failure_keys(result)) == 1

    def test_error_raises_check_run_error(self) -> None:
        """result.error set means pylint failed to run."""
        result = PylintResult(return_code=32, messages=[], error="pylint crashed")
        with pytest.raises(CheckRunError):
            _pylint_failure_keys(result)

    def test_clean_result_yields_no_keys(self) -> None:
        """No messages, no error: empty key set."""
        assert _pylint_failure_keys(PylintResult(return_code=0, messages=[])) == set()


class TestMypyFailureKeys:
    """Keys from mypy results: (mypy, file, code, message), errors only."""

    def test_only_error_severity_becomes_key(self) -> None:
        """Notes and other severities are ignored."""
        result = MypyResult(
            return_code=1,
            messages=[
                MypyMessage(
                    file="src/mod.py",
                    line=5,
                    column=1,
                    severity="error",
                    message="Incompatible return value",
                    code="return-value",
                ),
                MypyMessage(
                    file="src/mod.py",
                    line=5,
                    column=1,
                    severity="note",
                    message="See docs",
                    code=None,
                ),
            ],
        )
        assert _mypy_failure_keys(result) == {
            ("mypy", "src/mod.py", "return-value", "Incompatible return value")
        }

    def test_none_code_maps_to_empty_string(self) -> None:
        """code=None becomes "" in the key."""
        result = MypyResult(
            return_code=1,
            messages=[
                MypyMessage(
                    file="src/mod.py",
                    line=7,
                    column=1,
                    severity="error",
                    message="Cannot find module",
                    code=None,
                )
            ],
        )
        assert _mypy_failure_keys(result) == {
            ("mypy", "src/mod.py", "", "Cannot find module")
        }

    def test_line_insensitive(self) -> None:
        """Two errors identical except line number collapse to one key."""
        result = MypyResult(
            return_code=1,
            messages=[
                MypyMessage(
                    file="src/mod.py",
                    line=5,
                    column=1,
                    severity="error",
                    message="Incompatible types",
                    code="assignment",
                ),
                MypyMessage(
                    file="src/mod.py",
                    line=50,
                    column=9,
                    severity="error",
                    message="Incompatible types",
                    code="assignment",
                ),
            ],
        )
        assert len(_mypy_failure_keys(result)) == 1

    def test_error_raises_check_run_error(self) -> None:
        """result.error set means mypy failed to run."""
        result = MypyResult(return_code=2, messages=[], error="mypy blew up")
        with pytest.raises(CheckRunError):
            _mypy_failure_keys(result)


class TestRegressionSemantics:
    """Documents the comparison contract: regression = verification - baseline."""

    def test_set_difference_flags_only_new_keys(self) -> None:
        """Pre-existing failures never block; only new keys are regressions."""
        baseline = {
            ("pytest", "tests/test_old.py::test_flaky"),
            ("pylint", "src/mod.py", "W0611", "Unused import os"),
        }
        verification = {
            ("pytest", "tests/test_old.py::test_flaky"),
            ("mypy", "src/mod.py", "arg-type", "Bad argument"),
        }
        assert verification - baseline == {
            ("mypy", "src/mod.py", "arg-type", "Bad argument")
        }

    def test_fixed_failures_are_not_regressions(self) -> None:
        """Keys that vanish between baseline and verification are ignored."""
        baseline = {("pylint", "src/mod.py", "W0611", "Unused import os")}
        verification: set[tuple[str, ...]] = set()
        assert verification - baseline == set()


class TestRunAllChecks:
    """_run_all_checks unions the three key sets and wraps run failures."""

    def test_unions_all_three_key_sets(self, tmp_path: Path) -> None:
        """Keys from pytest, pylint and mypy are merged into one set."""
        report = _make_report(
            tests=[_make_test("tests/test_a.py::test_fails", "failed")]
        )
        pylint_result = PylintResult(
            return_code=4,
            messages=[_pylint_message("src/mod.py", "W0611", "Unused import os")],
        )
        mypy_result = MypyResult(
            return_code=1,
            messages=[
                MypyMessage(
                    file="src/mod.py",
                    line=5,
                    column=1,
                    severity="error",
                    message="Bad argument",
                    code="arg-type",
                )
            ],
        )
        with (
            patch(
                "mcp_coder.workflows.rebase_checks.run_pytest_check",
                return_value=_pytest_results(report),
            ),
            patch(
                "mcp_coder.workflows.rebase_checks.run_pylint_check",
                return_value=pylint_result,
            ),
            patch(
                "mcp_coder.workflows.rebase_checks.run_mypy_check",
                return_value=mypy_result,
            ),
        ):
            keys = _run_all_checks(tmp_path)

        assert keys == {
            ("pytest", "tests/test_a.py::test_fails"),
            ("pylint", "src/mod.py", "W0611", "Unused import os"),
            ("mypy", "src/mod.py", "arg-type", "Bad argument"),
        }

    def test_clean_checks_yield_empty_set(self, tmp_path: Path) -> None:
        """All-green checks produce an empty key set."""
        with (
            patch(
                "mcp_coder.workflows.rebase_checks.run_pytest_check",
                return_value=_pytest_results(_make_report()),
            ),
            patch(
                "mcp_coder.workflows.rebase_checks.run_pylint_check",
                return_value=PylintResult(return_code=0, messages=[]),
            ),
            patch(
                "mcp_coder.workflows.rebase_checks.run_mypy_check",
                return_value=MypyResult(return_code=0, messages=[]),
            ),
        ):
            assert _run_all_checks(tmp_path) == set()

    def test_wrapper_exception_becomes_check_run_error(self, tmp_path: Path) -> None:
        """An unexpected exception from a wrapper is wrapped, naming the checker."""
        with patch(
            "mcp_coder.workflows.rebase_checks.run_pytest_check",
            side_effect=RuntimeError("No pyproject.toml found"),
        ):
            with pytest.raises(CheckRunError, match="pytest"):
                _run_all_checks(tmp_path)

    def test_check_run_error_names_failing_checker(self, tmp_path: Path) -> None:
        """A CheckRunError from an extractor is re-raised naming the checker."""
        with (
            patch(
                "mcp_coder.workflows.rebase_checks.run_pytest_check",
                return_value=_pytest_results(_make_report()),
            ),
            patch(
                "mcp_coder.workflows.rebase_checks.run_pylint_check",
                return_value=PylintResult(
                    return_code=32, messages=[], error="pylint crashed"
                ),
            ),
        ):
            with pytest.raises(CheckRunError, match="pylint"):
                _run_all_checks(tmp_path)
