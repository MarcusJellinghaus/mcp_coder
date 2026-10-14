"""Tests for shared test helpers in tests/cli/commands/conftest.py."""

import argparse

import pytest

from tests.cli.commands.conftest import unavailable_command_stub


def test_unavailable_command_stub_raises() -> None:
    with pytest.raises(NotImplementedError):
        unavailable_command_stub(argparse.Namespace())
