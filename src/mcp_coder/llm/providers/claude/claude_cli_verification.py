"""Claude CLI verification functionality."""

import logging
from typing import Any

from .claude_code_api import _verify_claude_before_use
from .claude_executable_finder import verify_claude_installation

logger = logging.getLogger(__name__)


def verify_claude() -> dict[str, Any]:
    """Verify Claude CLI installation and return structured results.

    Returns a dict with verification results (no printing).
    The CLI layer handles all output formatting.

    Returns:
        Dict with keys: cli_found, cli_path (if found), cli_version (if available),
        cli_works, api_integration, overall_ok.
    """
    logger.info("Executing Claude installation verification")

    # Run basic verification
    basic = verify_claude_installation()

    result: dict[str, Any] = {
        "cli_found": {"ok": basic["found"], "value": "YES" if basic["found"] else "NO"},
    }

    if basic["path"]:
        result["cli_path"] = {"ok": True, "value": basic["path"]}

    if basic["version"]:
        result["cli_version"] = {"ok": True, "value": basic["version"]}

    result["cli_works"] = {
        "ok": basic["works"],
        "value": "YES" if basic["works"] else "NO",
    }

    # Run advanced verification (API integration)
    api_ok = False
    try:
        success, claude_path, error_msg = _verify_claude_before_use()
        api_ok = success
        result["api_integration"] = {
            "ok": success,
            "value": "OK" if success else "FAILED",
            "error": error_msg if not success else None,
        }
    except Exception as e:
        result["api_integration"] = {
            "ok": False,
            "value": "FAILED",
            "error": f"EXCEPTION - {e}",
        }

    # overall_ok = True means everything is working, False means action needed
    result["overall_ok"] = basic["found"] and basic["works"] and api_ok

    logger.info(
        "Claude verification completed %s",
        "successfully" if result["overall_ok"] else "with issues",
    )

    return result
