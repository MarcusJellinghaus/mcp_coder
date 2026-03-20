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

    def test_llm_method_default_none(self) -> None:
        """--llm-method defaults to None when not provided."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.llm_method is None

    def test_llm_method_claude(self) -> None:
        """--llm-method claude is accepted."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--llm-method", "claude"])
        assert args.llm_method == "claude"

    def test_llm_method_langchain(self) -> None:
        """--llm-method langchain is accepted."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--llm-method", "langchain"])
        assert args.llm_method == "langchain"
