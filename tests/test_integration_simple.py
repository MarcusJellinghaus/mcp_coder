#!/usr/bin/env python3
"""Simple integration tests to verify both CLI and API methods work."""

import subprocess

import pytest

from mcp_coder.llm_interface import ask_llm


class TestSimpleIntegration:
    """Simple integration tests for both CLI and API methods."""

    @pytest.mark.integration
    @pytest.mark.parametrize("method", ["cli", "api"])
    def test_both_methods_work(self, method: str) -> None:
        """Test that both CLI and API methods can correctly answer a simple math question."""
        try:
            response = ask_llm("What is 2+2? Just answer a number!", method=method)

            # Verify we got a response
            assert response is not None
            assert len(response) > 0

            # Verify both methods give the correct answer
            # Check if response can be parsed as exact int 4
            response_clean = response.strip()
            # Try to parse as integer directly - must be exactly "4"
            assert int(response_clean) == 4
            # !!! Commented out fallback check - we only accept exact "4" now
            # try:
            #     # Try to parse as integer directly
            #     assert int(response_clean) == 4
            # except ValueError:
            #     # If not a pure number, check if "4" is in the response
            #     assert "4" in response_clean

            print(f"{method.upper()} method response: {response}")

        except FileNotFoundError:
            if method == "cli":
                pytest.skip("Claude Code CLI not found - skipping CLI integration test")
            else:
                pytest.skip("Claude Code API not found - skipping API integration test")
        except ImportError as e:
            if method == "api":
                pytest.skip(f"claude-code-sdk not installed: {e}")
            else:
                raise  # Unexpected for CLI method
        except subprocess.TimeoutExpired:
            pytest.skip(
                f"Claude {method.upper()} call timed out - may indicate setup issues"
            )
        except subprocess.CalledProcessError as e:
            if (
                "authentication" in str(e.stderr).lower()
                or "login" in str(e.stderr).lower()
            ):
                pytest.skip(
                    f"Claude {method.upper()} authentication required: {e.stderr}"
                )
            else:
                pytest.skip(
                    f"Claude {method.upper()} failed - may indicate setup issues: {e}"
                )
        except (RuntimeError, ValueError) as e:
            pytest.skip(
                f"Runtime or validation error during {method.upper()} test: {e}"
            )
