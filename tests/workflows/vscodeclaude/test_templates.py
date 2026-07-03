"""Tests for vscodeclaude template strings."""

from mcp_coder.workflows.vscodeclaude.templates import (
    GITIGNORE_ENTRY,
    INTERVENTION_WARNING,
    LAUNCHER_POSIX,
    LAUNCHER_WINDOWS,
)


def test_launcher_windows_format_substitution() -> None:
    """LAUNCHER_WINDOWS is a thin launcher into ``session_setup``.

    The only placeholder is ``{mcp_coder_install_path}`` (to locate the
    coordinator venv's Python). ``%CD%`` is the session directory passed as the
    module argument and ``|| pause`` keeps the window open on interpreter
    startup failure. After substitution no ``{`` placeholder must remain.
    """
    rendered = LAUNCHER_WINDOWS.format(mcp_coder_install_path="C:\\tool")
    assert "python.exe" in rendered
    assert "-m mcp_coder.workflows.vscodeclaude.session_setup" in rendered
    assert '"%CD%"' in rendered
    assert "|| pause" in rendered
    assert "{" not in rendered


def test_launcher_posix_format_substitution() -> None:
    """LAUNCHER_POSIX is the POSIX counterpart of LAUNCHER_WINDOWS.

    It starts with a bash shebang, invokes the coordinator venv's Python via a
    forward-slash path, passes ``$PWD`` as the session directory, and uses
    ``read -r -p`` (the POSIX equivalent of ``pause``) on failure.
    """
    rendered = LAUNCHER_POSIX.format(mcp_coder_install_path="/opt/tool")
    assert rendered.startswith("#!/usr/bin/env bash")
    assert "/.venv/bin/python" in rendered
    assert "-m mcp_coder.workflows.vscodeclaude.session_setup" in rendered
    assert '"$PWD"' in rendered
    assert "read -r -p" in rendered
    assert "{" not in rendered


def test_gitignore_entry_ignores_session_json() -> None:
    """GITIGNORE_ENTRY ignores the generated session-spec JSON.

    ``session_setup`` consumes ``.vscodeclaude_session.json`` written at launch
    time; it is auto-generated and must not be committed (issue #695).
    """
    assert ".vscodeclaude_session.json" in GITIGNORE_ENTRY


def test_intervention_warning_text() -> None:
    """INTERVENTION_WARNING holds the verbatim ``!! INTERVENTION MODE`` block.

    ``render_banner`` is its consumer: the warning is printed by Python (no
    shell), so it carries no ``{}`` placeholder and reproduces the two key
    lines from the retired INTERVENTION_SCRIPT_* templates.
    """
    assert (
        "INTERVENTION MODE - Automation may be running elsewhere"
        in INTERVENTION_WARNING
    )
    assert "No automated analysis will run." in INTERVENTION_WARNING
    assert "{" not in INTERVENTION_WARNING
