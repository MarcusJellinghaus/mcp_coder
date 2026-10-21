"""Unit tests for mcp_coder.install._env — InstallConfig.from_args.

The installer no longer owns a parser (``mcp-coder install`` is the only
entry point, defined in ``cli/parsers.py``), so these tests build the
Namespace the parser would produce with the shared ``_namespace`` helper
(see ``conftest.py``) and call ``InstallConfig.from_args`` directly. The
defaults that helper mirrors are pinned in ``tests/cli/commands/test_install``.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from mcp_coder.install import InstallConfig

from .conftest import namespace as _namespace

MALFORMED_TOML = "this is not valid toml {{{"


def _write_pyproject(tmp_path: Path, body: str) -> None:
    """Write a minimal pyproject.toml with the given trailing body."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "test-project"\nversion = "0.1.0"\n' + body,
        encoding="utf-8",
    )


class TestExtrasResolution:
    """Where the effective extras string comes from."""

    def test_declared_extras_are_used(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path, '\n[tool.mcp-coder.install]\nextras = "dev,mlflow"\n'
        )
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.extras == "dev,mlflow"

    def test_missing_section_falls_back_to_dev(self, tmp_path: Path) -> None:
        _write_pyproject(tmp_path, "")
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.extras == "dev"

    def test_missing_pyproject_falls_back_to_dev(self, tmp_path: Path) -> None:
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.extras == "dev"

    def test_explicit_empty_extras_means_no_extras(self, tmp_path: Path) -> None:
        _write_pyproject(tmp_path, '\n[tool.mcp-coder.install]\nextras = "dev"\n')
        config = InstallConfig.from_args(_namespace(target=tmp_path, extras=""))
        assert config.extras == ""

    def test_explicit_extras_override_the_declaration(self, tmp_path: Path) -> None:
        _write_pyproject(tmp_path, '\n[tool.mcp-coder.install]\nextras = "dev"\n')
        config = InstallConfig.from_args(_namespace(target=tmp_path, extras="mlflow"))
        assert config.extras == "mlflow"


class TestStrictTomlRead:
    """The extras read is strict and unconditional."""

    def test_malformed_pyproject_raises_naming_the_file(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        with pytest.raises(ValueError) as exc_info:
            InstallConfig.from_args(_namespace(target=tmp_path))
        assert "pyproject.toml" in str(exc_info.value)

    def test_malformed_pyproject_raises_even_with_explicit_extras(
        self, tmp_path: Path
    ) -> None:
        """An explicit --extras overrides the value but never skips the read."""
        (tmp_path / "pyproject.toml").write_text(MALFORMED_TOML, encoding="utf-8")
        with pytest.raises(ValueError) as exc_info:
            InstallConfig.from_args(_namespace(target=tmp_path, extras="mlflow"))
        assert "pyproject.toml" in str(exc_info.value)


class TestPostInstallChecksResolution:
    """The post-install checks are read strictly from the pyproject.toml."""

    def test_declared_checks_are_used(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path,
            '\n[tool.mcp-coder.install]\npost_install_checks = [["a", "--version"]]\n',
        )
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.post_install_checks == (("a", "--version"),)

    def test_missing_key_means_no_checks(self, tmp_path: Path) -> None:
        _write_pyproject(tmp_path, '\n[tool.mcp-coder.install]\nextras = "dev"\n')
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.post_install_checks == ()

    def test_malformed_checks_raise(self, tmp_path: Path) -> None:
        _write_pyproject(
            tmp_path, "\n[tool.mcp-coder.install]\npost_install_checks = [[]]\n"
        )
        with pytest.raises(ValueError, match="post_install_checks"):
            InstallConfig.from_args(_namespace(target=tmp_path))


class TestLocalPathResolution:
    """--local-path defaulting and the --source local requirement."""

    def test_local_path_defaults_to_target(self, tmp_path: Path) -> None:
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        assert config.local_path == tmp_path.resolve()
        assert config.target == tmp_path.resolve()

    def test_explicit_local_path_wins(self, tmp_path: Path) -> None:
        checkout = tmp_path / "checkout"
        checkout.mkdir()
        _write_pyproject(checkout, '\n[tool.mcp-coder.install]\nextras = "mlflow"\n')
        config = InstallConfig.from_args(
            _namespace(target=tmp_path, local_path=checkout)
        )
        assert config.local_path == checkout.resolve()
        # The extras policy is read from the checkout, not the target.
        assert config.extras == "mlflow"

    def test_source_local_without_local_path_errors(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError) as exc_info:
            InstallConfig.from_args(_namespace(target=tmp_path, source="local"))
        assert "--local-path" in str(exc_info.value)


class TestFrozenConfig:
    """InstallConfig is frozen."""

    def test_attribute_assignment_is_rejected(self, tmp_path: Path) -> None:
        config = InstallConfig.from_args(_namespace(target=tmp_path))
        with pytest.raises(dataclasses.FrozenInstanceError):
            config.extras = "mlflow"  # type: ignore[misc]


class TestUseSyncTargetGuard:
    """--use-sync requires target == --local-path (uv sync writes <cwd>/.venv)."""

    def test_mismatched_paths_error(self, tmp_path: Path) -> None:
        other = tmp_path / "other"
        other.mkdir()
        with pytest.raises(ValueError) as exc_info:
            InstallConfig.from_args(
                _namespace(
                    target=tmp_path,
                    source="local",
                    local_path=other,
                    use_sync=True,
                )
            )
        message = str(exc_info.value)
        assert "--use-sync" in message
        assert "local-path" in message

    def test_matching_paths_pass_the_guard(self, tmp_path: Path) -> None:
        config = InstallConfig.from_args(
            _namespace(
                target=tmp_path,
                source="local",
                local_path=tmp_path,
                use_sync=True,
            )
        )
        assert config.use_sync is True
        assert config.local_path == config.target
