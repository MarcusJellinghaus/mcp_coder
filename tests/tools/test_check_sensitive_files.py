"""Unit tests for tools/check_sensitive_files.py.

Git is replaced by a fake runner; these tests do not read the repository.
"""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_TOOL_PY = Path(__file__).resolve().parents[2] / "tools" / "check_sensitive_files.py"


def _load() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_sensitive_files", _TOOL_PY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_sensitive_files = _load()

# Synthetic rules, not the repository's .mcp-file-access: the /.claude/ and
# /.claude/skills/ rules exist only for the directory and override tests.
_DEFAULT_RULES = (
    b"read-only /.mcp.json\nread-only /.claude/\nread-write /.claude/skills/\n"
)


@dataclass
class FakeGit:
    changed: list[str] = field(default_factory=list)
    rules: bytes | None = _DEFAULT_RULES
    mode: str = "100644"
    fail: bool = False
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def __call__(self, args: Sequence[str]) -> Any:
        self.calls.append(tuple(args))
        result = check_sensitive_files.GitResult
        if self.fail:
            return result(128, b"", "fatal: bad revision")
        command = args[0]
        if command == "merge-base":
            return result(0, b"MB\n", "")
        if command == "diff":
            return result(0, b"\0".join(p.encode() for p in self.changed), "")
        if command == "ls-tree":
            if self.rules is None:
                return result(0, b"", "")
            listing = f"{self.mode} blob 0123\t.mcp-file-access\0"
            return result(0, listing.encode(), "")
        if command == "show":
            return result(0, self.rules or b"", "")
        raise AssertionError(f"unexpected git call: {args}")


@pytest.fixture(name="module")
def fixture_module() -> ModuleType:
    return check_sensitive_files


def _run(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    fake: FakeGit,
) -> tuple[int, str]:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setattr(module, "run_git", fake)
    code = module.main(["--base", "B", "--head", "H"])
    return code, capsys.readouterr().out


def _warnings(out: str) -> dict[str, str]:
    """Map each file annotation's escaped path to its message."""
    found: dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith("::warning file="):
            path, message = line[len("::warning file=") :].split("::", 1)
            found[path] = message
    return found


def test_no_rules_file_on_base(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=["pyproject.toml"], rules=None)
    code, out = _run(module, monkeypatch, capsys, fake)
    assert code == 0
    assert "No .mcp-file-access on B: read-only rule check skipped." in out
    assert _warnings(out) == {"pyproject.toml": "watch list /pyproject.toml"}


