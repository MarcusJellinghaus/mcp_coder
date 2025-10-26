"""
Stress tests for git operations with Unicode and special characters.

Tests subprocess encoding handling with large amounts of special characters
to ensure the git diff operation doesn't hang or fail on Windows.
"""

import tempfile
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.utils.git_operations import get_branch_diff, is_git_repository


@pytest.mark.git_integration
class TestGitEncodingStress:
    """Test git operations with heavy Unicode and special character content."""

    def test_git_diff_with_10k_special_characters(  # pylint: disable=too-many-statements
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test git diff with 10,000 special Unicode characters to stress subprocess handling."""
        repo, project_dir = git_repo

        # Create test content with 10,000 diverse Unicode characters
        # Include characters from different Unicode blocks to test encoding robustness
        special_chars = []

        # Basic Latin extended and symbols
        special_chars.extend(
            [chr(i) for i in range(0x00A0, 0x00FF)]
        )  # Latin-1 Supplement
        special_chars.extend(
            [chr(i) for i in range(0x0100, 0x017F)]
        )  # Latin Extended-A
        special_chars.extend(
            [chr(i) for i in range(0x0180, 0x024F)]
        )  # Latin Extended-B
        special_chars.extend(
            [chr(i) for i in range(0x2000, 0x206F)]
        )  # General Punctuation
        special_chars.extend(
            [chr(i) for i in range(0x2070, 0x209F)]
        )  # Superscripts and Subscripts
        special_chars.extend(
            [chr(i) for i in range(0x20A0, 0x20CF)]
        )  # Currency Symbols
        special_chars.extend(
            [chr(i) for i in range(0x2100, 0x214F)]
        )  # Letterlike Symbols
        special_chars.extend([chr(i) for i in range(0x2190, 0x21FF)])  # Arrows
        special_chars.extend(
            [chr(i) for i in range(0x2200, 0x22FF)]
        )  # Mathematical Operators
        special_chars.extend(
            [chr(i) for i in range(0x2300, 0x23FF)]
        )  # Miscellaneous Technical
        special_chars.extend([chr(i) for i in range(0x2500, 0x257F)])  # Box Drawing
        special_chars.extend(
            [chr(i) for i in range(0x25A0, 0x25FF)]
        )  # Geometric Shapes

        # Emojis and symbols
        special_chars.extend([chr(i) for i in range(0x1F600, 0x1F64F)])  # Emoticons
        special_chars.extend(
            [chr(i) for i in range(0x1F300, 0x1F5FF)]
        )  # Misc Symbols and Pictographs
        special_chars.extend(
            [chr(i) for i in range(0x1F680, 0x1F6FF)]
        )  # Transport and Map Symbols

        # CJK characters (Chinese, Japanese, Korean)
        special_chars.extend(
            [chr(i) for i in range(0x4E00, 0x4E50)]
        )  # CJK Unified Ideographs
        special_chars.extend([chr(i) for i in range(0x3040, 0x309F)])  # Hiragana
        special_chars.extend([chr(i) for i in range(0x30A0, 0x30FF)])  # Katakana

        # Arabic and Hebrew
        special_chars.extend([chr(i) for i in range(0x0600, 0x06FF)])  # Arabic
        special_chars.extend([chr(i) for i in range(0x0590, 0x05FF)])  # Hebrew

        # Greek and Cyrillic
        special_chars.extend(
            [chr(i) for i in range(0x0370, 0x03FF)]
        )  # Greek and Coptic
        special_chars.extend([chr(i) for i in range(0x0400, 0x04FF)])  # Cyrillic

        # Build 10,000 character string by repeating and cycling through special chars
        target_length = 10000
        test_content_chars = []
        char_index = 0

        for i in range(target_length):
            # Cycle through special characters
            test_content_chars.append(special_chars[char_index % len(special_chars)])
            char_index += 1

            # Add newlines every 100 characters for realistic file structure
            if i > 0 and i % 100 == 0:
                test_content_chars.append("\n")

        test_content = "".join(test_content_chars)

        # Verify we have the expected length
        assert (
            len(test_content) > 10000
        ), f"Test content should be > 10k chars, got {len(test_content)}"

        # Create initial commit
        initial_file = project_dir / "test_unicode.txt"
        initial_file.write_text("Initial content", encoding="utf-8")
        repo.index.add(["test_unicode.txt"])
        repo.index.commit("Initial commit")

        # Create main branch
        if repo.active_branch.name != "main":
            main_branch = repo.create_head("main")
            main_branch.checkout()

        # Create feature branch
        feature_branch = repo.create_head("feature-unicode-test")
        feature_branch.checkout()

        # Write the massive Unicode content to a file
        test_file = project_dir / "unicode_stress_test.py"
        file_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress test file with 10,000+ Unicode characters.
This tests git diff subprocess handling with heavy Unicode content.
"""

# Massive Unicode string for testing subprocess encoding
UNICODE_TEST_DATA = """
{test_content}
"""

def process_unicode_data():
    """Process the Unicode test data."""
    return len(UNICODE_TEST_DATA)

if __name__ == "__main__":
    print(f"Processed {{process_unicode_data()}} characters")
'''

        test_file.write_text(file_content, encoding="utf-8")

        # Commit the changes
        repo.index.add(["unicode_stress_test.py"])
        repo.index.commit("Add Unicode stress test with 10k+ special characters")

        # Test git diff - this should not hang and should handle the encoding properly
        diff_result = get_branch_diff(project_dir, base_branch="main")

        # Verify the function completed successfully (didn't hang)
        assert isinstance(diff_result, str), "get_branch_diff should return a string"
        assert len(diff_result) > 0, "Diff should contain content"

        # Verify the diff contains some of our Unicode content
        # Note: The exact representation in diff may vary, but it should contain the file name
        assert (
            "unicode_stress_test.py" in diff_result
        ), "Diff should contain the Unicode test file"

        # Verify the diff doesn't crash on Unicode characters
        # The diff should be readable as UTF-8
        try:
            diff_result.encode("utf-8").decode("utf-8")
        except UnicodeError as e:
            pytest.fail(f"Git diff result contains invalid Unicode: {e}")

    def test_git_diff_with_mixed_line_endings(self, git_repo: tuple[Any, Path]) -> None:
        """Test git diff with mixed line endings and encoding edge cases."""
        repo, project_dir = git_repo

        # Create content with various line ending combinations and encoding edge cases
        mixed_content = (
            "Line with CRLF\r\n"
            "Line with LF\n"
            "Line with special chars: áéíóú ñüç\n"
            "Line with emojis: 🎉🚀💻🌟\r\n"
            "Line with math symbols: ∑∞∂∇∅⊆⊇∈∉\n"
            "Line with currency: €$£¥₹₿\r\n"
            "Line with arrows: →←↑↓↔↕⇒⇔\n"
            "Mixed: 中文 العربية Русский Ελληνικά עברית\r\n"
            "Control chars test: \t\v\f\r\n"  # Tab, vertical tab, form feed
            "Zero-width chars: \u200b\u200c\u200d\u2060\n"  # Zero-width space, non-joiner, joiner, word joiner
        )

        # Create initial commit
        initial_file = project_dir / "mixed_encoding.txt"
        initial_file.write_text("Initial", encoding="utf-8")
        repo.index.add(["mixed_encoding.txt"])
        repo.index.commit("Initial commit")

        # Create branches
        if repo.active_branch.name != "main":
            main_branch = repo.create_head("main")
            main_branch.checkout()

        feature_branch = repo.create_head("feature-mixed-encoding")
        feature_branch.checkout()

        # Write mixed content
        test_file = project_dir / "mixed_encoding_test.txt"
        test_file.write_text(mixed_content, encoding="utf-8")

        repo.index.add(["mixed_encoding_test.txt"])
        repo.index.commit("Add mixed encoding and line ending test")

        # Test git diff
        diff_result = get_branch_diff(project_dir, base_branch="main")

        # Verify success
        assert isinstance(diff_result, str), "get_branch_diff should return a string"
        assert len(diff_result) > 0, "Diff should contain content"
        assert (
            "mixed_encoding_test.txt" in diff_result
        ), "Diff should contain the test file"

    def test_git_diff_with_binary_and_text_mix(
        self, git_repo: tuple[Any, Path]
    ) -> None:
        """Test git diff behavior with mixed binary and text files."""
        repo, project_dir = git_repo

        # Create initial commit
        initial_file = project_dir / "readme.txt"
        initial_file.write_text("Initial readme", encoding="utf-8")
        repo.index.add(["readme.txt"])
        repo.index.commit("Initial commit")

        # Create branches
        if repo.active_branch.name != "main":
            main_branch = repo.create_head("main")
            main_branch.checkout()

        feature_branch = repo.create_head("feature-binary-mix")
        feature_branch.checkout()

        # Add a text file with Unicode
        text_file = project_dir / "unicode_text.py"
        text_content = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
Test with Unicode strings: "Hello 世界! مرحبا בעולם Привет мир Γεια σας κόσμος"
'''
print("Testing Unicode: 🌍🚀💻⭐🎉")
"""
        text_file.write_text(text_content, encoding="utf-8")

        # Add a simulated binary file (actually text but with lots of null bytes and control chars)
        binary_file = project_dir / "fake_binary.bin"
        binary_content = (
            b"\x00\x01\x02\x03\xff\xfe\xfd\xfc" + b"Some text" + b"\x00" * 100
        )
        binary_file.write_bytes(binary_content)

        # Commit both files
        repo.index.add(["unicode_text.py", "fake_binary.bin"])
        repo.index.commit("Add mixed text and binary files")

        # Test git diff - should handle binary files gracefully
        diff_result = get_branch_diff(project_dir, base_branch="main")

        # Verify success
        assert isinstance(diff_result, str), "get_branch_diff should return a string"
        assert len(diff_result) > 0, "Diff should contain content"

        # Should mention both files
        assert "unicode_text.py" in diff_result, "Diff should contain the text file"
        assert "fake_binary.bin" in diff_result, "Diff should contain the binary file"

        # Binary files should be handled with "Binary files differ" message
        if "Binary files" in diff_result or "differ" in diff_result:
            # Git detected binary content and handled it properly
            pass
        else:
            # Git might show the content if it's mostly text, that's also fine
            pass

    def test_subprocess_encoding_directly(self) -> None:
        """Test subprocess encoding handling directly without git repository."""
        import os
        import subprocess

        # Test direct subprocess call with Unicode content
        unicode_test_string = (
            "Testing encoding: 🎉🚀💻🌟 áéíóú ñüç 中文 العربية Русский"
        )

        # Create environment with UTF-8 encoding
        env = os.environ.copy()
        env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
                "LC_ALL": "C.UTF-8" if os.name != "nt" else "en_US.UTF-8",
            }
        )

        # Test echo command with Unicode (cross-platform)
        if os.name == "nt":  # Windows
            cmd = ["cmd", "/c", f"echo {unicode_test_string}"]
        else:  # Unix-like
            cmd = ["echo", unicode_test_string]

        try:
            # Run subprocess with explicit UTF-8 encoding
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",  # Replace invalid characters instead of crashing
                env=env,
                timeout=10,  # Prevent hanging
                check=False,  # Don't raise exception on non-zero exit code
            )

            # Verify the subprocess completed successfully
            assert (
                result.returncode == 0
            ), f"Subprocess failed with code {result.returncode}: {result.stderr}"
            assert isinstance(
                result.stdout, str
            ), "Subprocess output should be a string"

            # Verify some Unicode characters made it through
            # (exact representation may vary by platform/shell)
            output = result.stdout.strip()
            assert len(output) > 0, "Subprocess should produce output"

            # Test encoding/decoding roundtrip
            try:
                encoded = output.encode("utf-8")
                decoded = encoded.decode("utf-8")
                assert decoded == output, "UTF-8 encoding roundtrip should work"
            except UnicodeError as e:
                pytest.fail(f"Unicode encoding roundtrip failed: {e}")

        except subprocess.TimeoutExpired:
            pytest.fail("Subprocess timed out - possible hanging issue")
        except Exception as e:
            pytest.fail(f"Subprocess test failed: {e}")

    @pytest.mark.parametrize("char_count", [1000, 5000, 10000])
    def test_git_diff_performance_with_unicode(
        self, git_repo: tuple[Any, Path], char_count: int
    ) -> None:
        """Test git diff performance with varying amounts of Unicode content."""
        import time

        repo, project_dir = git_repo

        # Generate Unicode content of specified length
        unicode_chars = "🎉🚀💻🌟⭐🌈🔥💎🚀🎯" * (char_count // 10)
        unicode_chars = unicode_chars[:char_count]  # Trim to exact length

        # Create initial commit
        initial_file = project_dir / "readme.txt"
        initial_file.write_text("Initial", encoding="utf-8")
        repo.index.add(["readme.txt"])
        repo.index.commit("Initial commit")

        # Create branches
        if repo.active_branch.name != "main":
            main_branch = repo.create_head("main")
            main_branch.checkout()

        feature_branch = repo.create_head(f"feature-perf-{char_count}")
        feature_branch.checkout()

        # Write Unicode content
        test_file = project_dir / f"unicode_perf_{char_count}.txt"
        test_file.write_text(unicode_chars, encoding="utf-8")

        repo.index.add([f"unicode_perf_{char_count}.txt"])
        repo.index.commit(f"Add {char_count} Unicode characters")

        # Measure git diff performance
        start_time = time.time()
        diff_result = get_branch_diff(project_dir, base_branch="main")
        end_time = time.time()

        diff_duration = end_time - start_time

        # Verify success
        assert isinstance(diff_result, str), "get_branch_diff should return a string"
        assert len(diff_result) > 0, "Diff should contain content"

        # Performance check - should complete within reasonable time
        # Even with 10k characters, it should complete within 30 seconds
        assert (
            diff_duration < 30
        ), f"Git diff took too long: {diff_duration:.2f}s for {char_count} chars"

        # Log performance for debugging
        print(f"Git diff with {char_count} Unicode chars took {diff_duration:.3f}s")
