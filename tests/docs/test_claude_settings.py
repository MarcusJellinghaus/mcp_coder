"""Checks on this repo's committed Claude Code settings files."""

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SETTINGS_JSON = REPO_ROOT / ".claude" / "settings.json"
SETTINGS_LOCAL_JSON = REPO_ROOT / ".claude" / "settings.local.json"

GIT_WRITE_TOOLS = {
    "mcp__mcp-workspace__git_branch",
    "mcp__mcp-workspace__git_branch_delete",
    "mcp__mcp-workspace__git_commit",
    "mcp__mcp-workspace__git_push",
    "mcp__mcp-workspace__git_push_force",
}
READ_ONLY_EXTRA_TOOLS = {
    "mcp__mcp-tools-py__run_deptry_check",
    "mcp__mcp-workspace__github_subissue_list",
}


def _load(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def _local_allow() -> list[str]:
    allow: list[str] = _load(SETTINGS_LOCAL_JSON)["permissions"]["allow"]
    return allow


def test_no_committed_settings_json() -> None:
    """No committed `.claude/settings.json`: allows live in the tracked local file."""
    assert not SETTINGS_JSON.exists()


def test_settings_local_json_has_no_deny() -> None:
    assert "deny" not in _load(SETTINGS_LOCAL_JSON)["permissions"]


def test_settings_local_json_has_no_git_write_tools() -> None:
    present = sorted(GIT_WRITE_TOOLS & set(_local_allow()))
    assert not present, f"git write tools must not be allow-listed: {present}"


def test_settings_local_json_has_read_only_extra_tools() -> None:
    missing = sorted(READ_ONLY_EXTRA_TOOLS - set(_local_allow()))
    assert not missing, f"missing allow entries: {missing}"


def test_settings_local_json_has_no_dropped_entries() -> None:
    dropped = [
        entry
        for entry in _local_allow()
        if entry.startswith("Bash(start ") or ".bat" in entry
    ]
    assert not dropped, f"dropped entries are back: {dropped}"


def test_settings_local_json_gh_tool_narrowed() -> None:
    """Only `gh-tool checkout-issue-branch` stays allow-listed."""
    allow = _local_allow()
    broad = [entry for entry in allow if "gh-tool:*" in entry or "set-status" in entry]
    assert not broad, f"gh-tool must be narrowed to checkout-issue-branch: {broad}"
    assert "mcp__mcp-workspace__github_issue_set_status" not in allow
