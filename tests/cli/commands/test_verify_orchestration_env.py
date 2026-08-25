"""Tests for verify orchestrator env-var and prompt wiring (steps 3, 4 & 13).

Split out of ``test_verify_orchestration.py``: the retired-env-var warning, the
mistyped-``[llm.langchain]`` regression and the ``project_dir=`` forwarding of
the test prompt all drive ``execute_verify`` through environment/config inputs
rather than through its section wiring.
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _assert_value_at_column,
    _claude_ok,
    _expected_value_column,
    _github_ok_default,
    _langchain_ok,
    _make_args,
    _minimal_llm_response,
    _mlflow_not_installed,
    _mlflow_ok,
)


class TestRetiredEnvVarWarning:
    """Tests for the retired-env-var warning (step 3).

    ``MCP_CODER_LLM_LANGCHAIN_ENDPOINT`` is no longer read by anything after
    the ``endpoint`` -> ``base_url`` rename, and unknown-key detection only
    scans config sections, so ``verify`` calls it out explicitly. The check is
    outside both provider gates and prints only.
    """

    _OLD = "MCP_CODER_LLM_LANGCHAIN_ENDPOINT"
    _NEW = "MCP_CODER_LLM_LANGCHAIN_BASE_URL"

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_warning_shown_when_langchain_active(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Warning appears for langchain users and leaves the exit code alone."""
        monkeypatch.setenv(self._OLD, "https://relay.example/v1")
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_ok()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())
        output = capsys.readouterr().out

        assert self._OLD in output
        assert "retired env var is set and ignored" in output
        assert self._NEW in output
        assert result == 0

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_warning_shown_when_claude_active(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """The check is outside both provider gates, so claude users see it too."""
        monkeypatch.setenv(self._OLD, "https://relay.example/v1")
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())
        output = capsys.readouterr().out

        assert self._OLD in output
        assert "retired env var is set and ignored" in output
        assert self._NEW in output
        assert result == 0

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_nothing_printed_when_env_var_unset(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """No row at all when the retired variable is not exported."""
        monkeypatch.delenv(self._OLD, raising=False)
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        result = execute_verify(_make_args())
        output = capsys.readouterr().out

        assert self._OLD not in output
        assert "retired env var" not in output
        assert result == 0

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_empty_env_var_is_not_flagged(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """An exported-but-empty value carries no redirect, so it stays quiet."""
        monkeypatch.setenv(self._OLD, "")
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args())
        output = capsys.readouterr().out

        assert "retired env var" not in output

    def test_retired_table_maps_endpoint_to_base_url(self) -> None:
        """The table drives the message, so future retirements have a home."""
        from mcp_coder.cli.commands.verify_sections import _RETIRED_ENV_VARS

        assert _RETIRED_ENV_VARS[self._OLD] == self._NEW

    def test_row_keeps_the_value_column_aligned(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The label is wider than _LABEL_WIDTH; the row widens to match."""
        from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS
        from mcp_coder.cli.commands.verify_sections import (
            _print_retired_env_var_warning,
        )

        with patch.dict("os.environ", {self._OLD: "https://relay.example/v1"}):
            _print_retired_env_var_warning(STATUS_SYMBOLS)
        line = capsys.readouterr().out.rstrip("\n")

        assert line.startswith(f"  {self._OLD} ")
        _assert_value_at_column(
            line, _expected_value_column(2, label_width=len(self._OLD))
        )


class TestVerifySurvivesMistypedLangchainConfig:
    """Regression: a mistyped [llm.langchain] value must not crash verify (step 4).

    ``_load_langchain_config()`` runs on every ``verify`` — for claude users
    too, via the backend-readiness warning — so the ``ValueError`` that
    ``get_config_values`` raises on a schema type mismatch has to be swallowed.
    The CONFIG section already reports the mismatch; ``verify`` should exit 1
    from *that*, not from a traceback.
    """

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_int_model_exits_1_from_config_error_without_traceback(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """`[llm.langchain] model = 123` completes the run and exits 1."""
        for env_var in (
            "MCP_CODER_LLM_LANGCHAIN_BACKEND",
            "MCP_CODER_LLM_LANGCHAIN_MODEL",
            "MCP_CODER_LLM_LANGCHAIN_BASE_URL",
            "MCP_CODER_LLM_LANGCHAIN_API_VERSION",
        ):
            monkeypatch.delenv(env_var, raising=False)
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        with (
            patch(
                "mcp_coder.utils.user_config.load_config",
                return_value={"llm": {"langchain": {"model": 123}}},
            ),
            patch(
                f"{_VERIFY}.verify_config",
                return_value={
                    "entries": [
                        {
                            "label": "[llm.langchain]",
                            "status": "error",
                            "value": "model expected str, got int ('123')",
                        }
                    ],
                    "has_error": True,
                },
            ),
        ):
            result = execute_verify(_make_args())

        output = capsys.readouterr().out
        assert result == 1
        assert "expected str, got int" in output
        assert "Traceback" not in output


class TestVerifyTestPromptCarriesProjectDir:
    """Step 13: the verify test prompt carries the real message shape.

    Without ``project_dir=``, ``prompt_llm`` never calls ``load_prompts``, so the
    provider is handed ``system_prompt=None, project_prompt=None`` and the test
    prompt exercises a message shape no real run ever sends.
    """

    @pytest.fixture(autouse=True)
    def _mock_resolve_mcp(self) -> Any:
        """Default: resolve_mcp_config_path returns None (no MCP config)."""
        with patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None):
            yield

    @pytest.fixture(autouse=True)
    def _mock_github(self) -> Any:
        """Default: verify_github returns neutral ok result."""
        with patch(f"{_VERIFY}.verify_github", return_value=_github_ok_default()):
            yield

    @staticmethod
    def _test_prompt_kwargs(mock_prompt_llm: MagicMock) -> dict[str, Any]:
        """Return the kwargs of the single "Reply with OK" call."""
        calls = [
            c for c in mock_prompt_llm.call_args_list if c[0][0] == "Reply with OK"
        ]
        assert len(calls) == 1
        return dict(calls[0][1])

    @patch(f"{_VERIFY}.find_claude_executable", return_value=None)
    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_LC_VERIFY}.verify_langchain")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_langchain_active_forwards_project_dir(
        self,
        mock_provider: MagicMock,
        mock_lc: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        mock_find_claude: MagicMock,
        tmp_path: Path,
    ) -> None:
        """langchain active: the test prompt is given project_dir."""
        mock_provider.return_value = ("langchain", "config.toml")
        mock_lc.return_value = _langchain_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args(project_dir=str(tmp_path)))

        kwargs = self._test_prompt_kwargs(mock_prompt_llm)
        assert kwargs["project_dir"] == str(tmp_path.resolve())

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_claude_active_forwards_project_dir(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        tmp_path: Path,
    ) -> None:
        """claude active: the same kwarg, no per-provider conditional."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        execute_verify(_make_args(project_dir=str(tmp_path)))

        kwargs = self._test_prompt_kwargs(mock_prompt_llm)
        assert kwargs["project_dir"] == str(tmp_path.resolve())

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_explicit_project_dir_is_resolved_not_cwd(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        tmp_path: Path,
    ) -> None:
        """--project-dir wins over CWD and arrives resolved."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.return_value = _minimal_llm_response()

        target = tmp_path / "proj"
        target.mkdir()
        unresolved = str(target / ".." / "proj")

        execute_verify(_make_args(project_dir=unresolved))

        kwargs = self._test_prompt_kwargs(mock_prompt_llm)
        assert kwargs["project_dir"] == str(target.resolve())
        assert kwargs["project_dir"] != str(Path.cwd())

    @patch(f"{_VERIFY}.log_to_mlflow", create=True)
    @patch(f"{_VERIFY}.prompt_llm")
    @patch(f"{_VERIFY}.verify_mlflow")
    @patch(f"{_VERIFY}.verify_claude")
    @patch(f"{_VERIFY}.resolve_llm_method")
    def test_prompt_failure_still_exits_1_with_classified_message(
        self,
        mock_provider: MagicMock,
        mock_claude: MagicMock,
        mock_mlflow: MagicMock,
        mock_prompt_llm: MagicMock,
        _mock_log_mlflow: MagicMock,
        capsys: pytest.CaptureFixture[str],
        tmp_path: Path,
    ) -> None:
        """Regression: a failing test prompt is still classified and exits 1."""
        mock_provider.return_value = ("claude", "default")
        mock_claude.return_value = _claude_ok()
        mock_mlflow.return_value = _mlflow_not_installed()
        mock_prompt_llm.side_effect = RuntimeError("boom")

        result = execute_verify(_make_args(project_dir=str(tmp_path)))
        output = capsys.readouterr().out

        assert result == 1
        assert "FAILED (RuntimeError: boom)" in output
