from unittest.mock import MagicMock, patch

from mcp_coder.utils.user_config import get_cache_refresh_minutes


class TestGetCacheRefreshMinutes:
    """Tests for get_cache_refresh_minutes function.

    Note: This function has been moved to utils.user_config module.
    These tests patch the new location.
    """

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_default(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test default value when config not set."""
        # Setup - return batch config values dict with None value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): None,
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # 24 hours

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_custom_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test custom value from config."""
        # Setup - return batch config values dict with custom value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): 720,
        }

        result = get_cache_refresh_minutes()
        assert result == 720  # 12 hours

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_invalid_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for invalid values."""
        # Setup - return batch config values dict with invalid value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): "invalid",
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default

    @patch("mcp_coder.utils.user_config.get_config_values")
    def test_get_cache_refresh_minutes_negative_value(
        self, mock_get_config: MagicMock
    ) -> None:
        """Test fallback to default for negative values."""
        # Setup - return batch config values dict with negative value
        mock_get_config.return_value = {
            ("coordinator", "cache_refresh_minutes"): -60,
        }

        result = get_cache_refresh_minutes()
        assert result == 1440  # Falls back to default
