"""Markdown parsing helpers for the prompt manager.

Pure markdown-string parsing utilities (no I/O): header extraction,
code-block extraction after a header, and duplicate detection.
"""

import re
from typing import Any, Dict, List, Union


def _extract_headers(content: str) -> List[Dict[str, Any]]:
    """Extract all headers from markdown content.

    This function finds all markdown headers (levels 1-5) and returns
    detailed information about each one including position data.

    Args:
        content: Markdown content

    Returns:
        list: List of header dictionaries with keys:
            - name (str): Header text without # symbols
            - level (int): Header level (1-5)
            - line (int): 1-based line number
            - position (int): 0-based line index
    """
    headers = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # Match headers with any level (# ## ### #### #####)
        match = re.match(r"^(#{1,5})\s+(.+)$", line.strip())
        if match:
            level = len(match.group(1))
            name = match.group(2).strip()

            headers.append(
                {
                    "name": name,
                    "level": level,
                    "line": line_num,
                    "position": line_num - 1,  # 0-based index for lines array
                }
            )

    return headers


def _extract_code_block_after_header(
    content: str, header: Dict[str, Any]
) -> Union[str, None]:
    """Extract the first code block after a header.

    This function looks for the first ``` fenced code block that appears
    after the given header, stopping if it encounters another header first.

    Args:
        content: Full markdown content
        header: Header dictionary with position info

    Returns:
        str or None: Code block content (excluding ``` markers), or None
                     if no code block found before the next header
    """
    lines = content.split("\n")
    start_line = header["position"] + 1  # Start searching after the header

    # Look for the start of a code block (```)
    code_start = None
    for i in range(start_line, len(lines)):
        if lines[i].strip().startswith("```"):
            code_start = i
            break
        # Stop if we hit another header
        if re.match(r"^#{1,5}\s+", lines[i].strip()):
            break

    if code_start is None:
        return None

    # Find the end of the code block
    code_end = None
    for i in range(code_start + 1, len(lines)):
        if lines[i].strip() == "```":
            code_end = i
            break

    if code_end is None:
        return None

    # Extract the code content (excluding the ``` lines)
    code_lines = lines[code_start + 1 : code_end]
    return "\n".join(code_lines)


def _find_duplicates(items: List[str]) -> List[str]:
    """Find duplicate items in a list.

    Args:
        items: List of items to check

    Returns:
        list: List of items that appear more than once (unique duplicates)
    """
    seen = set()
    duplicates = set()

    for item in items:
        if item in seen:
            duplicates.add(item)
        else:
            seen.add(item)

    return list(duplicates)
