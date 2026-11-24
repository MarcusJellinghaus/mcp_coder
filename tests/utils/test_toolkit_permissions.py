"""Tests for llm_permissions, bash_grants_of and mcp_servers_of in toolkit_runner."""

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.toolkits.command import CommandToolkit
from mcp_coder.utils import toolkit_runner
from mcp_coder.utils.prompt_slots import RERUN_INTRO, resolve_prompt_slots
from mcp_coder.utils.toolkit import ActionRequest, ActionResult, Toolkit, ToolkitInfo
from mcp_coder.utils.toolkit_runner import (
    bash_grants_of,
    llm_permissions,
    mcp_servers_of,
)

_PERMISSIONS: dict[str, dict[str, list[str]]] = {
    "format": {"apply": ["Bash(npm run fmt)"]},
    "check": {"quick": ["Bash(npm run lint)", "mcp__tools__check"]},
    "test": {"standard": ["Bash(npm test)", "Bash(npm run lint)"]},
}


class PermToolkit(Toolkit):
    """Fake toolkit declaring Bash and MCP permissions."""

    def describe(self) -> ToolkitInfo:
        return ToolkitInfo(
            actions={action: list(depths) for action, depths in _PERMISSIONS.items()},
            params_schema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
            llm_permissions=_PERMISSIONS,
        )

    def run(self, request: ActionRequest) -> ActionResult:
        return ActionResult("ok", "")


@pytest.fixture(name="perm_project")
def _perm_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Project dir whose toolkit is PermToolkit; resets the warn-once flag."""
    monkeypatch.setattr(toolkit_runner, "_toolkit_class", lambda _name: PermToolkit)
    monkeypatch.setattr(toolkit_runner, "_bash_drop_warned", False)
    (tmp_path / "mcp-coder.toml").write_text(
        '[tool.mcp-coder.toolkit]\ntoolkit = "perm"\n', encoding="utf-8"
    )
    return tmp_path


def test_union_over_everything_deduplicated(perm_project: Path) -> None:
    """entry=None returns every permission once, in order."""
    assert llm_permissions(perm_project, "claude") == [
        "Bash(npm run fmt)",
        "Bash(npm run lint)",
        "mcp__tools__check",
        "Bash(npm test)",
    ]


def test_entry_uses_resolved_depth(perm_project: Path) -> None:
    """rebase asks check@standard; only check.quick exists, so its grants apply."""
    assert llm_permissions(perm_project, "claude", "rebase") == [
        "Bash(npm run lint)",
        "mcp__tools__check",
        "Bash(npm test)",
    ]


def test_implement_task_default_grants_check_quick(perm_project: Path) -> None:
    """implement_task defaults to check@quick, so its grants apply."""
    assert llm_permissions(perm_project, "claude", "implement_task") == [
        "Bash(npm run lint)",
        "mcp__tools__check",
    ]


def test_entry_with_no_requests(perm_project: Path) -> None:
    """An entry bound to nothing grants no permissions."""
    (perm_project / "mcp-coder.toml").write_text(
        '[tool.mcp-coder.toolkit]\ntoolkit = "perm"\n'
        "[tool.mcp-coder.toolkit.bindings]\nimplement_task = []\n",
        encoding="utf-8",
    )
    assert not llm_permissions(perm_project, "claude", "implement_task")


def test_bash_grants_of_keeps_only_bash() -> None:
    """Only Bash(...) entries survive."""
    assert bash_grants_of(["Bash(npm test)", "mcp__x__y", "Bash(ls)"]) == [
        "Bash(npm test)",
        "Bash(ls)",
    ]


@pytest.mark.parametrize(
    ("permissions", "expected"),
    [
        ([], ["mcp-workspace"]),
        (["Bash(npm test)"], ["mcp-workspace"]),
        (
            [
                "mcp__mcp-tools-py__run_pytest_check",
                "mcp__a__x",
                "mcp__mcp-workspace__git",
            ],
            ["mcp-workspace", "a", "mcp-tools-py"],
        ),
    ],
)
def test_mcp_servers_of(permissions: list[str], expected: list[str]) -> None:
    """mcp-workspace first, then the other mcp__<server>__ prefixes sorted."""
    assert mcp_servers_of(permissions) == expected


def test_python_toolkit_has_no_bash_grants(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The default PythonToolkit grants MCP tools only."""
    monkeypatch.setattr(toolkit_runner, "_bash_drop_warned", False)
    perms = llm_permissions(tmp_path, "claude")
    assert perms
    assert not bash_grants_of(perms)


