"""Test configuration for tools tests."""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from tests.utils.jenkins_operations.integration_fixtures import (
    jenkins_client as jenkins_client,
)
from tests.utils.jenkins_operations.integration_fixtures import (
    jenkins_test_setup as jenkins_test_setup,
)

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

# Bare name, not tools.jenkins_builds: the scripts import this module object,
# so the fixture's patches must target it.
jenkins_builds = importlib.import_module("jenkins_builds")

_FULL_CONFIG: dict[str, str | None] = {
    "server_url": "https://jenkins.example.com",
    "username": "user",
    "api_token": "token",
}


@pytest.fixture(name="client")
def fixture_client(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch config and JenkinsClient; return the client instance mock."""
    monkeypatch.setattr(jenkins_builds, "get_jenkins_config", lambda: _FULL_CONFIG)
    monkeypatch.setattr(jenkins_builds, "load_config", dict)
    client_cls = MagicMock()
    instance: MagicMock = client_cls.return_value
    instance.get_recent_builds.return_value = []
    monkeypatch.setattr(jenkins_builds, "JenkinsClient", client_cls)
    return instance
