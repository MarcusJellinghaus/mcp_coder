"""Helper script to run ruff check and print results."""

import subprocess
import sys

result = subprocess.run(
    [
        sys.executable.replace("python.exe", "ruff.exe"),
        "check",
        "src",
        "tests",
        "--select",
        "D100,D101,D103,D403,D415,D417,DOC102,DOC202",
    ],
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
