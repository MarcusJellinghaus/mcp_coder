"""Claude CLI verification functionality."""

import logging
from typing import Any, Optional, Tuple

from .claude_executable_finder import (
    setup_claude_path,
    verify_claude_installation,
)

logger = logging.getLogger(__name__)


def _verify_claude_before_use() -> Tuple[bool, Optional[str], Optional[str]]:
    """Verify Claude installation before attempting to use it.

    Returns:
        Tuple of (success, claude_path, error_message)
    """
    logger.debug("Verifying Claude installation before use")

    try:
        # First try to setup the PATH
        claude_path = setup_claude_path()
        if claude_path:
            logger.debug("Claude CLI found and PATH configured: %s", claude_path)
        else:
            logger.warning(
                "setup_claude_path() returned None - Claude not found in standard locations"
            )
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.warning("Error during PATH setup: %s", e)
        claude_path = None

    # Run detailed verification
    verification_result = verify_claude_installation()

    logger.debug("Claude verification result: %s", verification_result)

    if verification_result["found"] and verification_result["works"]:
        return True, verification_result["path"], None
    else:
        error_msg = verification_result.get("error", "Claude CLI verification failed")

        # If verification failed but we found Claude, provide more helpful error message
        if verification_result["found"] and verification_result["path"]:
            detailed_error = f"Claude found at {verification_result['path']} but version check failed: {error_msg}"
            logger.warning("Claude verification detailed error: %s", detailed_error)
            return False, verification_result.get("path"), detailed_error

        return False, verification_result.get("path"), error_msg


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
    if not basic["found"]:
        result["cli_found"][
            "install_hint"
        ] = "https://docs.anthropic.com/en/docs/claude-code"

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
        success, _, error_msg = _verify_claude_before_use()
        api_ok = success
        result["api_integration"] = {
            "ok": success,
            "value": "OK" if success else "FAILED",
            "error": error_msg if not success else None,
        }
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
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
