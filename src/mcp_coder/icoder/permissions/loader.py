"""I/O loader for iCoder ``.icoder/`` permission settings (JSONC → model).

This module is the only member of the permissions package permitted to touch
``json``/``jsonschema`` and the filesystem; ``model``/``matcher``/``resolver``
stay pure. It reads the layered ``settings.json`` files, validates them, and
builds the in-memory :class:`~mcp_coder.icoder.permissions.model.PermissionConfig`
the resolver consumes.

Step 2 provides only :func:`_strip_jsonc`, the string/escape-aware JSONC
preprocessor. It is a security surface: comment-like sequences inside string
literals (URLs, ``"a // b"``, escaped quotes) must survive intact.
"""

from __future__ import annotations


def _strip_jsonc(text: str) -> str:
    """Strip // and /* */ comments and trailing commas from JSONC text.

    String/escape-aware: comment markers and commas inside string literals
    are preserved.

    Args:
        text: The JSONC source to preprocess.

    Returns:
        A comment-free, trailing-comma-free JSON string suitable for
        ``json.loads``.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    in_str = False
    esc = False
    while i < n:
        c = text[i]
        peek = text[i + 1] if i + 1 < n else ""
        if in_str:
            # Inside "...": copy verbatim, tracking backslash escapes so an
            # escaped quote (\") does not close the string.
            out.append(c)
            esc = c == "\\" and not esc
            in_str = c != '"' or esc
        elif c == '"':
            in_str = True
            out.append(c)
        elif c == "/" and peek == "/":
            # Line comment: skip to (but keep) the newline.
            while i < n and text[i] != "\n":
                i += 1
            continue
        elif c == "/" and peek == "*":
            # Block comment: skip through the closing */.
            i += 2
            while i < n and not (text[i] == "*" and i + 1 < n and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        elif c in "}]":
            # Drop a trailing comma sitting before this closing bracket,
            # skipping any whitespace already emitted between them.
            j = len(out) - 1
            while j >= 0 and out[j].isspace():
                j -= 1
            if j >= 0 and out[j] == ",":
                del out[j]
            out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)
