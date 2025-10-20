"""Test configuration for jenkins_operations tests."""

import sys
from pathlib import Path

# Add src directory to Python path to ensure jenkins_operations module can be imported
# This is needed when the package editable install hasn't picked up new modules yet
project_root = Path(__file__).parent.parent.parent.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
