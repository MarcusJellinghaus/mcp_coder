"""Tests for the JENKINS / JENKINS JOBS verify sections.

``verify_jenkins()`` is patched out of every other CLI command test by the
autouse ``_neutral_jenkins_verify`` fixture; this module imports it directly
from ``mcp_coder.cli.commands.verify_jenkins`` and is therefore unaffected.

Probe patching note: ``verify_jenkins.py`` imports ``probe`` by name, while
``diagnose_403`` / ``diagnose_404`` resolve it through the ``diagnostics``
module globals. Both bindings must be replaced for a hermetic test, which is
what ``_patch_probes`` does.
"""

from contextlib import ExitStack, contextmanager
from dataclasses import replace
from typing import Any, Callable, Generator, Optional
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.verify import execute_verify
from mcp_coder.cli.commands.verify_formatting import STATUS_SYMBOLS, _format_section
from mcp_coder.cli.commands.verify_jenkins import verify_jenkins
from mcp_coder.utils.jenkins_operations.diagnostics import ProbeResult

from .conftest import (
    _LC_VERIFY,
    _VERIFY,
    _claude_ok,
    _make_args,
    _mcp_servers_ok,
    _minimal_llm_response,
    _mlflow_not_installed,
)

_JENKINS = "mcp_coder.cli.commands.verify_jenkins"
_DIAGNOSTICS = "mcp_coder.utils.jenkins_operations.diagnostics"

_BASE_URL = "https://jenkins:8080"
_DOCS = "docs/repository-setup/jenkins.md"

_UNPATCHED = object()
"""Sentinel: leave ``get_jenkins_config`` in place so the real env path runs."""


