"""Deterministic check layer for the ``mcp-coder rebase`` workflow.

Runs pytest, pylint and mypy and reduces their results to line-insensitive
failure keys so the orchestrator in ``rebase.py`` can compare a pre-rebase
baseline against a post-rebase verification run as a pure set difference.
"""

from pathlib import Path
from typing import Any, Callable

from mcp_coder.mcp_tools_py import (
    MypyResult,
    PylintResult,
    run_mypy_check,
    run_pylint_check,
    run_pytest_check,
)


class CheckRunError(Exception):
    """A check failed to RUN (infrastructure), as opposed to reporting failures."""


FailureKey = tuple[str, ...]
"""``("pytest", nodeid)`` | ``("pylint" | "mypy", file, code, message)``.

Line numbers never enter a key: a rebase shifts lines, and merely-moved
findings must not read as regressions (regression = verification − baseline).
"""

_PYTEST_NON_FAILING_OUTCOMES = ("passed", "skipped", "xfailed", "xpassed")


def _pytest_failure_keys(results: dict[str, Any]) -> set[FailureKey]:
    """Reduce a pytest result dict to a set of failure keys.

    Failing outcomes (``failed``/``error``/unrecognized) and failed collectors
    become keys. ``skipped``/``xfailed``/``xpassed`` tests and skipped
    collectors (module-level ``importorskip``) do not: a rebase can pull new
    self-skipping tests in from the base branch, and a skip the LLM cannot
    "fix" must not read as a regression.

    ``error_info`` is deliberately ignored — the library sets it for ANY
    non-zero pytest exit, including exit 1 (ordinary failures) and exit 2
    (collection errors, report still parsed). Genuine infrastructure failures
    take the crash path (``success=False``, no ``test_results``).

    Returns:
        The set of failure keys derived from failing tests and collectors.

    Raises:
        CheckRunError: If pytest failed to run.
    """
    if results.get("success") is not True or results.get("test_results") is None:
        raise CheckRunError(
            f"failed to run: {results.get('error') or 'no test results produced'}"
        )
    report = results["test_results"]
    keys: set[FailureKey] = {
        ("pytest", test.nodeid)
        for test in report.tests or []
        if test.outcome not in _PYTEST_NON_FAILING_OUTCOMES
    }
    keys |= {
        ("pytest", collector.nodeid)
        for collector in report.collectors or []
        if collector.outcome == "failed"
    }
    return keys


def _pylint_failure_keys(result: PylintResult) -> set[FailureKey]:
    """Reduce a ``PylintResult`` to line-insensitive failure keys.

    Returns:
        The set of failure keys derived from the pylint messages.

    Raises:
        CheckRunError: If pylint failed to run (``result.error`` set).
    """
    if result.error:
        raise CheckRunError(f"failed to run: {result.error}")
    return {("pylint", m.path, m.message_id, m.message) for m in result.messages}


def _mypy_failure_keys(result: MypyResult) -> set[FailureKey]:
    """Reduce a ``MypyResult`` to line-insensitive failure keys (errors only).

    Returns:
        The set of failure keys derived from the mypy error messages.

    Raises:
        CheckRunError: If mypy failed to run (``result.error`` set).
    """
    if result.error:
        raise CheckRunError(f"failed to run: {result.error}")
    return {
        ("mypy", m.file, m.code or "", m.message)
        for m in result.messages
        if m.severity == "error"
    }


def _run_all_checks(project_dir: Path) -> set[FailureKey]:
    """Run pytest, pylint and mypy and union their failure keys.

    Findings (failed tests, lint messages, type errors) become keys; a check
    that fails to *run* raises ``CheckRunError`` naming the checker.

    Returns:
        The union of failure keys across all three checks.

    Raises:
        CheckRunError: If any check fails to run.
    """
    checkers: list[tuple[str, Callable[[], set[FailureKey]]]] = [
        ("pytest", lambda: _pytest_failure_keys(run_pytest_check(project_dir))),
        ("pylint", lambda: _pylint_failure_keys(run_pylint_check(project_dir))),
        ("mypy", lambda: _mypy_failure_keys(run_mypy_check(project_dir))),
    ]
    keys: set[FailureKey] = set()
    for name, run_checker in checkers:
        try:
            keys |= run_checker()
        except CheckRunError as exc:
            raise CheckRunError(f"{name}: {exc}") from exc
        except Exception as exc:  # pylint: disable=broad-exception-caught
            raise CheckRunError(f"{name}: {exc}") from exc
    return keys
