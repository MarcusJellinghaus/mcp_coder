"""Checks on this repo's committed Claude Code settings files."""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_JSON = REPO_ROOT / ".claude" / "settings.json"
SETTINGS_LOCAL_JSON = REPO_ROOT / ".claude" / "settings.local.json"

PROTECTED_DENY_RULES = [
    "Edit(/.mcp.json)",
    "Edit(/.mcp.linux.json)",
    "Edit(/.mcp.macos.json)",
    "Edit(/.mcp-file-access)",
    "Edit(/.claude/settings.json)",
    "Edit(/.claude/settings.local.json)",
]
GIT_WRITE_TOOLS = {
    "mcp__mcp-workspace__git_branch",
    "mcp__mcp-workspace__git_branch_delete",
    "mcp__mcp-workspace__git_commit",
    "mcp__mcp-workspace__git_push",
    "mcp__mcp-workspace__git_push_force",
}
T11_TOOLS = {
    "mcp__mcp-tools-py__run_deptry_check",
    "mcp__mcp-workspace__github_subissue_list",
}


def _load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _local_allow() -> list[str]:
    allow: list[str] = _load(SETTINGS_LOCAL_JSON)["permissions"]["allow"]
    return allow


def test_settings_json_is_exactly_the_protected_deny() -> None:
    expected = {"permissions": {"deny": PROTECTED_DENY_RULES}}
    assert _load(SETTINGS_JSON) == expected


def test_settings_local_json_has_no_git_write_tools() -> None:
    present = sorted(GIT_WRITE_TOOLS & set(_local_allow()))
    assert not present, f"git write tools must not be allow-listed: {present}"


def test_settings_local_json_has_t11_tools() -> None:
    missing = sorted(T11_TOOLS - set(_local_allow()))
    assert not missing, f"missing allow entries: {missing}"


def test_settings_local_json_has_no_dropped_entries() -> None:
    dropped = [
        entry
        for entry in _local_allow()
        if entry.startswith("Bash(start ") or ".bat" in entry
    ]
    assert not dropped, f"dropped entries are back: {dropped}"
