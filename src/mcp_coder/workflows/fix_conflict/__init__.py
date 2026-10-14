"""Fix-conflict workflow package.

Mechanical (no-LLM) rebase executed by Jenkins to resolve a detected
merge conflict on a PR.
"""

from .core import run_fix_conflict_workflow

__all__ = [
    "run_fix_conflict_workflow",
]
