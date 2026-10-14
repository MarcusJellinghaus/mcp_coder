"""Fix-ci workflow package.

CI auto-fix loop executed by Jenkins to resolve a detected failing-CI
escalation on a PR.
"""

from .core import run_fix_ci_workflow

__all__ = [
    "run_fix_ci_workflow",
]
