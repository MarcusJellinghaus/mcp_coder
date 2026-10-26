"""Fail if ``src/`` runs git as a subprocess or imports mcp_workspace internals.

Rules (no allowlist beyond each shim importing its own upstream package):

- ``git``: an argv list starting with ``"git"`` (``["git", ...]``, also split
  across lines). Use ``mcp_coder.mcp_workspace_git`` instead.
- ``workspace-git-direct-import``: ``mcp_workspace.git_operations`` outside
  ``src/mcp_coder/mcp_workspace_git.py``.
- ``workspace-github-direct-import``: ``mcp_workspace.github_operations``
  outside ``src/mcp_coder/mcp_workspace_github.py``.

This is a text scan, not an AST check. It guards against accidents, not
deliberate bypass: an argv that never spells ``"git"`` literally
(``[GIT_BIN, ...]``, ``shlex.split("git status")``) is not caught.

Out of scope: tests, shell text in ``command_templates.py``, ``gh`` calls,
and scripts under ``tools/``.
"""

import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Rule:
    """A forbidden pattern, the roots it applies to and the files exempt from it."""

    id: str
    patterns: tuple[re.Pattern[str], ...]
    paths: tuple[str, ...]
    exclude: tuple[str, ...]
    message: str


RULES: tuple[Rule, ...] = (
    Rule(
        "git",
        (re.compile(r'\[\s*"git"'),),
        ("src",),
        (),
        "use `mcp_coder.mcp_workspace_git`",
    ),
    Rule(
        "workspace-git-direct-import",
        (re.compile(r"mcp_workspace\.git_operations"),),
        ("src",),
        ("src/mcp_coder/mcp_workspace_git.py",),
        "import from `mcp_coder.mcp_workspace_git`",
    ),
    Rule(
        "workspace-github-direct-import",
        (re.compile(r"mcp_workspace\.github_operations"),),
        ("src",),
        ("src/mcp_coder/mcp_workspace_github.py",),
        "import from `mcp_coder.mcp_workspace_github`",
    ),
)


def _applies(rule: Rule, rel_path: str) -> bool:
    if rel_path in rule.exclude:
        return False
    return any(rel_path.startswith(f"{root}/") for root in rule.paths)


def find_violations(
    rel_path: str, text: str, rules: Sequence[Rule] = RULES
) -> list[str]:
    """Return "<path>:<line>: [<rule id>] <message>" for every hit in one file."""
    hits: list[str] = []
    for rule in rules:
        if not _applies(rule, rel_path):
            continue
        for pattern in rule.patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                hits.append(f"{rel_path}:{line}: [{rule.id}] {rule.message}")
    return hits


def scan(root: Path) -> list[str]:
    """Return all violations in every *.py under ``root / "src"``."""
    hits: list[str] = []
    for py in sorted((root / "src").rglob("*.py")):
        rel_path = py.relative_to(root).as_posix()
        hits.extend(find_violations(rel_path, py.read_text(encoding="utf-8")))
    return hits


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def main() -> int:
    """Print violations; return 1 if any, else 0."""
    hits = scan(_repo_root())
    if hits:
        for hit in hits:
            print(hit)
        print()
        print(f"ERROR: {len(hits)} forbidden call(s) found in src/")
        return 1

    print("OK: no forbidden calls")
    return 0


if __name__ == "__main__":
    sys.exit(main())
