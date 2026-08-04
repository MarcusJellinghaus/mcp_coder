"""Startup banner + permission-notice wiring for ICoderApp."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_coder.icoder.ui import runtime_banner
from mcp_coder.icoder.ui.widgets.output_log import OutputLog

from .app import STYLE_CANCELLED

if TYPE_CHECKING:
    from .app import ICoderApp


def render_startup_banner(app: "ICoderApp") -> None:
    """Render the fresh-start runtime banner and startup permission notices.

    Extracted from ``ICoderApp.on_mount`` so the app shell stays thin. Applies
    the CLI-provided tool-display tier, then either resumes a prior log or
    renders the live runtime banner, and finally emits the prominent
    startup permission notices (#1061: broken skills + a degraded config).

    The permission-notice block is gated only on the fresh-start path and lives
    deliberately OUTSIDE the ``runtime_info`` branch — nesting it there drops the
    degraded line when ``runtime_info`` is ``None``.

    Args:
        app: The ICoderApp whose OutputLog receives the banner/notice lines.
    """
    core = app._core
    output = app.query_one(OutputLog)
    # Apply the CLI-provided initial tool-display tier before any output.
    output.set_tool_display_default(core.tool_display)  # type: ignore[arg-type]
    if app._resume_log_path is not None:
        app.do_resume(app._resume_log_path)
    elif core.runtime_info:
        lines = runtime_banner.format_runtime_info(core.runtime_info)
        output.append_text("\n".join(lines), style="dim")
    if app._resume_log_path is None:
        notices = runtime_banner.format_startup_permission_notices(
            core.broken_skills, core.permission_degraded
        )
        if notices:
            output.append_text("\n".join(notices), style=STYLE_CANCELLED)
