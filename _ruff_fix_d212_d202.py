"""Temporary script to run ruff check --fix for D212 and D202."""

import subprocess
import sys

ruff = sys.executable.replace("python.exe", "ruff.exe")

# First show current violations
print("=== Current D212,D202 violations ===")
r = subprocess.run(
    [ruff, "check", "src", "tests", "--select", "D212,D202"],
    capture_output=True,
    text=True,
)
print(r.stdout)
print(f"Return code: {r.returncode}")

# Auto-fix
print("\n=== Running ruff check --fix ===")
r2 = subprocess.run(
    [ruff, "check", "--fix", "src", "tests", "--select", "D212,D202"],
    capture_output=True,
    text=True,
)
print(r2.stdout)
print(f"Return code: {r2.returncode}")

# Verify
print("\n=== Verification ===")
r3 = subprocess.run(
    [ruff, "check", "src", "tests", "--select", "D212,D202"],
    capture_output=True,
    text=True,
)
print(r3.stdout if r3.stdout else "No violations found!")
print(f"Return code: {r3.returncode}")
