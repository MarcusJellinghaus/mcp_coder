"""Custom build hook to bundle .claude/ skill files into the wheel."""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyWithSkills(build_py):  # type: ignore[misc]
    """Copy .claude/ skill dirs into package resources before building."""

    def run(self) -> None:
        """Run the build after copying claude resources."""
        _copy_claude_resources()
        super().run()


def _copy_claude_resources() -> None:
    """Copy .claude/{skills,knowledge_base,agents}/ → src/mcp_coder/resources/claude/.

    Removes any existing destination first so stale build artifacts (files
    that were deleted from .claude/ since the previous build) don't linger.
    """
    repo_root = Path(__file__).parent
    source = repo_root / ".claude"
    dest = repo_root / "src" / "mcp_coder" / "resources" / "claude"
    if dest.exists():
        shutil.rmtree(dest)
    for subdir in ["skills", "knowledge_base", "agents"]:
        src_dir = source / subdir
        if src_dir.exists():
            shutil.copytree(src_dir, dest / subdir, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildPyWithSkills})
