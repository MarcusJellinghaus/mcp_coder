"""Tests for `CommandToolkit.describe` and `CommandToolkit.run`."""

import logging
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.executable import resolve_executable
from mcp_coder.utils.subprocess_runner import CommandResult
from mcp_coder.utils.toolkit import ActionRequest, ActionResult

_JUNIT_TWO_FAILED = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="s" tests="3">
  <testcase classname="pkg.TestA" name="test_one">
    <failure message="expected 1, got 2">trace</failure>
  </testcase>
  <testcase classname="pkg.TestA" name="test_ok"/>
  <testcase classname="pkg.TestB" name="test_two">
    <error>boom</error>
  </testcase>
</testsuite></testsuites>
"""

_JUNIT_ALL_PASSED = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="s" tests="1">
  <testcase classname="pkg.TestA" name="test_ok"/>
</testsuite></testsuites>
"""


def _script(scripts: Path, name: str, body: str) -> None:
    (scripts / f"{name}.py").write_text(body, encoding="utf-8")


def _exit_script(scripts: Path, name: str, code: int, output: str = "") -> None:
    _script(scripts, name, f"import sys\nprint({output!r})\nsys.exit({code})\n")


def _run(
    config: dict[str, Any], project_dir: Path, action: str = "check", depth: str = "q"
) -> ActionResult:
    request = ActionRequest(
        action=action, depth=depth, project_dir=project_dir, params={}
    )
    return CommandToolkit(config).run(request)


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    return path


class TestResolveExe:
    """argv[0] resolution through `resolve_executable`."""

    @pytest.fixture(autouse=True)
    def _posix(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "platform", "linux")

    def test_project_relative(self, project_dir: Path) -> None:
        lint = project_dir / "tools" / "lint"
        lint.parent.mkdir()
        lint.write_text("", encoding="utf-8")
        lint.chmod(0o755)
        assert resolve_executable("tools/lint", project_dir) == str(lint)

    def test_bare_name(self, project_dir: Path, tmp_path: Path) -> None:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir()
        npm = bin_dir / "npm"
        npm.write_text("", encoding="utf-8")
        npm.chmod(0o755)
        assert resolve_executable("npm", project_dir, path=str(bin_dir)) == str(npm)
        assert resolve_executable("npm", project_dir, path=str(project_dir)) is None


class TestDescribe:
    """`describe` output."""

    def test_actions_in_config_order_with_grants(self) -> None:
        config = {
            "test": {"full": [{"argv": ["npm", "test"]}]},
            "check": {
                "quick": [{"argv": ["npm", "run", "lint"]}],
                "full": [
                    {"argv": ["npm", "run", "lint"]},
                    {"argv": ["npx", "tsc"]},
                ],
            },
        }
        info = CommandToolkit(config).describe()
        assert list(info.actions) == ["test", "check"]
        assert info.actions["check"] == ["quick", "full"]
        assert info.llm_permissions == {
            "test": {"full": ["Bash(npm test)"]},
            "check": {
                "quick": ["Bash(npm run lint)"],
                "full": ["Bash(npm run lint)", "Bash(npx tsc)"],
            },
        }
        assert info.params_schema["additionalProperties"] is False

    def test_no_grants_under_none(self) -> None:
        config = {"llm_permissions": "none", "check": {"q": [{"argv": ["npm"]}]}}
        info = CommandToolkit(config).describe()
        assert info.actions == {"check": ["q"]}
        assert info.llm_permissions == {"check": {"q": []}}

    def test_no_grants_under_global_error(self) -> None:
        config = {"bogus": 1, "check": {"q": [{"argv": ["npm"]}]}}
        info = CommandToolkit(config).describe()
        assert info.actions == {"check": ["q"]}
        assert info.llm_permissions == {}

    def test_depth_with_only_malformed_steps_declared(self) -> None:
        config: dict[str, Any] = {"check": {"q": [{"argv": []}]}}
        info = CommandToolkit(config).describe()
        assert info.actions == {"check": ["q"]}


