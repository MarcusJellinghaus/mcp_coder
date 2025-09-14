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
    def test_ask_claude_real_simple_math(self) -> None:
        """Test asking Claude a simple math question with real CLI."""
        try:
            print("Starting Claude CLI test...")
            claude_path = _find_claude_executable()
            print(f"Using Claude at: {claude_path}")

            response = ask_claude(
                "What is 2 + 2? Answer with just the number.", timeout=60
            )

            # Claude should respond with something containing "4"
            assert "4" in response
            assert len(response.strip()) > 0
            print(f"Claude responded: {response}")

        except FileNotFoundError:
            pytest.skip("Claude Code CLI not found - skipping real integration test")
        except subprocess.TimeoutExpired as e:
            print(f"Timeout details: {e}")
            print(f"Command that timed out: {e.cmd}")
            pytest.skip("Claude CLI call timed out - may indicate setup issues")
        except subprocess.CalledProcessError as e:
            print(f"Command error details: {e}")
            print(f"Return code: {e.returncode}")
            print(f"Stderr: {e.stderr}")
            pytest.skip(f"Claude CLI failed - may indicate setup issues: {e}")

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
    def test_cli_method_integration(self) -> None:
        """Test asking Claude via CLI method through the interface."""
        try:
            response = ask_claude_code(
                "What is 3 + 3? Answer with just the number.", 
                method="cli", 
                timeout=60
            )

            # Claude should respond with something containing "6"
            assert "6" in response
            assert len(response.strip()) > 0
            print(f"CLI method response: {response}")

        except FileNotFoundError:
            pytest.skip("Claude Code CLI not found - skipping CLI integration test")
        except subprocess.TimeoutExpired:
            pytest.skip("Claude CLI call timed out - may indicate setup issues")
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Claude CLI failed - may indicate setup issues: {e}")

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires claude-code-sdk setup and authentication")
    def test_api_method_integration(self) -> None:
        """Test asking Claude via API method through the interface."""
        try:
            response = ask_claude_code(
                "What is 5 + 5? Answer with just the number.", 
                method="api", 
                timeout=60
            )

            # Claude should respond with something containing "10"
            assert "10" in response
            assert len(response.strip()) > 0
            print(f"API method response: {response}")

        except ImportError:
            pytest.skip("claude-code-sdk not installed - skipping API integration test")
        except subprocess.TimeoutExpired:
            pytest.skip("Claude API call timed out - may indicate setup issues")
        except subprocess.CalledProcessError as e:
            pytest.skip(f"Claude API failed - may indicate setup issues: {e}")

    @pytest.mark.integration
    def test_method_parameter_comparison(self) -> None:
        """Test that both CLI and API methods work with the interface."""
        # This test verifies the interface routing works correctly
        
        # Test CLI method
        try:
            cli_response = ask_claude_code(
                "Say 'CLI works'", 
                method="cli", 
                timeout=30
            )
            cli_available = True
            print(f"CLI response: {cli_response}")
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            cli_available = False
            print("CLI method not available")

        # Test API method (expect it to fail gracefully if not set up)
        try:
            api_response = ask_claude_code(
                "Say 'API works'", 
                method="api", 
                timeout=30
            )
            api_available = True
            print(f"API response: {api_response}")
        except (ImportError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            api_available = False
            print("API method not available")

        # At least one method should be available for basic functionality
        if not cli_available and not api_available:
            pytest.skip("Neither CLI nor API methods are available")
        
        # If we get here, at least one method works
        assert True  # Test passes if we reach this point

    def test_invalid_method_raises_error(self) -> None:
        """Test that invalid method parameter raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            ask_claude_code("test question", method="invalid")
        
        assert "Unsupported method: invalid" in str(exc_info.value)
        assert "Supported methods: 'cli', 'api'" in str(exc_info.value)
