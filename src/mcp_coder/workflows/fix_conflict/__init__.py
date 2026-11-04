"""Fix-conflict workflow package.

Rebase executed by Jenkins to resolve a detected merge conflict on a PR:
``run_fix_conflict_workflow`` tries a git-only rebase and falls back to the
LLM rebase via ``rebase_with_llm_fallback``.
"""

from .core import run_fix_conflict_workflow

__all__ = [
    "run_fix_conflict_workflow",
]
