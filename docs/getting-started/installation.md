# Installation

mcp-coder ships a single installer (`tools/install.py`) shared by every install
flow — PyPI release, developer reinstall, and CI / worker provisioning. The
wrappers below choose the right flags for each scenario.

## Prerequisites

- Python 3.11+
- Git
- `uv` on PATH — if missing, install.py auto-runs `pip install uv` for you

## Pick your install

### Typical user — stable release

```bash
pip install mcp-coder
```

Installs the latest published release from PyPI. Fastest, no clone.

### Developer — editable local checkout

```bash
git clone https://github.com/MarcusJellinghaus/mcp_coder.git
cd mcp_coder
# Windows:
tools\reinstall_local.bat
# POSIX:
source tools/reinstall_local.sh
```

Editable install (`pip install -e`) of your checkout, plus sibling MCP packages
pinned to GitHub HEAD via `[tool.mcp-coder.install-from-github]` in
`pyproject.toml`. Re-run `reinstall_local` after a `git pull` that touches
dependencies.

### Bleeding-edge / custom — call `install.py` directly

```bash
# Latest unreleased commit on a branch:
python tools/install.py /path/to/target --source git --ref main

# A specific tag or SHA:
python tools/install.py /path/to/target --source git --ref v1.2.3

# Local checkout, editable:
python tools/install.py /path/to/target --source local --local-path /path/to/checkout

# Stable PyPI release into a custom location:
python tools/install.py /path/to/target --source pypi
```

`tools/install.py` is the canonical script and supports every install scenario
the project has. Useful when you need to:

- **Install from GitHub** (`--source git`) — pull a not-yet-released fix or
  test a colleague's branch without waiting for a PyPI release.
- **Pin a specific commit/tag** (`--ref <sha|tag|branch>`) — reproduce a known
  state for debugging or CI.
- **Provision a worker / CI environment** into a custom directory rather than
  your active Python.
- **Apply GitHub HEAD overrides for sibling packages** (mcp-tools-py,
  mcp-workspace, mcp-coder-utils) — controlled by
  `[tool.mcp-coder.install-from-github]`, applied automatically unless
  `--skip-overrides` is set.

Run `python tools/install.py --help` for the full flag list.

### Minimal files (no full clone)

You don't need the whole repo to run `install.py`. With `--source git` the
script fetches mcp-coder from GitHub itself; the local files only need to
tell it which sibling-package overrides to apply.

**Just `install.py`** (overrides skipped):

```bash
curl -O https://raw.githubusercontent.com/MarcusJellinghaus/mcp_coder/main/tools/install.py
python install.py /path/to/target --source git --skip-overrides
```

You get whatever PyPI has for mcp-tools-py, mcp-workspace, and
mcp-coder-utils — works, but may lag GitHub HEAD.

**`install.py` + `pyproject.toml`** (full functionality):

```bash
mkdir mcp-coder-installer && cd mcp-coder-installer
curl -O --create-dirs https://raw.githubusercontent.com/MarcusJellinghaus/mcp_coder/main/tools/install.py -o tools/install.py
curl -O https://raw.githubusercontent.com/MarcusJellinghaus/mcp_coder/main/pyproject.toml
python tools/install.py /path/to/target --source git
```

`install.py` looks for `pyproject.toml` one directory above itself (i.e.
expects `<somewhere>/tools/install.py` + `<somewhere>/pyproject.toml`) and
reads `[tool.mcp-coder.install-from-github]` to pin sibling packages to
GitHub HEAD. Alternatively, pass `--local-path <dir-with-pyproject.toml>`
to point at a different location.

## Optional extras

Several features are gated behind pip extras (LangChain providers, MLflow
logging, Textual dev tooling, …). See
[Optional Dependencies](../configuration/optional-dependencies.md) for the
full list.

## Troubleshooting

- **`uv` not found** — install.py attempts `pip install uv` automatically. If
  that fails (no network, PEP 668 externally-managed-environment, etc.),
  install it manually: `pip install uv` or follow
  [astral.sh/uv](https://docs.astral.sh/uv/).
- **`missing CLI binaries after install`** — entry points (mcp-coder,
  mcp-tools-py, etc.) didn't get wired up. Re-run with `--clean` to wipe and
  recreate the venv: `python tools/install.py <target> --clean`.
- **Two `.venv` dirs after `--use-sync`** — `uv sync` writes to
  `<local-path>/.venv`; install.py enforces `target == --local-path` when
  `--use-sync` is set and exits early if they differ.

## See also

- [Environments architecture](../environments/environments.md) — the two-venv
  setup (tool env vs project env) used during automation
- [Optional Dependencies](../configuration/optional-dependencies.md) — pip
  extras catalog
