"""Tests for get_dispatch_delay_seconds and its [coordinator] schema entry.

load_config is patched so the real get_config_values and its schema type
check run, without reading the user's config file.
"""

import logging
from typing import Any
from unittest.mock import patch

import pytest

from mcp_coder.utils.user_config import (
    DEFAULT_DISPATCH_DELAY_SECONDS,
    _get_field_def,
    get_dispatch_delay_seconds,
)

_LOAD_CONFIG = "mcp_coder.utils.user_config.load_config"


def _run_with_config(config: dict[str, Any]) -> int:
    with patch(_LOAD_CONFIG, return_value=config):
        return get_dispatch_delay_seconds()


class TestGetDispatchDelaySeconds:
    """Tests for get_dispatch_delay_seconds."""

    def test_default_is_15(self) -> None:
        assert DEFAULT_DISPATCH_DELAY_SECONDS == 15

    @pytest.mark.parametrize(
        "config",
        [{}, {"coordinator": {}}, {"coordinator": {"cache_refresh_minutes": 60}}],
    )
    def test_absent_returns_default(self, config: dict[str, Any]) -> None:
        assert _run_with_config(config) == 15

    def test_configured_value_returned(self) -> None:
        assert _run_with_config({"coordinator": {"dispatch_delay_seconds": 30}}) == 30

    @pytest.mark.parametrize("value", [0, -5])
    def test_not_positive_returns_default_with_warning(
        self, value: int, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="mcp_coder.utils.user_config"):
            result = _run_with_config(
                {"coordinator": {"dispatch_delay_seconds": value}}
            )

        assert result == 15
        warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert any("dispatch_delay_seconds" in r.getMessage() for r in warnings)

    def test_string_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="dispatch_delay_seconds"):
            _run_with_config({"coordinator": {"dispatch_delay_seconds": "15"}})

    def test_bool_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="dispatch_delay_seconds"):
            _run_with_config({"coordinator": {"dispatch_delay_seconds": True}})


class TestDispatchDelaySchema:
    """The schema entry keeps `mcp-coder verify` from reporting an unknown key."""

    def test_schema_field_is_int(self) -> None:
        field_def = _get_field_def("coordinator", "dispatch_delay_seconds")

        assert field_def is not None
        assert field_def.field_type is int
