"""Test sys.path and module availability."""

import sys
from pathlib import Path


def test_syspath() -> None:
    """Test that sys.path includes the project directory."""
    project_dir = Path(__file__).parent.parent.parent.parent.parent / "src"
    project_dir_str = str(project_dir.resolve())

    # Print sys.path for debugging
    print(f"\nProject dir expected: {project_dir_str}")
    print("\nPython sys.path:")
    for path in sys.path:
        print(f"  - {path}")

    # Check if project is in path
    assert any(
        project_dir_str in path or str(project_dir) in path for path in sys.path
    ), f"Project directory {project_dir_str} not in sys.path"


def test_module_exists() -> None:
    """Test that the jenkins_operations module directory exists."""
    test_file = Path(__file__)
    src_dir = test_file.parent.parent.parent.parent.parent / "src"
    jenkins_ops_dir = src_dir / "mcp_coder" / "utils" / "jenkins_operations"
    models_file = jenkins_ops_dir / "models.py"

    print(f"\nLooking for: {models_file}")
    print(f"Exists: {models_file.exists()}")

    assert jenkins_ops_dir.exists(), f"Directory doesn't exist: {jenkins_ops_dir}"
    assert models_file.exists(), f"Models file doesn't exist: {models_file}"