@pytest.mark.parametrize("provider", ["copilot", "langchain"])
def test_non_claude_drops_bash_and_warns_once(
    perm_project: Path, provider: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Bash entries are dropped for other providers, with a single warning."""
    with caplog.at_level(logging.WARNING, logger=toolkit_runner.__name__):
        first = llm_permissions(perm_project, provider)
        second = llm_permissions(perm_project, provider)
    assert first == second == ["mcp__tools__check"]
    warnings = [r for r in caplog.records if "Bash grants dropped" in r.getMessage()]
    assert len(warnings) == 1
    assert provider in warnings[0].getMessage()


def test_no_warning_when_nothing_dropped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """A toolkit without Bash grants never warns."""
    monkeypatch.setattr(toolkit_runner, "_bash_drop_warned", False)
    with caplog.at_level(logging.WARNING, logger=toolkit_runner.__name__):
        llm_permissions(tmp_path, "copilot")
    assert "Bash grants dropped" not in caplog.text


def test_provider_falls_back_to_env(
    perm_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty provider resolves like prompt_llm does."""
    monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "copilot")
    assert llm_permissions(perm_project, "") == ["mcp__tools__check"]
    monkeypatch.delenv("MCP_CODER_LLM_PROVIDER")
    assert "Bash(npm test)" in llm_permissions(perm_project, "")


def test_load_failure_returns_empty(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An invalid config yields no grants and a warning."""
    (tmp_path / "mcp-coder.toml").write_text(
        "[tool.mcp-coder.toolkit]\nbogus = 1\n", encoding="utf-8"
    )
    with caplog.at_level(logging.WARNING, logger=toolkit_runner.__name__):
        result: Any = llm_permissions(tmp_path, "claude")
    assert result == []
    assert "No toolkit grants" in caplog.text


# One distinct command per declared step of the real command toolkit
_COMMANDS: dict[str, str] = {
    "check.quick": "npm run lint-quick",
    "check.standard": "npm run lint",
    "check.full": "npm run lint-full",
    "test.quick": "npm run test-quick",
    "test.unattended": "npm run test-ci",
    "test.mutation": "npm run test-mutation",
    "format.apply": "npm run fmt",
    "format.check": "npm run fmt-check",
}
_NEVER_GRANTED = ("check.full", "test.mutation", "format.apply", "format.check")


@pytest.fixture(name="command_project")
def _command_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Real command-toolkit project with default bindings and every step above."""
    monkeypatch.setattr(toolkit_runner, "_toolkit_class", lambda _name: CommandToolkit)
    monkeypatch.setattr(toolkit_runner, "_bash_drop_warned", False)
    steps = "".join(
        f"{key} = [{{ argv = {json.dumps(command.split())} }}]\n"
        for key, command in _COMMANDS.items()
    )
    (tmp_path / "mcp-coder.toml").write_text(
        '[tool.mcp-coder.toolkit]\ntoolkit = "command"\n\n'
        f"[tool.mcp-coder.toolkit.command]\n{steps}",
        encoding="utf-8",
    )
    return tmp_path


def _grant(key: str) -> str:
    return f"Bash({_COMMANDS[key]})"


def test_command_implement_task_grants_only_check_quick(command_project: Path) -> None:
    """implement_task requests check@quick only."""
    perms = llm_permissions(command_project, "claude", "implement_task")
    assert bash_grants_of(perms) == [_grant("check.quick")]


def test_command_implement_final_grants_its_two_depths(command_project: Path) -> None:
    """implement_final requests check@standard and test@quick only."""
    perms = llm_permissions(command_project, "claude", "implement_final")
    assert bash_grants_of(perms) == [_grant("check.standard"), _grant("test.quick")]


@pytest.mark.parametrize("entry", ["implement_task", "implement_final"])
def test_command_unrequested_depths_get_no_grant(
    command_project: Path, entry: str
) -> None:
    """Depths no implement binding requests are never granted."""
    perms = llm_permissions(command_project, "claude", entry)
    for key in _NEVER_GRANTED:
        assert _grant(key) not in perms


def _rerun_text(project: Path, grants: list[str]) -> str:
    return resolve_prompt_slots("[check_instructions]", project, "claude", grants)[
        "check_instructions"
    ]


def test_task_session_rerun_list_matches_its_grants(command_project: Path) -> None:
    """The task session lists exactly the implement_task and implement_final steps."""
    perms = llm_permissions(
        command_project, "claude", "implement_task"
    ) + llm_permissions(command_project, "claude", "implement_final")
    grants = bash_grants_of(list(dict.fromkeys(perms)))

    text = _rerun_text(command_project, grants)

    assert text.startswith(RERUN_INTRO)
    listed = text[len(RERUN_INTRO) :].split("\n")
    assert listed == [
        f"- `{_COMMANDS[key]}`"
        for key in ("check.quick", "check.standard", "test.quick")
    ]
    for key in _NEVER_GRANTED:
        assert _COMMANDS[key] not in text


def test_final_session_rerun_list_omits_unrequested(command_project: Path) -> None:
    """Finalisation and CI fix list no command of an unrequested depth."""
    grants = bash_grants_of(
        llm_permissions(command_project, "claude", "implement_final")
    )

    text = _rerun_text(command_project, grants)

    assert _COMMANDS["check.standard"] in text
    for key in _NEVER_GRANTED:
        assert f"`{_COMMANDS[key]}`" not in text