def test_invalid_rules_file_warns_once(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json", "pyproject.toml"], rules=b"read-only\n")
    _, out = _run(module, monkeypatch, capsys, fake)
    generic = [line for line in out.splitlines() if line.startswith("::warning::")]
    assert len(generic) == 1
    assert "line 1: expected '<level> <pattern>'" in generic[0]
    assert _warnings(out) == {"pyproject.toml": "watch list /pyproject.toml"}


def test_non_utf8_rules_file_is_invalid(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json"], rules=b"read-only /\xff\n")
    code, out = _run(module, monkeypatch, capsys, fake)
    assert code == 0
    assert "::warning::" in out
    assert "is not valid UTF-8" in out
    assert not _warnings(out)


def test_mixed_case_level_is_invalid(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json"], rules=b"Read-Only /.mcp.json\n")
    _, out = _run(module, monkeypatch, capsys, fake)
    assert "unknown level 'Read-Only'" in out
    assert not _warnings(out)


def test_lowered_pattern_raising_re_error_is_invalid(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    fake = FakeGit(changed=["Zx"], rules=b"read-only /[Z-a]x\n")
    code, out = _run(module, monkeypatch, capsys, fake)
    assert code == 0
    assert "::warning::" in out
    assert "pattern error:" in out
    assert not _warnings(out)


def test_lowered_load_problems_are_invalid(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    real = module.load_access_rules

    def wrapped(project_dir: Path) -> Any:
        if b"[z-a]" in (project_dir / ".mcp-file-access").read_bytes():
            return module.AccessRules(problems=("line 1: invalid pattern '/[z-a]x'",))
        return real(project_dir)

    monkeypatch.setattr(module, "load_access_rules", wrapped)
    fake = FakeGit(changed=["Zx"], rules=b"read-only /[Z-a]x\n")
    _, out = _run(module, monkeypatch, capsys, fake)
    generic = [line for line in out.splitlines() if line.startswith("::warning::")]
    assert len(generic) == 1
    assert "line 1: invalid pattern '/[z-a]x'" in generic[0]
    assert not _warnings(out)


@pytest.mark.parametrize("mode", ["040000", "120000"])
def test_rules_file_not_regular_is_invalid(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    mode: str,
) -> None:
    fake = FakeGit(changed=[".mcp.json"], mode=mode)
    _, out = _run(module, monkeypatch, capsys, fake)
    assert "::warning::" in out
    assert "not a regular file" in out
    assert not _warnings(out)
    assert not any(call[0] == "show" for call in fake.calls)


def test_read_only_file_flagged(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".mcp.json": "read-only rule /.mcp.json"}


def test_read_only_directory_rule_flags_file_below(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".claude/settings.json"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".claude/settings.json": "read-only rule /.claude/"}


def test_read_write_override_drops_read_only_reason(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".claude/skills/x/SKILL.md"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {
        ".claude/skills/x/SKILL.md": "watch list /.claude/skills/"
    }


def test_rules_file_flagged(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp-file-access"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".mcp-file-access": "rules file"}


def test_watch_list_pyproject(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=["pyproject.toml"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {"pyproject.toml": "watch list /pyproject.toml"}


def test_watch_list_agents(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".claude/agents/a.md"], rules=None)
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".claude/agents/a.md": "watch list /.claude/agents/"}


def test_rename_flags_old_path(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=["x.json", ".mcp.json"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".mcp.json": "read-only rule /.mcp.json"}
    diff_calls = [call for call in fake.calls if call[0] == "diff"]
    assert len(diff_calls) == 1
    assert "--no-renames" in diff_calls[0]


def test_deleted_read_only_file_flagged(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".claude/removed.md"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".claude/removed.md": "read-only rule /.claude/"}


def test_case_insensitive_match_keeps_original_path(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    fake = FakeGit(changed=[".MCP.json"])
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {".MCP.json": "read-only rule /.mcp.json"}


def test_rules_read_from_base(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp-file-access"])
    _run(module, monkeypatch, capsys, fake)
    assert ("show", "B:.mcp-file-access") in fake.calls
    assert ("ls-tree", "-z", "B", "--", ".mcp-file-access") in fake.calls


def test_several_reasons_listed(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp-file-access"], rules=b"read-only /.mcp-file-access\n")
    _, out = _run(module, monkeypatch, capsys, fake)
    assert _warnings(out) == {
        ".mcp-file-access": "read-only rule /.mcp-file-access; rules file"
    }


def test_nothing_flagged(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=["README.md"])
    code, out = _run(module, monkeypatch, capsys, fake)
    assert code == 0
    assert out == "No sensitive files changed.\n"


def test_diff_starts_from_merge_base(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=["README.md"])
    _run(module, monkeypatch, capsys, fake)
    assert ("merge-base", "B", "H") in fake.calls
    assert ("diff", "--name-only", "--no-renames", "-z", "MB", "H") in fake.calls


def test_escaping(module: ModuleType) -> None:
    assert module._escape_property("a%b:c,d\r\ne") == "a%25b%3Ac%2Cd%0D%0Ae"
    assert module._escape_data("a%b:c,d\r\ne") == "a%25b:c,d%0D%0Ae"
    summary = module._summary(
        {".claude/agents/a|b.md": ["watch list /.claude/agents/"]}
    )
    assert "| .claude/agents/a\\|b.md | watch list /.claude/agents/ |" in summary


def test_escaping_end_to_end(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".claude/agents/a%:,\nb.md"], rules=None)
    _, out = _run(module, monkeypatch, capsys, fake)
    assert (
        "::warning file=.claude/agents/a%25%3A%2C%0Ab.md::watch list /.claude/agents/"
        in out
    )
    assert not any(line.startswith("b.md") for line in out.splitlines())


def test_summary_table(module: ModuleType) -> None:
    summary = module._summary(
        {
            ".mcp.json": ["read-only rule /.mcp.json"],
            "pyproject.toml": ["watch list /pyproject.toml"],
        }
    )
    assert summary == (
        "## Sensitive files changed\n"
        "\n"
        "| File | Reasons |\n"
        "|---|---|\n"
        "| .mcp.json | read-only rule /.mcp.json |\n"
        "| pyproject.toml | watch list /pyproject.toml |\n"
    )
    assert module._summary({}) == "No sensitive files changed.\n"


def test_summary_appended_to_step_summary(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    summary_file = tmp_path / "summary.md"
    summary_file.write_text("existing\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))
    monkeypatch.setattr(module, "run_git", FakeGit(changed=[".mcp.json"]))
    assert module.main(["--base", "B", "--head", "H"]) == 0
    out = capsys.readouterr().out
    content = summary_file.read_text(encoding="utf-8")
    assert content.startswith("existing\n## Sensitive files changed\n")
    assert "| .mcp.json | read-only rule /.mcp.json |" in content
    assert "## Sensitive files changed" not in out
    assert "::warning file=.mcp.json::read-only rule /.mcp.json" in out


def test_exit_code_zero_when_flagged(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json", "pyproject.toml"])
    code, out = _run(module, monkeypatch, capsys, fake)
    assert code == 0
    assert len(_warnings(out)) == 2


def test_git_failure_exits_non_zero(
    module: ModuleType,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    fake = FakeGit(changed=[".mcp.json"], fail=True)
    with pytest.raises(SystemExit) as exc_info:
        _run(module, monkeypatch, capsys, fake)
    assert exc_info.value.code not in (0, None)
