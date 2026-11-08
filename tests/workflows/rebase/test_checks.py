"""Unit tests for the rebase check layer over the ``rebase`` bindings.

``load_toolkit`` and ``run_binding`` are patched to return ``ActionResult``s
directly, except for one test that runs the real ``PythonToolkit``.
"""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.toolkit import ActionResult, Finding
from mcp_coder.utils.toolkit_runner import LoadedToolkit, load_toolkit_config
from mcp_coder.workflows import rebase_checks
from mcp_coder.workflows.rebase_checks import CheckRunError, _run_all_checks

_LOAD = "mcp_coder.workflows.rebase_checks.load_toolkit"
_RUN = "mcp_coder.workflows.rebase_checks.run_binding"


def _findings(*keys: str) -> ActionResult:
    """Build a ``findings`` result carrying one finding per key."""
    return ActionResult(
        "findings", "found", [Finding(key=key, message=key) for key in keys]
    )


def _run_with(
    tmp_path: Path, results: list[tuple[str, ActionResult]], automated: bool = False
) -> tuple[set[str], MagicMock]:
    """Run ``_run_all_checks`` with a patched toolkit returning ``results``.

    Returns:
        ``(keys, run_binding_mock)``.
    """
    with (
        patch(_LOAD, return_value=MagicMock()),
        patch(_RUN, return_value=results) as mock_run,
    ):
        keys = _run_all_checks(tmp_path, automated)
    return keys, mock_run


class TestRunAllChecks:
    """_run_all_checks prefixes finding keys with the action and maps errors."""

    def test_findings_become_action_prefixed_keys(self, tmp_path: Path) -> None:
        """``ok`` adds nothing; ``findings`` adds ``"<action>: <key>"`` keys."""
        keys, _ = _run_with(
            tmp_path,
            [
                ("check@standard", _findings("a.py|E1|msg")),
                ("test@standard", _findings("tests/t.py::test_x")),
                ("test@quick", ActionResult("ok", "clean")),
            ],
        )
        assert keys == {"check: a.py|E1|msg", "test: tests/t.py::test_x"}

    def test_clean_results_yield_empty_set(self, tmp_path: Path) -> None:
        """All-``ok`` results produce an empty key set."""
        keys, _ = _run_with(tmp_path, [("check@standard", ActionResult("ok", "ok"))])
        assert keys == set()

    @pytest.mark.parametrize(
        ("automated", "entry"),
        [(False, "rebase"), (True, "rebase_automated")],
    )
    def test_entry_follows_automated(
        self, tmp_path: Path, automated: bool, entry: str
    ) -> None:
        """``automated`` selects the ``rebase_automated`` binding."""
        _, mock_run = _run_with(tmp_path, [], automated=automated)
        assert mock_run.call_args.args[1:] == (tmp_path, entry)

    def test_error_result_raises_naming_request(self, tmp_path: Path) -> None:
        """An ``error`` result is an infrastructure failure naming the request."""
        with pytest.raises(CheckRunError, match="test@standard: pytest crashed"):
            _run_with(
                tmp_path,
                [
                    ("check@standard", ActionResult("ok", "ok")),
                    ("test@standard", ActionResult("error", "pytest crashed")),
                ],
            )

    def test_skipped_result_adds_no_keys_and_logs(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A ``skipped`` result adds no keys and is logged."""
        with caplog.at_level(logging.INFO, logger=rebase_checks.__name__):
            keys, _ = _run_with(
                tmp_path, [("test@standard", ActionResult("skipped", "no tests"))]
            )
        assert keys == set()
        assert "test@standard skipped: no tests" in caplog.text

    def test_toolkit_load_failure_raises(self, tmp_path: Path) -> None:
        """A config/registry problem from ``load_toolkit`` is a CheckRunError."""
        with patch(_LOAD, side_effect=ValueError("bad config")):
            with pytest.raises(CheckRunError, match="toolkit: bad config"):
                _run_all_checks(tmp_path)

    def test_same_key_from_two_actions_stays_distinct(self, tmp_path: Path) -> None:
        """The action prefix keeps equal finding keys from colliding."""
        keys, _ = _run_with(
            tmp_path,
            [
                ("check@standard", _findings("same")),
                ("test@standard", _findings("same")),
            ],
        )
        assert keys == {"check: same", "test: same"}


class TestRegressionSemantics:
    """Documents the comparison contract: regression = verification - baseline."""

    def test_set_difference_flags_only_new_keys(self) -> None:
        """Pre-existing failures never block; only new keys are regressions."""
        baseline = {"test: tests/test_old.py::test_flaky", "check: src/m.py|W0611|x"}
        verification = {
            "test: tests/test_old.py::test_flaky",
            "check: src/m.py|arg-type|Bad argument",
        }
        assert verification - baseline == {"check: src/m.py|arg-type|Bad argument"}


def test_real_toolkit_failing_test(tmp_path: Path) -> None:
    """The real PythonToolkit's failing test becomes a ``test:`` key."""
    from mcp_tools_py.toolkit import PythonToolkit

    (tmp_path / "pyproject.toml").write_text(
        '[tool.mcp-coder.toolkit.bindings]\nrebase = ["test@standard"]\n',
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text(
        "def test_pass():\n    assert True\n\n\ndef test_fail():\n    assert False\n",
        encoding="utf-8",
    )
    toolkit = PythonToolkit()
    loaded = LoadedToolkit(
        "mcp-tools-py", toolkit, toolkit.describe(), load_toolkit_config(tmp_path)
    )
    with patch(_LOAD, return_value=loaded):
        assert _run_all_checks(tmp_path) == {"test: tests/test_fail.py::test_fail"}
