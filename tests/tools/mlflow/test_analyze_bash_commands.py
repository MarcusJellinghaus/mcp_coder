"""Unit tests for tools/mlflow/analyze_bash_commands.py.

Covers the pure command classifier: env/`cd` stripping and purpose bucketing.
Loaded by file path (tools/ is outside pythonpath); this script has no sibling
imports, so a plain spec load is enough.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

_TOOL_PY = (
    Path(__file__).resolve().parents[3]
    / "tools"
    / "mlflow"
    / "analyze_bash_commands.py"
)


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("analyze_bash_commands", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load()


@pytest.mark.parametrize(
    "command, expected",
    [
        ("git status --short", "git_read"),
        ("git log --oneline -8", "git_read"),
        ("git commit -m 'x'", "git_write"),
        ("git checkout -b feature", "git_write"),
        ("git push -u origin feature", "git_write"),
        ("gh issue create --title x", "gh_issue_write"),
        ("gh issue view 5", "gh_issue_read"),
        ("gh issue edit 5 --add-assignee me", "gh_issue_write"),
        ("gh pr create --base main --head x", "gh_pr_write"),
        ("gh pr view 1", "gh_pr_read"),
        ("gh api repos/x/commits", "gh_other"),
        ("gh label list", "gh_other"),
        ("cat file.txt", "file_read"),
        ("cat > /tmp/body.md <<'EOF'", "file_write"),
        ("ls -la", "file_list"),
        ("find . -name '*.py'", "file_list"),
        ("grep -n foo file", "file_search"),
        ("sed -i 's/a/b/' f", "file_write"),
        ("sed -n '313,400p' f", "text_proc"),
        ("echo hello", "nav_env"),
        ("echo x > out.txt", "file_write"),
        ("python -c 'import x'", "run_python"),
        ("pytest tests -x", "run_tests"),
        ("mypy src", "run_checks"),
        ("pip install foo", "pkg_install"),
        ("mcp-coder gh-tool set-status", "mcp_coder"),
        ("cd /some/path", "nav_env"),
        ("", "nav_env"),
    ],
)
def test_classify_purpose(command: str, expected: str) -> None:
    assert mod.classify_purpose(command) == expected


def test_effective_command_strips_env_and_cd() -> None:
    assert mod.effective_command("cd /x && git status") == "git status"
    assert mod.effective_command("VAR=1 python foo.py") == "python foo.py"
    assert mod.effective_command('cd "C:/a b" && ls') == "ls"


def test_cd_prefix_reclassifies_to_real_verb() -> None:
    # `cd <path> &&|;|newline <cmd>` should classify by the real command.
    assert mod.classify_purpose("cd /repo && git commit -m x") == "git_write"
    assert mod.classify_purpose("cd ~/x\npython -c 'import json'") == "run_python"


def test_command_of_and_load(tmp_path: Path) -> None:
    import json

    dataset = tmp_path / "permission_events.jsonl"
    rows = [
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        {
            "tool_name": "mcp__mcp-workspace__read_file",
            "tool_input": {"file_path": "x"},
        },
    ]
    dataset.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    events = mod.load_bash_events(tmp_path)
    assert len(events) == 1  # only the Bash row
    assert mod.command_of(events[0]) == "git status"


def test_summarize_counts_purposes() -> None:
    events = [
        {"tool_name": "Bash", "tool_input": {"command": "git status"}},
        {"tool_name": "Bash", "tool_input": {"command": "gh issue create -t x"}},
        {"tool_name": "Bash", "tool_input": {"command": "gh issue create -t y"}},
    ]
    summary = mod.summarize(events)
    assert summary["total"] == 3
    assert summary["by_purpose"]["gh_issue_write"] == 2
    assert summary["by_purpose"]["git_read"] == 1
