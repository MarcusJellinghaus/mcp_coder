"""Shared TOML helpers.

Formatting of TOML parse errors lives here so that both the user-level config
reader (``user_config``) and the project-level reader (``pyproject_config``)
can report syntax errors the same way.
"""

import re
import tomllib
from pathlib import Path

# Curly quotes pasted from chat windows or documents (U+201C/U+201D/U+2018/U+2019)
_SMART_QUOTES = "“”‘’"


def format_toml_error(file_path: Path, error: tomllib.TOMLDecodeError) -> str:
    """Format TOML parse error in Python SyntaxError style.

    Args:
        file_path: Path to the config file that failed to parse
        error: The TOMLDecodeError from tomllib

    Returns:
        Formatted error string with file path, line content, and pointer
    """
    # TOMLDecodeError has lineno/colno attributes (added in Python 3.11)
    # but type stubs may not include them
    line_num: int | None = getattr(error, "lineno", None)
    col_num: int | None = getattr(error, "colno", None)

    # If attributes aren't available, try to extract from error message
    # Error message format: "... (at line X, column Y)"
    if line_num is None:
        match = re.search(r"at line (\d+)", str(error))
        if match:
            line_num = int(match.group(1))
    if col_num is None:
        match = re.search(r"column (\d+)", str(error))
        if match:
            col_num = int(match.group(1))

    # Build the file/line header
    lines = [f'  File "{file_path}", line {line_num}']

    # Offending line content - stays empty when the file can't be read
    error_line = ""

    # Try to read the error line from the file
    try:
        file_content = file_path.read_text(encoding="utf-8")
        file_lines = file_content.splitlines()

        # Check if line number is valid (1-based)
        if line_num is not None and 1 <= line_num <= len(file_lines):
            error_line = file_lines[line_num - 1].rstrip()
            lines.append(f"    {error_line}")

            # Add pointer at column position (1-based to 0-based)
            if col_num is not None and col_num >= 1:
                pointer_pos = col_num - 1
                lines.append("    " + " " * pointer_pos + "^")
    except OSError:
        # File can't be read - skip line content
        pass

    # Add the error message
    error_str = str(error)
    lines.append(f"TOML parse error: {error_str}")

    # Add hint for common Windows path backslash issues
    if "Invalid" in error_str and ("hex" in error_str or "escape" in error_str):
        lines.append("")
        lines.append("Hint: Backslashes in paths need escaping in TOML.")
        lines.append('  Use forward slashes: "C:/Users/..."')
        lines.append("  Or single quotes:    'C:\\Users\\...'")

    # Add hint for curly/smart quotes pasted from a chat window or a document
    if any(ch in error_line for ch in _SMART_QUOTES):
        lines.append("")
        lines.append("Hint: Curly/smart quotes are not valid TOML string delimiters.")
        lines.append("  Use straight quotes: \"value\" or 'value'")

    return "\n".join(lines)
