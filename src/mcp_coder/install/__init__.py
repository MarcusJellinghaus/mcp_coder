"""Install mcp-coder (and/or related projects) into a target environment.

Backs the ``mcp-coder install`` subcommand.

Scope: Python packages only. Files that need to be staged alongside the
install (e.g. ``.mcp.json``, ``.claude/``) are the caller's responsibility.

Install sources: ``--source git`` (default) fetches from
``git+https://...mcp_coder.git@<ref>``, with sibling MCP packages
(mcp-tools-py, mcp-workspace, mcp-coder-utils) coming from GitHub HEAD via
``[tool.mcp-coder.install-from-github]``. ``--source pypi`` installs plain
``mcp-coder`` from PyPI and skips the GitHub override step. ``--source local``
does an editable install of a local checkout (``-e <path>[extras]``); with
``--use-sync`` it switches to a uv.lock-honoring flow: ``uv venv`` ->
``uv sync --extra <extras>`` -> GitHub overrides ->
``uv pip install -e . --no-deps``.

The run is idempotent — re-running upgrades in place unless ``--clean`` — and
never blocks on user input.
"""

from __future__ import annotations

from ._env import (
    MCP_CODER_REPO,
    REPORT_BINARIES,
    REPORT_PACKAGES,
    InstallConfig,
    ensure_system_uv,
    exe,
    run,
    venv_bin,
)
from ._phases import (
    phase_bootstrap_pip_uv,
    phase_install_main,
    phase_overrides,
    phase_report_versions,
    phase_venv,
)

__all__ = [
    "MCP_CODER_REPO",
    "REPORT_BINARIES",
    "REPORT_PACKAGES",
    "InstallConfig",
    "install",
]


def install(config: InstallConfig) -> None:
    """Run every install phase for a resolved configuration.

    System uv is required: every install command goes through it (with
    ``--python <venv-py>``), because the in-venv uv can vanish mid-run —
    ``uv sync`` rewrites the venv to match the lockfile, which removes
    uv+pip when they are not project dependencies.

    Args:
        config: Resolved install configuration.
    """
    uv_bin = ensure_system_uv()

    venv = config.target / ".venv"
    bin_dir = venv_bin(venv)
    py_v = bin_dir / exe("python")

    src_label = config.source
    if config.source == "git":
        src_label += f"@{config.ref}"
    elif config.source == "local":
        src_label += f" ({config.local_path})"
        if config.use_sync:
            src_label += " [uv sync]"
    print(f"=== mcp-coder install -> {config.target}")
    print(f"    source: {src_label}")

    phase_venv(config, venv)
    phase_bootstrap_pip_uv(config, py_v)
    is_editable = phase_install_main(config, uv_bin, py_v)
    phase_overrides(config, uv_bin, py_v, is_editable)

    if config.extra_packages:
        run(
            [
                uv_bin,
                "pip",
                "install",
                "--python",
                str(py_v),
                *config.extra_packages.split(),
            ],
            dry=config.check,
        )

    phase_report_versions(config, bin_dir, uv_bin, py_v)
    print(f"\nOK  mcp-coder install complete: {config.target}")
