"""Claude CLI verification functionality."""

import argparse
import logging
from typing import Optional

from .claude_code_api import _verify_claude_before_use
from .claude_executable_finder import verify_claude_installation

logger = logging.getLogger(__name__)


def verify_claude_cli_installation(args: argparse.Namespace) -> int:
    """Execute verification command to check Claude installation. Returns exit code."""
    logger.info("Executing Claude installation verification")

    print("Verifying Claude Code CLI installation...\n")

    # Run basic verification
    verification_result = verify_claude_installation()

    print("=== BASIC VERIFICATION ===")
    print(f"Claude CLI Found: {'✓ YES' if verification_result['found'] else '✗ NO'}")
    if verification_result["path"]:
        print(f"Location: {verification_result['path']}")
    if verification_result["version"]:
        print(f"Version: {verification_result['version']}")
    print(f"Executable Works: {'✓ YES' if verification_result['works'] else '✗ NO'}")

    if verification_result["error"]:
        print(f"Error: {verification_result['error']}")

    print("\n=== ADVANCED VERIFICATION ===")

    # Run advanced verification (same as used by API)
    try:
        success, claude_path, error_msg = _verify_claude_before_use()
        print(f"API Integration: {'✓ OK' if success else '✗ FAILED'}")
        if success:
            print(f"Verified Path: {claude_path}")
        elif error_msg:
            print(f"API Error: {error_msg}")
    except Exception as e:
        print(f"API Integration: ✗ EXCEPTION - {e}")
        success = False

    print("\n=== RECOMMENDATIONS ===")

    if verification_result["found"] and verification_result["works"] and success:
        print("✓ Claude Code CLI is properly installed and configured!")
        print("✓ You can use mcp-coder commands that require LLM integration.")
        logger.info("Claude verification completed successfully")
        return 0
    else:
        print("⚠ Issues detected with Claude Code CLI installation:")

        if not verification_result["found"]:
            print("  1. Install Claude CLI: npm install -g @anthropic-ai/claude-code")
            print("  2. Restart your terminal")
            print("  3. Verify installation: claude --version")

        if verification_result["found"] and not verification_result["works"]:
            print("  1. Check if Claude CLI is executable")
            print(
                "  2. Try reinstalling: npm uninstall -g @anthropic-ai/claude-code && npm install -g @anthropic-ai/claude-code"
            )
            print("  3. Ensure you have proper permissions")

        if verification_result["works"] and not success:
            print("  1. Check PATH environment variable includes Claude directory")
            print("  2. Restart your terminal or IDE")
            print("  3. Try running from a different directory")

        print("\nFor more help, visit: https://docs.anthropic.com/en/docs/claude-code")
        logger.warning("Claude verification completed with issues")
        return 1
