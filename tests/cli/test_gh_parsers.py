from __future__ import annotations

import argparse

from mcp_coder.cli.main import create_parser


class TestDefineLabelsParser:
    """Tests for define-labels CLI flags."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_default_flags_are_false(self) -> None:
        """All optional flags default to False/None."""
        args = self._parse("gh-tool", "define-labels")
        assert args.init is False
        assert args.validate is False
        assert args.config is None
        assert args.generate_github_actions is False
        assert args.all is False

    def test_init_flag(self) -> None:
        """--init sets args.init=True."""
        args = self._parse("gh-tool", "define-labels", "--init")
        assert args.init is True

    def test_validate_flag(self) -> None:
        """--validate sets args.validate=True."""
        args = self._parse("gh-tool", "define-labels", "--validate")
        assert args.validate is True

    def test_config_flag(self) -> None:
        """--config path/to/config.json sets args.config."""
        args = self._parse(
            "gh-tool", "define-labels", "--config", "path/to/config.json"
        )
        assert args.config == "path/to/config.json"

    def test_generate_github_actions_flag(self) -> None:
        """--generate-github-actions sets args.generate_github_actions=True."""
        args = self._parse("gh-tool", "define-labels", "--generate-github-actions")
        assert args.generate_github_actions is True

    def test_all_flag(self) -> None:
        """--all sets args.all=True."""
        args = self._parse("gh-tool", "define-labels", "--all")
        assert args.all is True

    def test_combined_flags(self) -> None:
        """Multiple flags can be combined."""
        args = self._parse(
            "gh-tool",
            "define-labels",
            "--init",
            "--validate",
            "--config",
            "my.json",
            "--generate-github-actions",
            "--all",
        )
        assert args.init is True
        assert args.validate is True
        assert args.config == "my.json"
        assert args.generate_github_actions is True
        assert args.all is True