def _full_creds() -> dict[str, Optional[str]]:
    """Return a complete, valid credential set."""
    return {
        "server_url": _BASE_URL,
        "username": "job_manager",
        "api_token": "secret-token",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _repos(**paths: str) -> dict[str, Any]:
    """Build a ``load_config()`` payload with the given repo -> job path map."""
    return {
        "coordinator": {
            "repos": {name: {"executor_job_path": path} for name, path in paths.items()}
        }
    }


@contextmanager
def _patch_probes(
    responder: Callable[[str], ProbeResult],
) -> Generator[MagicMock, None, None]:
    """Replace both ``probe`` bindings with a path-keyed fake.

    Args:
        responder: Maps the probed URL path (e.g. "/api/json") to a ProbeResult.

    Yields:
        The mock installed at the ``verify_jenkins`` import site.
    """

    def fake_probe(_session: Any, base_url: str, path: str) -> ProbeResult:
        return replace(responder(path), url=f"{base_url}{path}")

    with ExitStack() as stack:
        mock = stack.enter_context(patch(f"{_JENKINS}.probe", side_effect=fake_probe))
        stack.enter_context(patch(f"{_DIAGNOSTICS}.probe", side_effect=fake_probe))
        yield mock


def _result(status: Optional[int], error_text: Optional[str] = None) -> ProbeResult:
    """Build a ProbeResult; the URL is filled in by ``_patch_probes``."""
    return ProbeResult(status=status, url="", error_text=error_text)


@contextmanager
def _patch_env(
    creds: Any = None,
    config: Optional[dict[str, Any]] = None,
    creds_error: Optional[Exception] = None,
    config_error: Optional[Exception] = None,
) -> Generator[dict[str, MagicMock], None, None]:
    """Patch the config sources and JenkinsClient used by ``verify_jenkins``.

    Args:
        creds: Credential dict for ``get_jenkins_config``; None uses a full
            valid set, ``_UNPATCHED`` leaves the real function in place so the
            env-var override path runs.
        config: Payload for ``load_config``; defaults to an empty config.
        creds_error: Raised by ``get_jenkins_config`` instead of returning.
        config_error: Raised by ``load_config`` instead of returning.

    Yields:
        The installed mocks, keyed by patched name.
    """
    client = MagicMock()
    client.base_url = _BASE_URL
    with ExitStack() as stack:
        mocks: dict[str, MagicMock] = {
            "JenkinsClient": stack.enter_context(
                patch(f"{_JENKINS}.JenkinsClient", return_value=client)
            ),
            "load_config": stack.enter_context(
                patch(
                    f"{_JENKINS}.load_config",
                    side_effect=config_error,
                    return_value=config if config is not None else {},
                )
            ),
        }
        if creds is not _UNPATCHED:
            mocks["get_jenkins_config"] = stack.enter_context(
                patch(
                    f"{_JENKINS}.get_jenkins_config",
                    side_effect=creds_error,
                    return_value=creds if creds is not None else _full_creds(),
                )
            )
        yield mocks


# ---------------------------------------------------------------------------
# Credential resolution / skip behaviour
# ---------------------------------------------------------------------------


class TestCredentialResolution:
    """When and how the section decides it has something to probe."""

    def test_unconfigured_returns_empty_and_builds_no_client(self) -> None:
        """No [jenkins] section -> both dicts empty, no client constructed."""
        creds: dict[str, Optional[str]] = {
            "server_url": None,
            "username": None,
            "api_token": None,
        }
        with _patch_env(creds=creds) as mocks:
            assert verify_jenkins() == ({}, {})
        mocks["JenkinsClient"].assert_not_called()

    def test_partial_config_returns_empty(self) -> None:
        """server_url alone is not enough to probe -> skipped."""
        creds: dict[str, Optional[str]] = {
            "server_url": _BASE_URL,
            "username": None,
            "api_token": None,
        }
        with _patch_env(creds=creds) as mocks:
            assert verify_jenkins() == ({}, {})
        mocks["JenkinsClient"].assert_not_called()

    def test_malformed_config_value_error_contained(self) -> None:
        """Malformed TOML surfaces in the CONFIG section, not as a crash here."""
        with _patch_env(creds_error=ValueError("bad TOML")):
            assert verify_jenkins() == ({}, {})

    def test_blank_credential_values_are_treated_as_unconfigured(self) -> None:
        """Whitespace-only fields are not configuration -> skipped, no client."""
        creds: dict[str, Optional[str]] = {
            "server_url": "   ",
            "username": "job_manager",
            "api_token": "secret-token",
        }
        with _patch_env(creds=creds) as mocks:
            assert verify_jenkins() == ({}, {})
        mocks["JenkinsClient"].assert_not_called()

    def test_client_construction_failure_is_reported_not_raised(self) -> None:
        """Credentials present but unusable -> a failed Server row, never a crash."""
        with _patch_env() as mocks:
            mocks["JenkinsClient"].side_effect = ValueError("bad server_url")
            server_result, jobs_result = verify_jenkins()

        assert server_result["server"]["ok"] is False
        assert server_result["authentication"]["ok"] is None
        assert server_result["overall_ok"] is False
        assert jobs_result == {}

    def test_scheme_less_server_url_renders_failed_row(self) -> None:
        """A URL with no scheme is reported, not allowed to abort the command.

        Regression guard against catching ValueError alone:
        "jenkins.example.com" leaves urllib3 with no scheme, so requests'
        ``Session.mount(None, ...)`` raises ``TypeError`` inside
        ``JenkinsClient.__init__``. Uncaught, that aborts the whole
        ``mcp-coder verify`` run before any other section prints. The real
        JenkinsClient is used here on purpose - a mock cannot reproduce it.
        """
        creds = {
            "server_url": "jenkins.example.com",
            "username": "job_manager",
            "api_token": "secret-token",
        }
        with patch(f"{_JENKINS}.get_jenkins_config", return_value=creds):
            server_result, jobs_result = verify_jenkins()

        server_row = server_result["server"]
        assert server_row["ok"] is False
        assert server_row["value"] == "jenkins.example.com"
        assert "scheme" in server_row["error"]
        assert server_row["install_hint"] == _DOCS
        assert server_result["authentication"]["ok"] is None
        assert server_result["overall_read"]["ok"] is None
        assert server_result["overall_ok"] is False
        assert jobs_result == {}

    def test_credentials_come_from_env_overrides(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env-var-only setups must be probed, with the env values.

        Regression guard for sourcing credentials from ``load_config()``, which
        reads the TOML file only: that would skip this setup entirely, or probe a
        different server than the coordinator dispatches to.
        """
        monkeypatch.setenv("JENKINS_URL", "https://env-jenkins:8080")
        monkeypatch.setenv("JENKINS_USER", "env_user")
        monkeypatch.setenv("JENKINS_TOKEN", "env-token")

        with (
            _patch_env(creds=_UNPATCHED) as mocks,
            _patch_probes(lambda _p: _result(200)),
        ):
            server_result, _jobs_result = verify_jenkins()

        assert server_result["overall_ok"] is True
        mocks["JenkinsClient"].assert_called_once_with(
            "https://env-jenkins:8080", "env_user", "env-token"
        )


# ---------------------------------------------------------------------------
# Server section
# ---------------------------------------------------------------------------


class TestServerSection:
    """The three JENKINS rows derived from the /api/json probe."""

    def test_all_ok_two_repos(self) -> None:
        """Everything reachable -> three server rows, two job rows, both ok."""
        config = _repos(**{"my-repo": "Windows-Agents/Executor", "other": "Build"})
        with _patch_env(config=config), _patch_probes(lambda _p: _result(200)):
            server_result, jobs_result = verify_jenkins()

        assert list(server_result) == [
            "server",
            "authentication",
            "overall_read",
            "overall_ok",
        ]
        assert server_result["overall_ok"] is True
        assert server_result["authentication"]["value"].startswith("job_manager")
        assert jobs_result["overall_ok"] is True
        assert set(jobs_result) == {"my-repo", "other", "overall_ok"}

    def test_403_reports_overall_read_and_skips_jobs(self) -> None:
        """403 on /api/json -> Overall/Read fails with the full diagnosis."""
        config = _repos(**{"my-repo": "Windows-Agents/Executor"})
        with _patch_env(config=config), _patch_probes(lambda _p: _result(403)):
            server_result, jobs_result = verify_jenkins()

        assert server_result["server"]["ok"] is True
        assert server_result["authentication"]["ok"] is True
        overall_read = server_result["overall_read"]
        assert overall_read["ok"] is False
        assert "Overall/Read" in overall_read["error"]
        assert _DOCS in overall_read["error"]
        assert server_result["overall_ok"] is False
        # Every job row would repeat the same upstream cause.
        assert jobs_result == {}

    def test_401_fails_authentication_only(self) -> None:
        """401 -> authentication fails; Overall/Read is unknown, not a hard fail."""
        with _patch_env(), _patch_probes(lambda _p: _result(401, "bad credentials")):
            server_result, jobs_result = verify_jenkins()

        assert server_result["server"]["ok"] is True
        assert server_result["authentication"]["ok"] is False
        assert server_result["overall_read"]["ok"] is None
        assert server_result["overall_ok"] is False
        assert jobs_result == {}

    def test_transport_failure_fails_server_row(self) -> None:
        """A probe that never completed -> server row carries the transport error."""
        message = "HTTPSConnectionPool: Name or service not known"
        with _patch_env(), _patch_probes(lambda _p: _result(None, message)):
            server_result, jobs_result = verify_jenkins()

        assert server_result["server"]["ok"] is False
        assert message in server_result["server"]["error"]
        assert server_result["authentication"]["ok"] is None
        assert server_result["overall_read"]["ok"] is None
        assert jobs_result == {}

    def test_unexpected_status_fails_server_row(self) -> None:
        """An unmodelled status is reported rather than silently passing."""
        with _patch_env(), _patch_probes(lambda _p: _result(500)):
            server_result, _jobs_result = verify_jenkins()

        assert server_result["server"]["ok"] is False
        assert "500" in server_result["server"]["error"]
        assert server_result["overall_ok"] is False


# ---------------------------------------------------------------------------
# Jobs section
# ---------------------------------------------------------------------------


class TestJobsSection:
    """Per-repo Job/Read rows."""

    def test_job_404_names_both_segments(self) -> None:
        """A 404 job row carries the ancestor-walk diagnosis and the docs hint."""

        def responder(path: str) -> ProbeResult:
            if path == "/api/json":
                return _result(200)
            if path == "/job/Windows-Agents/api/json":
                return _result(200)
            return _result(404)

        config = _repos(**{"my-repo": "Windows-Agents/Executor"})
        with _patch_env(config=config), _patch_probes(responder):
            server_result, jobs_result = verify_jenkins()

        assert server_result["overall_ok"] is True
        row = jobs_result["my-repo"]
        assert row["ok"] is False
        assert row["value"] == "Windows-Agents/Executor"
        assert "Windows-Agents" in row["error"]
        assert "Executor" in row["error"]
        assert row["install_hint"] == _DOCS
        assert jobs_result["overall_ok"] is False

    def test_job_403_uses_diagnosis(self) -> None:
        """A 403 on the job probe reports the permission diagnosis."""

        def responder(path: str) -> ProbeResult:
            return _result(200) if path == "/api/json" else _result(403)

        config = _repos(**{"my-repo": "Windows-Agents/Executor"})
        with _patch_env(config=config), _patch_probes(responder):
            _server_result, jobs_result = verify_jenkins()

        row = jobs_result["my-repo"]
        assert row["ok"] is False
        assert _DOCS in row["error"]
        assert row["install_hint"] == _DOCS

    def test_no_repos_configured_skips_jobs_section(self) -> None:
        """Server reachable but no coordinator repos -> jobs section skipped."""
        with _patch_env(config={}), _patch_probes(lambda _p: _result(200)):
            server_result, jobs_result = verify_jenkins()

        assert server_result["overall_ok"] is True
        assert jobs_result == {}

    def test_repo_without_job_path_is_skipped(self) -> None:
        """A repo missing executor_job_path is skipped, not crashed on."""
        config = {
            "coordinator": {
                "repos": {
                    "no-path": {"github_repository_url": "https://example.invalid"},
                    "my-repo": {"executor_job_path": "Build"},
                }
            }
        }
        with _patch_env(config=config), _patch_probes(lambda _p: _result(200)):
            _server_result, jobs_result = verify_jenkins()

        assert set(jobs_result) == {"my-repo", "overall_ok"}

    def test_load_config_value_error_contained(self) -> None:
        """Malformed TOML while credentials resolve -> server section still renders."""
        with (
            _patch_env(config_error=ValueError("bad TOML")),
            _patch_probes(lambda _p: _result(200)),
        ):
            server_result, jobs_result = verify_jenkins()

        assert server_result["overall_ok"] is True
        assert jobs_result == {}


# ---------------------------------------------------------------------------
# Rendering and orchestration
# ---------------------------------------------------------------------------


class TestJenkinsRendering:
    """The docs pointer must survive _format_section."""

    def test_failed_job_row_renders_error_and_docs_pointer(self) -> None:
        jobs_result: dict[str, Any] = {
            "my-repo": {
                "ok": False,
                "value": "Windows-Agents/Executor",
                "error": "404 on 'Windows-Agents/Executor' - not readable",
                "install_hint": _DOCS,
            },
            "overall_ok": False,
        }
        rendered = _format_section("JENKINS JOBS", jobs_result, STATUS_SYMBOLS)
        lines = rendered.splitlines()

        row_index = next(i for i, line in enumerate(lines) if "my-repo" in line)
        assert "[ERR]" in lines[row_index]
        assert "(404 on 'Windows-Agents/Executor' - not readable)" in lines[row_index]
        assert lines[row_index + 1].strip() == f"-> {_DOCS}"

    def test_server_labels_are_mapped(self) -> None:
        server_result: dict[str, Any] = {
            "server": {"ok": True, "value": f"{_BASE_URL} reachable"},
            "authentication": {"ok": True, "value": "job_manager (API token valid)"},
            "overall_read": {"ok": True, "value": "granted"},
            "overall_ok": True,
        }
        rendered = _format_section("JENKINS", server_result, STATUS_SYMBOLS)

        assert "Server" in rendered
        assert "Authentication" in rendered
        assert "Overall/Read" in rendered


class TestJenkinsOrchestration:
    """execute_verify prints JENKINS between GITHUB and BASIC VERIFICATION."""

    @pytest.fixture(autouse=True)
    def _live_jenkins_verify(self) -> Generator[None, None, None]:
        """Override the hermetic autouse fixture with a configured result."""
        server_result: dict[str, Any] = {
            "server": {"ok": True, "value": f"{_BASE_URL} reachable"},
            "overall_ok": True,
        }
        jobs_result: dict[str, Any] = {
            "my-repo": {"ok": True, "value": "Build"},
            "overall_ok": True,
        }
        with patch(
            f"{_VERIFY}.verify_jenkins", return_value=(server_result, jobs_result)
        ):
            yield

    def test_sections_print_between_github_and_basic_verification(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
            patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
            patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
            patch(f"{_VERIFY}.prepare_llm_environment", return_value={}),
            patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
            patch(f"{_VERIFY}.log_to_mlflow", create=True),
            patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
            patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_servers_ok()),
        ):
            exit_code = execute_verify(_make_args())

        lines = capsys.readouterr().out.splitlines()

        def index(prefix: str) -> int:
            return next(i for i, line in enumerate(lines) if line.startswith(prefix))

        assert (
            index("=== GITHUB ")
            < index("=== JENKINS ")
            < index("=== JENKINS JOBS ")
            < index("=== BASIC VERIFICATION ")
        )
        assert exit_code == 0


def _run_verify_with_jenkins(
    server_result: dict[str, Any], jobs_result: dict[str, Any]
) -> int:
    """Run ``execute_verify`` with every non-Jenkins check forced green.

    Args:
        server_result: JENKINS section dict returned by ``verify_jenkins``.
        jobs_result: JENKINS JOBS section dict returned by ``verify_jenkins``.

    Returns:
        The exit code ``execute_verify`` produced.
    """
    with (
        patch(f"{_VERIFY}.verify_jenkins", return_value=(server_result, jobs_result)),
        patch(f"{_VERIFY}.resolve_llm_method", return_value=("claude", "default")),
        patch(f"{_VERIFY}.verify_claude", return_value=_claude_ok()),
        patch(f"{_VERIFY}.verify_mlflow", return_value=_mlflow_not_installed()),
        patch(f"{_VERIFY}.prepare_llm_environment", return_value={}),
        patch(f"{_VERIFY}.prompt_llm", return_value=_minimal_llm_response()),
        patch(f"{_VERIFY}.log_to_mlflow", create=True),
        patch(f"{_VERIFY}.resolve_mcp_config_path", return_value=None),
        patch(f"{_LC_VERIFY}.verify_mcp_servers", return_value=_mcp_servers_ok()),
    ):
        return execute_verify(_make_args())


def _server_section(ok: bool) -> dict[str, Any]:
    """Build a JENKINS section dict that passes or fails."""
    if ok:
        return {
            "server": {"ok": True, "value": f"{_BASE_URL} reachable"},
            "overall_ok": True,
        }
    return {
        "server": {
            "ok": False,
            "value": _BASE_URL,
            "error": "unreachable",
            "install_hint": _DOCS,
        },
        "overall_ok": False,
    }


def _jobs_section(ok: bool) -> dict[str, Any]:
    """Build a JENKINS JOBS section dict that passes or fails."""
    if ok:
        return {"my-repo": {"ok": True, "value": "Build"}, "overall_ok": True}
    return {
        "my-repo": {
            "ok": False,
            "value": "Build",
            "error": "404 on 'Build'",
            "install_hint": _DOCS,
        },
        "overall_ok": False,
    }


class TestJenkinsExitCodeWiring:
    """A failing Jenkins section must make ``mcp-coder verify`` exit 1.

    ``test_verify_exit_codes.py`` calls ``_compute_exit_code`` directly, which
    cannot see the ``jenkins_ok = server_overall_ok and jobs_overall_ok``
    composition in ``verify.py`` - dropping either half of that expression, or
    the ``jenkins_ok=`` argument itself, leaves those unit tests green.
    """

    @pytest.mark.parametrize(
        "server_ok,jobs_ok,expected",
        [
            pytest.param(True, True, 0, id="both-pass"),
            pytest.param(False, None, 1, id="server-row-fails"),
            pytest.param(True, False, 1, id="job-row-fails"),
        ],
    )
    def test_exit_code(
        self, server_ok: bool, jobs_ok: Optional[bool], expected: int
    ) -> None:
        """A failed row in either section propagates to the process exit code."""
        # jobs_ok None mirrors verify_jenkins(): no job rows when the server fails.
        jobs_result = {} if jobs_ok is None else _jobs_section(jobs_ok)

        assert _run_verify_with_jenkins(_server_section(server_ok), jobs_result) == (
            expected
        )

    def test_unconfigured_jenkins_is_exit_neutral(self) -> None:
        """No [jenkins] section -> no rows, no effect on the exit code."""
        assert _run_verify_with_jenkins({}, {}) == 0
