#!/usr/bin/env python3
"""Split test_orchestrator_sessions.py into 4 separate test files.

Run from project root:
    python tools/split_test_file.py
"""

import ast
import textwrap
from pathlib import Path


SOURCE = Path("tests/workflows/vscodeclaude/test_orchestrator_sessions.py")

# Mapping: original class name -> (target filename, new class name or None to keep)
CLASS_MAP = {
    "TestOrchestration": ("test_session_restart.py", "TestSessionRestart"),
    "TestPrepareRestartBranch": ("test_session_restart_prepare_branch.py", None),
    "TestRestartClosedSessionsBranchHandling": (
        "test_session_restart_closed_sessions.py",
        None,
    ),
    "TestBranchHandlingIntegration": (
        "test_session_restart_branch_integration.py",
        None,
    ),
}

DOCSTRINGS = {
    "test_session_restart.py": '"""Tests for session restart orchestration logic."""',
    "test_session_restart_prepare_branch.py": '"""Tests for prepare_restart_branch functionality."""',
    "test_session_restart_closed_sessions.py": '"""Tests for restart closed sessions branch handling."""',
    "test_session_restart_branch_integration.py": '"""Tests for branch handling integration scenarios."""',
}


def find_used_names_in_class(class_source: str, all_imports: list[str]) -> list[str]:
    """Find which imported names are actually used in a class body."""
    used = []
    for imp_line in all_imports:
        # Extract imported names
        if imp_line.strip().startswith("from "):
            # from X import Y, Z
            match = __import__("re").search(r"import\s+(.+)", imp_line)
            if match:
                names = [n.strip().split(" as ")[-1].strip() for n in match.group(1).split(",")]
                if any(name in class_source for name in names):
                    used.append(imp_line)
        elif imp_line.strip().startswith("import "):
            # import X
            match = __import__("re").search(r"import\s+(\S+)", imp_line)
            if match:
                name = match.group(1).split(".")[-1]
                if name in class_source:
                    used.append(imp_line)
    return used


def main() -> None:
    content = SOURCE.read_text(encoding="utf-8")
    lines = content.split("\n")
    tree = ast.parse(content)

    # Collect all top-level import lines
    import_lines: list[str] = []
    first_class_line = None

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            # Get the actual source lines for this import (may be multi-line)
            start = node.lineno - 1
            end = node.end_lineno
            import_lines.append("\n".join(lines[start:end]))
        if isinstance(node, ast.ClassDef) and first_class_line is None:
            first_class_line = node.lineno

    # Also collect any pytest.mark or other decorators/constants between imports and first class
    # Get everything before first class that's not an import
    pre_class_lines = []
    if first_class_line:
        for i in range(first_class_line - 1):
            line = lines[i]
            stripped = line.strip()
            if (
                stripped
                and not stripped.startswith(("import ", "from ", "#", '"""', "'''"))
                and not any(stripped in imp for imp in import_lines)
            ):
                pre_class_lines.append(line)

    # Extract each class
    classes: dict[str, tuple[int, int, str]] = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and node.name in CLASS_MAP:
            start = node.lineno - 1
            end = node.end_lineno
            # Include decorators if any
            if node.decorator_list:
                start = node.decorator_list[0].lineno - 1
            class_text = "\n".join(lines[start:end])
            classes[node.name] = (start, end, class_text)

    target_dir = SOURCE.parent

    for class_name, (start, end, class_text) in classes.items():
        target_file, new_name = CLASS_MAP[class_name]
        docstring = DOCSTRINGS[target_file]

        # Rename class if needed
        if new_name:
            class_text = class_text.replace(f"class {class_name}", f"class {new_name}", 1)

        # Find needed imports
        needed_imports = find_used_names_in_class(class_text, import_lines)

        # Build file content
        parts = [docstring, ""]

        # Add __future__ imports first
        future_imports = [i for i in needed_imports if "__future__" in i]
        other_imports = [i for i in needed_imports if "__future__" not in i]

        if future_imports:
            parts.extend(future_imports)
            parts.append("")

        if other_imports:
            parts.extend(other_imports)
            parts.append("")

        # Add any pre-class constants/markers
        if pre_class_lines:
            # Only include if used in class
            for pcl in pre_class_lines:
                name = pcl.split("=")[0].strip() if "=" in pcl else pcl.strip()
                if name in class_text:
                    parts.append(pcl)
            parts.append("")

        parts.append("")
        parts.append(class_text)
        parts.append("")

        file_content = "\n".join(parts)
        target_path = target_dir / target_file
        target_path.write_text(file_content, encoding="utf-8")
        line_count = len(file_content.split("\n"))
        print(f"Created {target_path} ({line_count} lines)")

    # Delete original
    SOURCE.unlink()
    print(f"\nDeleted {SOURCE}")

    # Summary
    print("\nDone! Created 4 new test files.")


if __name__ == "__main__":
    main()