class TestExitCodes:
    """Exit-code mapping of a single step."""

    def test_exit_zero_is_ok(self, fake_npm: Path, project_dir: Path) -> None:
        _exit_script(fake_npm, "lint", 0, "all good")
        result = _run({"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}, project_dir)
        assert result.status == "ok"
        assert result.findings == []
        assert "all good" in result.raw

    def test_exit_one_is_findings_keyed_by_name(
        self, fake_npm: Path, project_dir: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        _exit_script(fake_npm, "lint", 1, "src/a.ts: bad")
        config = {"check": {"q": [{"argv": ["fakenpm", "lint"], "name": "eslint"}]}}
        with caplog.at_level(logging.INFO):
            result = _run(config, project_dir)
        assert result.status == "findings"
        assert [(f.key, f.message) for f in result.findings] == [
            ("eslint", "eslint failed")
        ]
        assert result.fix_text.startswith("eslint\n")
        assert "src/a.ts: bad" in result.fix_text
        assert "regression detection is degraded for eslint" in caplog.text

    def test_finding_keyed_by_argv_without_name(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        _exit_script(fake_npm, "lint", 1)
        result = _run({"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}, project_dir)
        assert [f.key for f in result.findings] == ["fakenpm lint"]

    def test_unmapped_exit_code_is_error(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        _exit_script(fake_npm, "lint", 3)
        result = _run({"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}, project_dir)
        assert result.status == "error"

    def test_custom_exit_codes(self, fake_npm: Path, project_dir: Path) -> None:
        _exit_script(fake_npm, "lint", 3)
        _exit_script(fake_npm, "fmt", 0)
        config = {
            "check": {
                "q": [{"argv": ["fakenpm", "lint"], "exit_codes": {"3": "skipped"}}],
                "f": [{"argv": ["fakenpm", "fmt"], "exit_codes": {"0": "findings"}}],
            }
        }
        assert _run(config, project_dir).status == "skipped"
        assert _run(config, project_dir, depth="f").status == "findings"


class TestMerge:
    """Merging several steps."""

    def test_worst_status_and_findings_concatenated(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        _exit_script(fake_npm, "a", 1, "out a")
        _exit_script(fake_npm, "b", 0)
        _exit_script(fake_npm, "c", 1, "out c")
        config = {
            "check": {
                "q": [
                    {"argv": ["fakenpm", "a"]},
                    {"argv": ["fakenpm", "b"]},
                    {"argv": ["fakenpm", "c"]},
                ]
            }
        }
        result = _run(config, project_dir)
        assert result.status == "findings"
        assert [f.key for f in result.findings] == ["fakenpm a", "fakenpm c"]
        assert result.fix_text.index("out a") < result.fix_text.index("out c")
        assert result.summary.splitlines() == [
            "fakenpm a: findings",
            "fakenpm b: ok",
            "fakenpm c: findings",
        ]

    def test_error_beats_findings(self, fake_npm: Path, project_dir: Path) -> None:
        _exit_script(fake_npm, "a", 1)
        _exit_script(fake_npm, "b", 5)
        config = {
            "check": {"q": [{"argv": ["fakenpm", "a"]}, {"argv": ["fakenpm", "b"]}]}
        }
        result = _run(config, project_dir)
        assert result.status == "error"
        assert [f.key for f in result.findings] == ["fakenpm a"]

    def test_skipped_below_ok(self, fake_npm: Path, project_dir: Path) -> None:
        _exit_script(fake_npm, "a", 0)
        _exit_script(fake_npm, "b", 4)
        config = {
            "check": {
                "q": [
                    {"argv": ["fakenpm", "a"]},
                    {"argv": ["fakenpm", "b"], "exit_codes": {"4": "skipped"}},
                ]
            }
        }
        assert _run(config, project_dir).status == "ok"


class TestFailures:
    """Steps that cannot produce a result."""

    def test_timeout(self, fake_npm: Path, project_dir: Path) -> None:
        _script(fake_npm, "slow", "import time\nprint('partial')\ntime.sleep(30)\n")
        config = {"test": {"q": [{"argv": ["fakenpm", "slow"], "timeout": 1}]}}
        result = _run(config, project_dir, action="test")
        assert result.status == "error"
        assert result.fix_text == "fakenpm slow: timed out after 1 s"

    def test_execution_error(self, fake_npm: Path, project_dir: Path) -> None:
        _exit_script(fake_npm, "lint", 1)
        failed = CommandResult(
            return_code=1,
            stdout="",
            stderr="",
            timed_out=False,
            execution_error="permission denied",
        )
        with patch(
            "mcp_coder.toolkits.command.toolkit.execute_command",
            MagicMock(return_value=failed),
        ):
            result = _run(
                {"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}, project_dir
            )
        assert result.status == "error"
        assert result.findings == []
        assert "permission denied" in result.fix_text

    def test_argv0_not_found(self, project_dir: Path) -> None:
        config = {"check": {"q": [{"argv": ["no-such-tool-xyz-1196"]}]}}
        result = _run(config, project_dir)
        assert result.status == "error"
        assert "not found" in result.fix_text

    def test_fix_text_capped(self, fake_npm: Path, project_dir: Path) -> None:
        _script(
            fake_npm,
            "lint",
            "import sys\nfor i in range(500):\n    print(f'line {i}')\nsys.exit(1)\n",
        )
        result = _run({"check": {"q": [{"argv": ["fakenpm", "lint"]}]}}, project_dir)
        lines = result.fix_text.splitlines()
        assert lines[0] == "fakenpm lint"
        assert lines[1:] == [f"line {i}" for i in range(300, 500)]
        assert "line 0" in result.raw


class TestJunit:
    """The junit parser."""

    @staticmethod
    def _config() -> dict[str, Any]:
        return {
            "test": {
                "q": [
                    {
                        "argv": ["fakenpm", "test"],
                        "name": "jest",
                        "parser": "junit",
                        "report": "out/junit.xml",
                    }
                ]
            }
        }

    @staticmethod
    def _writes_report(scripts: Path, xml: str, code: int) -> None:
        _script(
            scripts,
            "test",
            "import pathlib, sys\n"
            "pathlib.Path('out').mkdir(exist_ok=True)\n"
            f"pathlib.Path('out/junit.xml').write_text({xml!r})\n"
            "print('runner output')\n"
            f"sys.exit({code})\n",
        )

    def test_two_failed_cases(self, fake_npm: Path, project_dir: Path) -> None:
        self._writes_report(fake_npm, _JUNIT_TWO_FAILED, 1)
        result = _run(self._config(), project_dir, action="test")
        assert result.status == "findings"
        assert [(f.key, f.message) for f in result.findings] == [
            ("pkg.TestA::test_one", "expected 1, got 2"),
            ("pkg.TestB::test_two", "boom"),
        ]
        assert result.fix_text.splitlines()[:3] == [
            "jest",
            "pkg.TestA::test_one: expected 1, got 2",
            "pkg.TestB::test_two: boom",
        ]
        assert "runner output" in result.fix_text

    def test_stale_report_deleted(self, fake_npm: Path, project_dir: Path) -> None:
        (project_dir / "out").mkdir()
        (project_dir / "out/junit.xml").write_text(_JUNIT_TWO_FAILED, "utf-8")
        _exit_script(fake_npm, "test", 1)
        result = _run(self._config(), project_dir, action="test")
        assert result.status == "error"
        assert not (project_dir / "out/junit.xml").exists()

    def test_no_failed_cases_gives_fallback(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        self._writes_report(fake_npm, _JUNIT_ALL_PASSED, 1)
        result = _run(self._config(), project_dir, action="test")
        assert result.status == "findings"
        assert [(f.key, f.message) for f in result.findings] == [
            ("jest", "jest failed")
        ]

    def test_unparsable_report_is_error(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        self._writes_report(fake_npm, "<not xml", 1)
        assert _run(self._config(), project_dir, action="test").status == "error"

    def test_exit_zero_ignores_report(self, fake_npm: Path, project_dir: Path) -> None:
        self._writes_report(fake_npm, _JUNIT_TWO_FAILED, 0)
        result = _run(self._config(), project_dir, action="test")
        assert result.status == "ok"
        assert result.findings == []


class TestConfigProblems:
    """Config problems surface as `error` results."""

    def test_malformed_step_errors_its_depth_only(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        _exit_script(fake_npm, "lint", 0)
        config = {
            "check": {
                "q": [{"argv": ["fakenpm", "lint"]}, {"argv": []}],
                "f": [{"argv": ["fakenpm", "lint"]}],
            }
        }
        result = _run(config, project_dir)
        assert result.status == "error"
        assert "check.q[2]" in result.fix_text
        assert _run(config, project_dir, depth="f").status == "ok"

    @pytest.mark.parametrize("arg", ["a b", "a,b"])
    @pytest.mark.parametrize("code,status", [(0, "ok"), (1, "findings")])
    def test_non_shell_safe_argv_still_runs(
        self, fake_npm: Path, project_dir: Path, arg: str, code: int, status: str
    ) -> None:
        _exit_script(fake_npm, "lint", code)
        config = {"check": {"q": [{"argv": ["fakenpm", "lint", arg]}]}}
        assert CommandToolkit(config).describe().llm_permissions == {"check": {"q": []}}
        assert _run(config, project_dir).status == status

    def test_global_error_fails_every_request(
        self, fake_npm: Path, project_dir: Path
    ) -> None:
        _exit_script(fake_npm, "lint", 0)
        config = {"timeout": 0, "check": {"q": [{"argv": ["fakenpm", "lint"]}]}}
        result = _run(config, project_dir)
        assert result.status == "error"
        assert result.summary.startswith("command toolkit config: ")

    @pytest.mark.parametrize("action,depth", [("test", "q"), ("check", "full")])
    def test_undeclared_action_or_depth(
        self, project_dir: Path, action: str, depth: str
    ) -> None:
        config = {"check": {"q": [{"argv": ["npm"]}]}}
        result = _run(config, project_dir, action=action, depth=depth)
        assert result.status == "error"
        assert result.summary == f"{action}@{depth} not declared"
