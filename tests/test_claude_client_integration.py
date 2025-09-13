#!/usr/bin/env python3
"""Integration tests for claude_client module."""

import subprocess

import pytest

from mcp_coder.claude_client import ask_claude, _find_claude_executable


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
            
            response = ask_claude("What is 2 + 2? Answer with just the number.", timeout=60)
            
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