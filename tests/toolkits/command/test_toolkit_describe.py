"""Tests for `CommandToolkit.verify` and `CommandToolkit.prompt_fragments`."""

from pathlib import Path
from typing import Any

import pytest

from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils.toolkit import VerifyItem

_LINT = {"argv": ["fakenpm", "lint"]}
_UNIT = {"argv": ["fakenpm", "test", "--unit"]}


def _verify(
    config: dict[str, Any], project_dir: Path, action: str | None = None
) -> list[VerifyItem]:
    return CommandToolkit(config).verify(project_dir, action)


def _errors(items: list[VerifyItem]) -> list[str]:
    return [i.message for i in items if i.status == "error"]


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    path = tmp_path / "project"
    path.mkdir()
    return path


@pytest.mark.usefixtures("fake_npm")
class TestVerify:
    """verify reports config problems and missing executables."""

    def test_clean_config_is_single_ok(self, project_dir: Path) -> None:
        items = _verify(
            {"check": {"quick": [_LINT]}, "test": {"quick": [_UNIT]}}, project_dir
        )
        assert items == [VerifyItem(name="command", status="ok")]

    @pytest.mark.parametrize(
        ("config", "fragment"),
        [
            ({"bogus": 1, "check": {"q": [_LINT]}}, "unknown top-level key 'bogus'"),
            ({"parser": "xml", "check": {"q": [_LINT]}}, "parser must be one of"),
            ({"exit_codes": {"x": "ok"}, "check": {"q": [_LINT]}}, "exit_codes key"),
            ({"timeout": 0, "check": {"q": [_LINT]}}, "timeout must be"),
            ({"llm_permissions": "all", "check": {"q": [_LINT]}}, "llm_permissions"),
            ({"check": {"q": [{"argv": []}]}}, "argv must not be empty"),
            (
                {"test": {"q": [{"argv": ["fakenpm", "t"], "parser": "junit"}]}},
                "requires report",
            ),
            (
                {"test": {"q": [{"argv": ["fakenpm", "t"], "report": "r.xml"}]}},
                "report is only allowed",
            ),
            (
                {
                    "test": {
                        "q": [
                            {
                                "argv": ["fakenpm", "t"],
                                "parser": "junit",
                                "report": "../r.xml",
                            }
                        ]
                    }
                },
                "inside the project",
            ),
            ({"check": {"q": [{"argv": ["fakenpm"], "x": 1}]}}, "unknown key 'x'"),
        ],
    )
    def test_config_errors(
        self, project_dir: Path, config: dict[str, Any], fragment: str
    ) -> None:
        errors = _errors(_verify(config, project_dir))
        assert any(fragment in e for e in errors), errors

    def test_unsafe_element_is_warning(self, project_dir: Path) -> None:
        items = _verify({"check": {"q": [{"argv": ["fakenpm", "a b"]}]}}, project_dir)
        assert [i.status for i in items] == ["warning"]
        assert "not shell-safe" in items[0].message

    def test_missing_executable_is_error(self, project_dir: Path) -> None:
        items = _verify({"check": {"q": [{"argv": ["no-such-tool-xyz"]}]}}, project_dir)
        assert _errors(items) == ["no-such-tool-xyz: 'no-such-tool-xyz' not found"]

    def test_undeclared_action_is_error(self, project_dir: Path) -> None:
        items = _verify({"check": {"q": [_LINT]}}, project_dir, action="format")
        assert _errors(items) == ["format: not declared"]

    def test_global_errors_shown_for_any_action(self, project_dir: Path) -> None:
        config = {"bogus": 1, "format": {"q": [_LINT]}, "check": {"q": [_LINT]}}
        errors = _errors(_verify(config, project_dir, action="format"))
        assert any("unknown top-level key 'bogus'" in e for e in errors)

    def test_other_action_errors_hidden(self, project_dir: Path) -> None:
        config = {
            "format": {"q": [_LINT]},
            "check": {"q": [{"argv": []}, {"argv": ["no-such-tool-xyz"]}]},
        }
        items = _verify(config, project_dir, action="format")
        assert items == [VerifyItem(name="command", status="ok")]
        assert len(_errors(_verify(config, project_dir, action="check"))) == 2


class TestPromptFragments:
    """prompt_fragments lists the exact re-run commands."""

    def test_keys(self) -> None:
        fragments = CommandToolkit({"check": {"q": [_LINT]}}).prompt_fragments()
        assert set(fragments) == {
            "language_context",
            "check_instructions",
            "check_instructions.unattended",
            "fix.check",
            "fix.test",
        }
        assert fragments["language_context"] == ""
        assert fragments["fix.check"]
        assert fragments["fix.test"]

    def test_grants_verbatim_and_ungranted_marked(self) -> None:
        config = {
            "check": {"q": [_LINT, {"argv": ["fakenpm", "a b"], "name": "spaced"}]},
            "test": {"q": [_UNIT, _LINT]},
        }
        text = CommandToolkit(config).prompt_fragments()["check_instructions"]
        lines = text.splitlines()
        assert lines[0].startswith("Re-run the checks with these exact commands")
        assert lines[1:] == [
            "- `fakenpm lint`",
            "- spaced: can't be re-run; results come in the fix prompt",
            "- `fakenpm test --unit`",
        ]

    def test_unattended_only_when_declared(self) -> None:
        without = CommandToolkit({"test": {"q": [_UNIT]}}).prompt_fragments()
        assert without["check_instructions.unattended"] == ""

        config = {"check": {"q": [_LINT]}, "test": {"unattended": [_UNIT]}}
        text = CommandToolkit(config).prompt_fragments()[
            "check_instructions.unattended"
        ]
        assert "- `fakenpm test --unit`" in text
        assert "fakenpm lint" not in text

    @pytest.mark.parametrize(
        "config",
        [
            {"llm_permissions": "none", "test": {"unattended": [_UNIT]}},
            {"bogus": 1, "test": {"unattended": [_UNIT]}},
        ],
    )
    def test_no_grants_empty_instructions(self, config: dict[str, Any]) -> None:
        fragments = CommandToolkit(config).prompt_fragments()
        assert fragments["check_instructions"] == ""
        assert fragments["check_instructions.unattended"] == ""
        assert fragments["fix.check"]
        assert fragments["fix.test"]
