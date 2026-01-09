"""Constants used across the mcp-coder project."""

from pathlib import Path

# Prompt file paths
PROMPTS_FILE_PATH = Path("mcp_coder") / "prompts" / "prompts.md"
# constant is correct, even though it does not start from "src"

# Build artifacts to ignore in working directory clean checks
# These files are auto-generated and should not block git clean status
DEFAULT_IGNORED_BUILD_ARTIFACTS: list[str] = ["uv.lock"]
