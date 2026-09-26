# Installation

mcp-coder ships a single installer, the `mcp-coder install` subcommand, shared by
every install flow — PyPI release, developer reinstall, and CI / worker
provisioning. The wrappers below choose the right flags for each scenario.

## Prerequisites

- Python 3.11+
- Git
- `pip install mcp-coder` — the installer is a subcommand, so mcp-coder has to be
  installed somewhere before it can provision anything
- `uv` on PATH — if missing, `mcp-coder install` auto-runs `pip install uv` for you

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

The wrapper needs an `mcp-coder` **outside** the repo venv to drive the install —
either on PATH or pointed at by `MCP_CODER_VENV_PATH` — because the install
rewrites `<repo>/.venv` and cannot run from the binary it is replacing. So a fresh
clone needs `pip install mcp-coder` (the tool env) first; `uv sync --extra dev`
does not satisfy this. That copy must also be new enough to carry the `install`
subcommand — an older one fails with `invalid choice: 'install'`, and the fix is
`pip install -U mcp-coder` in the tool env, not re-running the wrapper.

### Custom / bleeding-edge — `mcp-coder install`

```bash
# Latest unreleased commit on a branch:
mcp-coder install /path/to/target --source git --ref main --local-path /path/to/checkout

# A specific tag or SHA:
mcp-coder install /path/to/target --source git --ref v1.2.3 --local-path /path/to/checkout

# Local checkout, editable:
mcp-coder install /path/to/target --source local --local-path /path/to/checkout

# Stable PyPI release into a custom location:
mcp-coder install /path/to/target --source pypi
```

Use it to install a not-yet-released fix or a colleague's branch
(`--source git`), to reproduce a known state (`--ref <sha|tag|branch>`), or to
provision a worker / CI environment into a custom directory rather than your
active Python.

Run `mcp-coder install --help` for the full flag list.

#### Sibling packages: with or without a checkout

The GitHub HEAD overrides for the sibling packages (mcp-tools-py, mcp-workspace,
mcp-coder-utils) come from `[tool.mcp-coder.install-from-github]` — read from
`--local-path`, which defaults to `<target>`. A fresh `--source git` target is an
empty directory with no `pyproject.toml`, so **the overrides are skipped unless
`--local-path` points at a checkout of the declaring repo**, and the siblings then
come from PyPI, where they lag mcp-coder's imports.

Sibling-pinned (recommended):

```bash
git clone https://github.com/MarcusJellinghaus/mcp_coder.git /path/to/checkout
mcp-coder install /path/to/target --source git --local-path /path/to/checkout
```

No checkout — PyPI siblings:

```bash
mcp-coder install /path/to/target --source git
```

This is only appropriate when the published sibling versions are what you want.
Nothing checks afterwards that the resulting environment is consistent.

## Optional extras

Several features are gated behind pip extras (LangChain providers, MLflow
logging, Textual dev tooling, …). See
[Optional Dependencies](../configuration/optional-dependencies.md) for the
full list.

The default extras come from `[tool.mcp-coder.install] extras` in the
`pyproject.toml` at `--local-path` — which defaults to `<target>`, so the
`--source git --local-path <checkout>` forms above take their extras from the
checkout, not from the target. Absent that key, the fallback is `dev`.
`--extras` overrides it; `--extras ""` installs none.

## Troubleshooting

- **`uv` not found** — the installer attempts `pip install uv` automatically. If
  that fails (no network, PEP 668 externally-managed-environment, etc.),
  install it manually: `pip install uv` or follow
  [astral.sh/uv](https://docs.astral.sh/uv/).
- **Two `.venv` dirs after `--use-sync`** — `uv sync` writes to
  `<local-path>/.venv`; the installer enforces `target == --local-path` when
  `--use-sync` is set and exits early if they differ.

## See also

- [Environments architecture](../environments/environments.md) — the two-venv
  setup (tool env vs project env) used during automation
- [Optional Dependencies](../configuration/optional-dependencies.md) — pip
  extras catalog
