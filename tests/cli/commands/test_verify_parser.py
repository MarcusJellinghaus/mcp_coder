"""Tests for the verify subparser in parsers.py."""

from mcp_coder.cli.main import create_parser


class TestVerifyParser:
    def test_verify_parser_exists(self) -> None:
        """verify subcommand is registered."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.command == "verify"

    def test_check_models_flag_default_false(self) -> None:
        """--check-models defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.check_models is False

    def test_check_models_flag_set(self) -> None:
        """--check-models sets attribute to True."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--check-models"])
        assert args.check_models is True
