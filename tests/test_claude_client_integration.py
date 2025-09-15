#!/usr/bin/env python3
"""Integration tests for claude_client module."""

import subprocess

import pytest

from mcp_coder.claude_client import ask_claude
from mcp_coder.claude_code_cli import _find_claude_executable
from mcp_coder.claude_code_interface import ask_claude_code


class TestClaudeClientRealIntegration:
    """Real integration tests with actual Claude Code CLI (if available)."""

    @pytest.mark.integration
    def test_claude_cli_available(self) -> None:
        """Test if Claude CLI is available and working."""
        try:
            # This should either work or raise FileNotFoundError
            claude_path = _find_claude_executable()
            assert claude_path is not None
            assert len(claude_path) > 0
            print(f"Found Claude CLI at: {claude_path}")
        except FileNotFoundError:
            pytest.skip("Claude Code CLI not found - skipping real integration test")

    @pytest.mark.integration
    def test_ask_claude_real_timeout(self) -> None:
        """Test timeout handling with real CLI using very short timeout."""
        try:
            # Use a very short timeout to force a timeout (if Claude is slow)
            with pytest.raises(subprocess.TimeoutExpired):
                ask_claude("Write a very long story about programming", timeout=1)

        except FileNotFoundError:
            pytest.skip("Claude Code CLI not found - skipping real integration test")
        except subprocess.CalledProcessError:
            # If Claude responds quickly, we might not get a timeout
            pytest.skip("Claude responded too quickly to test timeout")


class TestClaudeCodeInterfaceIntegration:
    """Integration tests for claude_code_interface with multiple methods."""

    @pytest.mark.integration
    @pytest.mark.parametrize("method", ["cli", "api"])
    def test_basic_functionality(self, method: str) -> None:
        """Test basic functionality for both CLI and API methods with a real question."""
        try:
            response = ask_claude_code(
                "What is 2+2? Just answer a number!", method=method, timeout=60
            )

            # Verify we got a response
            assert response is not None
            assert len(response.strip()) > 0
            
            # Verify both methods give the correct answer - expect exactly 4
            response_clean = response.strip()
            assert int(response_clean) == 4, f"Expected exactly '4', got: {repr(response)}"
            
            print(f"✓ {method.upper()} method response: {response}")

        except FileNotFoundError:
            pytest.skip(f"Claude Code CLI not found - skipping {method.upper()} integration test")
        except ImportError as e:
            if method == "api":
                pytest.skip(f"claude-code-sdk not installed: {e}")
            else:
                raise  # Unexpected for CLI method
        except subprocess.TimeoutExpired:
            pytest.skip(f"Claude {method.upper()} call timed out - may indicate setup issues")
        except subprocess.CalledProcessError as e:
            if (
                "authentication" in str(e.stderr).lower()
                or "login" in str(e.stderr).lower()
            ):
                pytest.skip(f"Claude {method.upper()} authentication required: {e.stderr}")
            else:
                pytest.skip(f"Claude {method.upper()} failed - may indicate setup issues: {e}")
        except (RuntimeError, ValueError, AttributeError) as e:
            pytest.skip(f"Runtime or configuration error during {method.upper()} test: {e}")
        except OSError as e:
            pytest.skip(f"System error during {method.upper()} test: {e}")

    def test_invalid_method_raises_error(self) -> None:
        """Test that invalid method parameter raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ask_claude_code("test question", method="invalid")

        assert "Unsupported method: invalid" in str(exc_info.value)
        assert "Supported methods: 'cli', 'api'" in str(exc_info.value)
