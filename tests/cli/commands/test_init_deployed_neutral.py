"""Deployed ``.claude/`` prose must not name Python tools or conventions.

``mcp-coder init`` copies ``skills/``, ``agents/`` and ``knowledge_base/``
into every repo that uses mcp-coder, whatever its language. Skill and agent
bodies therefore describe steps by purpose. Python specifics belong in
``knowledge_base/python.md``, which only ``mcp-tools-py`` repos get.
Frontmatter (``tools:``, ``allowed-tools``) is not checked.
"""

from __future__ import annotations

import re
from pathlib import Path

import frontmatter

from mcp_coder.cli.commands.init import DEPLOY_SUBDIRS

REPO_ROOT = Path(__file__).resolve().parents[3]
EXEMPT = Path("knowledge_base") / "python.md"
TERMS = (
    "pylint",
    "pytest",
    "mypy",
    "ruff",
    "vulture",
    "lint-imports",
    "lint_imports",
    "import-linter",
    "tach",
    "tools-py",
    "run_format_code",
    "move_symbol",
    "move_module",
    "pyproject",
    "uv.lock",
    "TYPE_CHECKING",
    "python",
)
_TERM_RE = re.compile(
    r"(?<![a-z0-9])(?:" + "|".join(map(re.escape, TERMS)) + r")(?![a-z0-9])"
    r"|\.py(?![a-z0-9])",
    re.IGNORECASE,
)


def _python_terms(text: str) -> list[str]:
    """Return the Python-specific terms found in ``text``."""
    return _TERM_RE.findall(text)


def _prose(path: Path) -> str:
    """Return the body of a Markdown file, without its frontmatter."""
    return str(frontmatter.load(str(path)).content)


def test_matcher() -> None:
    """Whole terms and ``.py`` suffixes hit; embedded letters do not."""
    assert _python_terms("mcp__mcp-tools-py__run_pytest_check")
    assert not _python_terms("attach")
    assert not _python_terms("detach")
    assert _python_terms("`types.py`")
    assert not _python_terms(".pyc")
    assert _python_terms("Python")


def test_deployed_prose_is_toolkit_neutral() -> None:
    """No deployed file except ``python.md`` names Python tools in its body."""
    base = REPO_ROOT / ".claude"
    files = sorted(
        path
        for subdir in DEPLOY_SUBDIRS
        for path in (base / subdir).rglob("*.md")
        if path.relative_to(base) != EXEMPT
    )
    assert files

    offenders = [
        f"{path.relative_to(REPO_ROOT).as_posix()}:{number}: {hits}"
        for path in files
        for number, line in enumerate(_prose(path).splitlines(), start=1)
        if (hits := _python_terms(line))
    ]
    assert not offenders, (
        "Deployed .claude prose names Python tools or conventions. Describe "
        "the step by purpose and move Python specifics to "
        "knowledge_base/python.md:\n" + "\n".join(offenders)
    )
