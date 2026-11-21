"""Deployed ``.claude/`` files must not name paths that exist only in mcp-coder.

``mcp-coder init --just-skills`` copies ``skills/``, ``agents/`` and
``knowledge_base/`` into every repo that uses mcp-coder. A path such as
``docs/...`` resolves here but silently breaks there. Allowed: shared
top-level directories, the bare directory name, or a path qualified
"in the mcp-coder repository" on the same line.
"""

from __future__ import annotations

import re
from pathlib import Path

from mcp_coder.cli.commands.init import DEPLOY_SUBDIRS

REPO_ROOT = Path(__file__).resolve().parents[3]

SHARED_TOP_LEVEL = frozenset(
    {".claude", ".git", ".github", ".scratch", "pr_info", "src", "tests"}
)
QUALIFIER = "in the mcp-coder repository"
_BACKTICK_PATH = re.compile(r"`([^`\s/]+)/[^`\s]+`")


def _repo_specific_dirs() -> frozenset[str]:
    """Top-level directories of this repo that other repos need not have."""
    return frozenset(
        entry.name
        for entry in REPO_ROOT.iterdir()
        if entry.is_dir() and entry.name not in SHARED_TOP_LEVEL
    )


def _unqualified_paths(line: str, repo_specific: frozenset[str]) -> list[str]:
    """Return the repo-specific top-level dirs a line names without qualifying."""
    if QUALIFIER in line:
        return []
    return [top for top in _BACKTICK_PATH.findall(line) if top in repo_specific]


def test_detects_unqualified_repo_path() -> None:
    """A bare ``docs/...`` path is flagged; qualified or bare-dir forms are not."""
    dirs = frozenset({"docs"})
    assert _unqualified_paths("see `docs/architecture/architecture.md`", dirs) == [
        "docs"
    ]
    assert not _unqualified_paths(f"see `docs/github.md` {QUALIFIER}.", dirs)
    assert not _unqualified_paths("document it in the `docs/` folder", dirs)
    assert not _unqualified_paths("read `pr_info/steps/summary.md`", dirs)


def test_deployed_files_name_no_repo_specific_paths() -> None:
    """No deployed file names a path that exists only in mcp-coder."""
    repo_specific = _repo_specific_dirs()
    files = sorted(
        path
        for subdir in DEPLOY_SUBDIRS
        for path in (REPO_ROOT / ".claude" / subdir).rglob("*.md")
    )
    assert files

    offenders = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{number}: {line.strip()}"
        for path in files
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _unqualified_paths(line, repo_specific)
    ]
    assert not offenders, (
        "Deployed .claude files name mcp-coder-only paths. Phrase them "
        f'generically or add "{QUALIFIER}":\n' + "\n".join(offenders)
    )
