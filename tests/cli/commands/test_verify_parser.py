"""Tests for the verify subparser in parsers.py."""

from mcp_coder.cli.main import create_parser


class TestVerifyParser:
    """Tests for the verify subparser registration and arguments."""

    def test_verify_parser_exists(self) -> None:
        """Verify subcommand is registered."""
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

    def test_project_dir_default_none(self) -> None:
        """--project-dir defaults to None when not provided."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.project_dir is None

    def test_project_dir_accepted(self) -> None:
        """--project-dir is accepted with a value."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--project-dir", "/some/path"])
        assert args.project_dir == "/some/path"

    def test_list_mcp_tools_flag_default_false(self) -> None:
        """--list-mcp-tools defaults to False."""
        parser = create_parser()
        args = parser.parse_args(["verify"])
        assert args.list_mcp_tools is False

    def test_list_mcp_tools_flag_set(self) -> None:
        """--list-mcp-tools sets attribute to True."""
        parser = create_parser()
        args = parser.parse_args(["verify", "--list-mcp-tools"])
        assert args.list_mcp_tools is True
