# Step 5 — Delete the old installer, rewrite `reinstall_local.*`, update CI

One commit by necessity: `ci.yml:172` is the last consumer of `tools/install.py`.
Deleting the file in a separate commit from the CI edit fails that commit's own CI run.

## WHERE

| File | Action |
|---|---|
| `tools/install.py` | **deleted** |
| `tools/install.bat` | **deleted** |
| `tools/install.sh` | **deleted** |
| `pyproject.toml` | drop `[tool.setuptools.data-files]` (`:139-145`, comment included); add `[tool.mcp-coder.install]` |
| `tools/reinstall_local.bat` | rewritten |
| `tools/reinstall_local.sh` | rewritten |
| `.github/workflows/ci.yml` | `vscodeclaude-template-install` job (`:136-183`) |

`tests/tools/__init__.py` stays — `tests/tools/mlflow/` still needs it.
`[tool.setuptools.packages.find]` auto-discovers `mcp_coder.install`, so no packaging
addition is needed to replace the data-files entry.

## WHAT

No Python API changes. One TOML section, two shell wrappers and one CI job.

**`pyproject.toml` declares its own extras.** Next to the existing
`[tool.mcp-coder.install-from-github]`:

```toml
[tool.mcp-coder.install]
extras = "dev"
```

Same value the deleted `--extras dev` hardcoded, so nothing about the install changes —
but mcp_coder is itself a target repo (the CI job and `reinstall_local` both install
it), so without this the Step 4 contract row warns on the repo that introduced it.

**Driver resolution (Decisions 20 + 22)** — `reinstall_local` is the one caller that
would otherwise drive an install from the venv being rewritten: the driver becomes
`mcp-coder.exe`, and `_phase_install_main` rewrites that same file (the Windows
self-replacement lock). It must therefore resolve an `mcp-coder` from **outside**
`<repo>/.venv`.

Order, identical on both platforms:

1. `MCP_CODER_VENV_PATH` (a bin/Scripts *directory*, not a venv root) — used only when
   set, holding an `mcp-coder`, **and** not equal to the repo venv's bin dir.
2. A PATH lookup taking the first hit whose directory is not the repo venv bin dir.
   Windows `where` lists all hits; `command -v` returns only the first and cannot
   express the filter, so the `.sh` side uses `type -a -P mcp-coder`.
3. Hard-fail with an actionable message.

The repo-venv filter gates **both** branches. `claude.bat:16-18` routes an activated
repo venv into `:discover_from_path`, whose non-shadow-proof `where` (`:27-31`) yields
`<repo>\.venv\Scripts`, which `claude.bat:45` assigns straight to
`MCP_CODER_VENV_PATH` — an unfiltered branch 1 would hand back the exact executable
about to be rewritten. Do **not** copy `claude.bat:25-33`'s fallback as-is.

## ALGORITHM

`tools/reinstall_local.bat`

```
for %%d in ("%~dp0..") do set "REPO=%%~fd"      # normalise; %~dp0.. is not a real path
set "REPO_BIN=%REPO%\.venv\Scripts"
set "MC="
if defined MCP_CODER_VENV_PATH  if exist "%MCP_CODER_VENV_PATH%\mcp-coder.exe" ^
   if /i not "%MCP_CODER_VENV_PATH%"=="%REPO_BIN%"  set "MC=%MCP_CODER_VENV_PATH%\mcp-coder.exe"
if not defined MC  for /f "delims=" %%i in ('where mcp-coder 2^>nul') do ^
   if not defined MC  if /i not "%%~dpi"=="%REPO_BIN%\"  set "MC=%%i"
if not defined MC  ( echo [FAIL] <message>  & exit /b 1 )
"%MC%" install "%REPO%" --source local --local-path "%REPO%" ^
    --extra-packages "langchain langchain-anthropic mlflow" --refresh
<existing activate tail, unchanged>
```

`tools/reinstall_local.sh` — same order, `$REPO_DIR/.venv/bin` as the filter, and:

