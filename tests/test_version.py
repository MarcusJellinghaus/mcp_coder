"""Tests for version management utilities."""

import tempfile
from pathlib import Path

import pytest

from mcp_coder.utils.version import (
    InvalidVersionFormatError,
    VersionMismatchError,
    format_version,
    get_package_version,
    is_prerelease,
    parse_version,
    validate_tag_version,
)


class TestParseVersion:
    """Tests for parse_version function."""

    def test_parse_stable_version(self) -> None:
        """Test parsing a stable version string."""
        major, minor, patch, prerelease = parse_version("1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == ""

    def test_parse_version_with_v_prefix(self) -> None:
        """Test parsing version with 'v' prefix."""
        major, minor, patch, prerelease = parse_version("v1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == ""

    def test_parse_prerelease_rc(self) -> None:
        """Test parsing release candidate version."""
        major, minor, patch, prerelease = parse_version("2.0.0-rc1")
        assert major == 2
        assert minor == 0
        assert patch == 0
        assert prerelease == "rc1"

    def test_parse_prerelease_alpha(self) -> None:
        """Test parsing alpha version."""
        major, minor, patch, prerelease = parse_version("1.5.0-alpha")
        assert major == 1
        assert minor == 5
        assert patch == 0
        assert prerelease == "alpha"

    def test_parse_prerelease_beta_with_number(self) -> None:
        """Test parsing beta version with number."""
        major, minor, patch, prerelease = parse_version("3.0.0-beta.2")
        assert major == 3
        assert minor == 0
        assert patch == 0
        assert prerelease == "beta.2"

    def test_parse_invalid_format_missing_parts(self) -> None:
        """Test parsing version with missing parts raises error."""
        with pytest.raises(InvalidVersionFormatError) as exc_info:
            parse_version("1.2")
        assert "Invalid version format" in str(exc_info.value)

    def test_parse_invalid_format_non_numeric(self) -> None:
        """Test parsing version with non-numeric parts raises error."""
        with pytest.raises(InvalidVersionFormatError) as exc_info:
            parse_version("1.x.3")
        assert "Invalid version format" in str(exc_info.value)

    def test_parse_invalid_format_extra_parts(self) -> None:
        """Test parsing version with extra parts raises error."""
        with pytest.raises(InvalidVersionFormatError) as exc_info:
            parse_version("1.2.3.4")
        assert "Invalid version format" in str(exc_info.value)


class TestValidateTagVersion:
    """Tests for validate_tag_version function."""

    def test_matching_stable_versions(self) -> None:
        """Test validation passes for matching stable versions."""
        # Should not raise
        validate_tag_version("1.2.3", "1.2.3")
        validate_tag_version("v1.2.3", "1.2.3")

    def test_matching_prerelease_versions(self) -> None:
        """Test validation passes for matching prerelease versions."""
        # Should not raise
        validate_tag_version("2.0.0-rc1", "2.0.0-rc1")
        validate_tag_version("v1.5.0-alpha", "1.5.0-alpha")

    def test_mismatched_major_version(self) -> None:
        """Test validation fails for mismatched major versions."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_tag_version("2.0.0", "1.0.0")
        assert "does not match" in str(exc_info.value)

    def test_mismatched_minor_version(self) -> None:
        """Test validation fails for mismatched minor versions."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_tag_version("1.3.0", "1.2.0")
        assert "does not match" in str(exc_info.value)

    def test_mismatched_patch_version(self) -> None:
        """Test validation fails for mismatched patch versions."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_tag_version("1.2.4", "1.2.3")
        assert "does not match" in str(exc_info.value)

    def test_mismatched_prerelease(self) -> None:
        """Test validation fails for mismatched prerelease identifiers."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_tag_version("1.2.3-rc1", "1.2.3-rc2")
        assert "does not match" in str(exc_info.value)

    def test_stable_vs_prerelease_mismatch(self) -> None:
        """Test validation fails when one is stable and other is prerelease."""
        with pytest.raises(VersionMismatchError) as exc_info:
            validate_tag_version("1.2.3", "1.2.3-rc1")
        assert "does not match" in str(exc_info.value)


class TestFormatVersion:
    """Tests for format_version function."""

    def test_format_stable_version(self) -> None:
        """Test formatting a stable version."""
        assert format_version(1, 2, 3) == "1.2.3"

    def test_format_prerelease_version(self) -> None:
        """Test formatting a prerelease version."""
        assert format_version(2, 0, 0, "rc1") == "2.0.0-rc1"
        assert format_version(1, 5, 0, "alpha") == "1.5.0-alpha"
        assert format_version(3, 0, 0, "beta.2") == "3.0.0-beta.2"

    def test_format_zero_version(self) -> None:
        """Test formatting version with zeros."""
        assert format_version(0, 0, 1) == "0.0.1"
        assert format_version(1, 0, 0) == "1.0.0"


class TestIsPrerelease:
    """Tests for is_prerelease function."""

    def test_stable_version_not_prerelease(self) -> None:
        """Test stable versions are not prereleases."""
        assert not is_prerelease("1.2.3")
        assert not is_prerelease("v2.0.0")

    def test_rc_is_prerelease(self) -> None:
        """Test release candidates are prereleases."""
        assert is_prerelease("1.0.0-rc1")
        assert is_prerelease("v2.0.0-rc2")

    def test_alpha_is_prerelease(self) -> None:
        """Test alpha versions are prereleases."""
        assert is_prerelease("1.5.0-alpha")

    def test_beta_is_prerelease(self) -> None:
        """Test beta versions are prereleases."""
        assert is_prerelease("3.0.0-beta.2")


class TestGetPackageVersion:
    """Tests for get_package_version function."""

    def test_get_version_from_real_package(self) -> None:
        """Test getting version from actual package."""
        # This test runs against the real package
        version = get_package_version(Path.cwd())
        # Should be a valid semantic version
        major, minor, patch, _ = parse_version(version)
        assert isinstance(major, int)
        assert isinstance(minor, int)
        assert isinstance(patch, int)

    def test_get_version_missing_init_file(self) -> None:
        """Test error when __init__.py doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                get_package_version(Path(tmpdir))

    def test_get_version_missing_version_variable(self) -> None:
        """Test error when __version__ is not defined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            init_file = tmp_path / "src" / "mcp_coder" / "__init__.py"
            init_file.parent.mkdir(parents=True)
            init_file.write_text("# No version here\n")

            with pytest.raises(ValueError) as exc_info:
                get_package_version(tmp_path)
            assert "Cannot find __version__" in str(exc_info.value)