```
for p in $(type -a -P mcp-coder 2>/dev/null); do
    case "$p" in "$REPO_DIR/.venv/bin/"*) continue ;; esac
    MC="$p"; break
done
```

`--extras dev` is **dropped** (repo policy now); `--extra-packages` and `--refresh`
**survive** — per-invocation dev convenience, not repo policy. Both scripts keep their
existing venv-activation tails verbatim.

`.github/workflows/ci.yml`, `vscodeclaude-template-install`:

```yaml
run: |
  set -euo pipefail

  # Bootstrap mcp-coder into the SYSTEM Python, not ./.venv:
  # `mcp-coder install . --use-sync` runs `uv sync`, which rewrites ./.venv
  # mid-run and would wipe a bootstrap installed there.
  #
  # Siblings come from GitHub HEAD, exactly as every other job does: the PyPI
  # copies of mcp-workspace / mcp-coder-utils are too old for mcp_coder's
  # imports, so a bare `uv pip install --system .` bootstrap could not even
  # `import mcp_coder`, let alone run the install subcommand.
  mapfile -t SPECS < <(python tools/read_github_deps.py --specs)
  uv pip install --system "${SPECS[@]}" .

  # Mirror the argv session_setup.build_install_argv produces:
  mcp-coder install . --source local --local-path . --use-sync --refresh

  source .venv/bin/activate
  mcp-coder --version
  mcp-tools-py --version        # Decision 15: restores the CLI_BINARIES check §2 removed
  mcp-workspace --version
  python -c "import mcp_coder; print('mcp_coder import OK from', mcp_coder.__file__)"
```

The `mapfile` + `uv pip install --system "${SPECS[@]}"` pair is copied verbatim from
`ci.yml:123-124`, the pattern every other job already uses.
Rewrite the stale job comment at `:136-143` and the inline one at `:164-171` — both
describe the deleted script and the wheel-deployed copy.

## DATA

Failure message for branch 3 (both wrappers, same wording):

```
[FAIL] No mcp-coder found outside <repo>\.venv.
       reinstall_local rewrites the repo venv, so it cannot be driven from it.
       Install the tool env first (pip install mcp-coder) or set
       MCP_CODER_VENV_PATH to its Scripts/bin directory.
```

## TESTS

Nothing unit-testable here — the wrappers are shell and the CI job is the test. Verify by:

1. Full local check suite (below) — `run_vulture_check` in particular, to catch anything
   left dangling by the deletions.
2. `git grep -n "install\.py"` returns only historical references in `docs/`, which
   Step 6 clears.
3. The `vscodeclaude-template-install` job passing on the pushed branch.

Also state in the commit message that `tools/reinstall_local.*` now requires an
`mcp-coder` on PATH (or `MCP_CODER_VENV_PATH`) before it can run in a fresh clone —
`uv sync --extra dev` does not satisfy this, since it populates the repo venv the
wrapper deliberately ignores. Step 6 documents it.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`.
>
> Implement Step 5 only, as one commit: delete `tools/install.py`, `tools/install.bat`
> and `tools/install.sh`; drop `[tool.setuptools.data-files]` from `pyproject.toml` and
> add `[tool.mcp-coder.install] extras = "dev"`; rewrite `tools/reinstall_local.bat` and
> `tools/reinstall_local.sh` with the three-branch driver resolution; update the
> `vscodeclaude-template-install` job in `.github/workflows/ci.yml`.
>
> The CI bootstrap must install the GitHub sibling specs before `.`, mirroring
> `ci.yml:123-124` — the PyPI copies are too old to import.
>
> The repo-venv filter must gate both the `MCP_CODER_VENV_PATH` branch and the PATH
> branch — see the rationale in this step. Normalise `%~dp0..` with `%%~fd` before
> comparing paths. Keep `--extra-packages` and `--refresh`; drop `--extras dev`. Keep
> both scripts' existing activation tails.
>
> Documentation is Step 6 — leave `docs/` and `README.md` alone.
>
> Then run `run_format_code`, `run_pylint_check`, `run_mypy_check`, the fast pytest
> selection and `run_vulture_check`. Commit once, green.
