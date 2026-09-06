# Step 6 — Documentation

Doc-only commit. Every remaining reference to `tools/install.py`, `install.bat`,
`install.sh` and the curl-bootstrap recipe goes.

## WHERE

| File | Change |
|---|---|
| `docs/getting-started/installation.md` | rewrite (closer to a rewrite than point edits) |
| `README.md` | `:143-157` |
| `docs/environments/environments.md` | `:113`, `:141` |
| `docs/repository-setup/internal.md` | `:38-39` |
| `docs/repository-setup/README.md` | `:84` + contracts table |
| `docs/cli-reference.md` | short `### install` entry |
| `docs/architecture/architecture.md` | new `install/` subsection in §5 |

## WHAT

**`docs/getting-started/installation.md`** — the named ranges are not exhaustive of the
file's `tools/install.py` references; read the whole file.

- `:3` and `:11`: the installer is a **subcommand**, not a script. Prerequisite becomes
  "`pip install mcp-coder` first".
- `:39-69`: the "call `install.py` directly" section becomes "custom / bleeding-edge —
  `mcp-coder install`", with the four commands re-expressed
  (`mcp-coder install /path/to/target --source git --ref main --local-path <checkout>`,
  etc.). Trim the six-bullet rationale to two or three — most of it justified a
  standalone script that no longer exists.
- `:64-67`: the "applied automatically unless `--skip-overrides`" claim now holds only
  when the pyproject that declares them is reachable. `--local-path` defaults to
  `<target>` (Decisions 10 + 17), and a fresh `--source git` target is an empty
  directory with no `pyproject.toml` — so **overrides are skipped unless `--local-path`
  points at a checkout of the declaring repo**, and the siblings then come from PyPI,
  where they lag mcp-coder's imports. Document both halves:
  - the sibling-pinned form: `git clone` the repo (or reuse an existing checkout), then
    `mcp-coder install /path/to/target --source git --local-path /path/to/checkout`;
  - the no-checkout form: `mcp-coder install /path/to/target --source git`, which
    installs PyPI siblings and is only appropriate when PyPI versions are wanted.
    Say so plainly rather than leaving the reader to infer it — §2 dropped the
    required-CLI check that used to surface a half-wired env.
- `:71-100`: the curl / minimal-files section is **deleted** (Decision 1).
- `:115-120`: the `missing CLI binaries after install` entry is **deleted**, not edited —
  §2 removed the failure it documents.
- `:121-123`: the `--use-sync` troubleshooting entry keeps its content, loses the
  script name.
- **Add** the tool-env prerequisite for `reinstall_local`: a fresh clone needs an
  `mcp-coder` on PATH (or `MCP_CODER_VENV_PATH` set) before the wrapper runs, because
  the driver deliberately comes from outside the repo venv. `uv sync --extra dev` does
  not satisfy this. State the version floor, not just presence: the tool-env copy must
  itself carry the `install` subcommand — a pre-#1151 one fails with
  `invalid choice: 'install'`, and the fix is to upgrade the tool env first
  (`pip install -U mcp-coder`), not to re-run the wrapper.

**`README.md:143-157`** — replace the whole fenced block, including `:150`'s
`curl -O … pyproject.toml`, **and** the trailing prose at `:154-157`, which describes
the deleted recipe and is orphaned without it. New content: `pip install mcp-coder`,
`git clone` the repo, then
`mcp-coder install ~/mcp-coder-env --source git --local-path <checkout>`. The
`--local-path` is what the retired `curl -O … pyproject.toml` line existed for: without
it the target has no `pyproject.toml`, so `[tool.mcp-coder.install-from-github]` is
never read and the siblings come from PyPI (Decisions 10 + 17). Keep the
Installation-Guide link and point at it for the no-checkout variant.

**`docs/environments/environments.md`**
- `:113`: `reinstall_local.*` now resolves an `mcp-coder` from outside the repo venv and
  invokes `mcp-coder install <repo> --source local --local-path <repo> --refresh`.
  Point the "full design" reference at `src/mcp_coder/install/`.
- `:141`: `tools/install.py:17` → the installer's scope statement in
  `src/mcp_coder/install/__init__.py` (installs Python packages only; staging is the
  caller's job).

**`docs/repository-setup/internal.md:38-39`** — drop the `install.py`/`.bat`/`.sh` row;
`:39`'s "Thin wrappers around `install.{bat,sh}`" is false once those are gone, so
`reinstall_local.*` is redescribed as "editable dev reinstall via `mcp-coder install`".

**`docs/repository-setup/README.md`**
- `:84`: drop `tools/install.py`, `tools/install.bat`, `tools/install.sh` from the row;
  keep `reinstall_local.*`, `read_github_deps.py`, `safe_delete_folder.py`.
- Add the target-repo contracts table (Decision 9), matching `validate_target_repo`:

| Contract | Declared / enforced by | Fails how |
|---|---|---|
| extras to install | `[tool.mcp-coder.install] extras`, default `dev` | `uv sync` error — warn |
| ships `.mcp.json` (+ `.mcp.linux.json` on POSIX) | `workspace._MCP_CONFIG_FILES`, `validate_mcp_json` | `FileNotFoundError` at launch — fatal |
| `[tool.mcp-coder.install-from-github]` for sibling pinning | `pyproject_config.get_github_install_config` | silently no overrides — warn |
| venv at `<repo>/.venv` | installer, `uv sync`, `session_setup` | two venvs / empty venv — warn |

A `uv.lock` is **not** required — mcp_coder itself tracks none, so `uv sync` resolves fresh.

**`docs/cli-reference.md`** — a short `### install` section in the `## Commands` list
plus its entry in the `### Basics` command list at `:7`. Not required by the issue and
not test-enforced, but the file is a complete command list and would otherwise be stale.
Keep it to synopsis + flag table; the details live in `installation.md`.

**`docs/architecture/architecture.md`** — §5 "Building Block View" carries one subsection
per top-level package (`llm/`, `cli/`, `icoder/`, `utils/`, `workflows/`, `:182-343`).
`src/mcp_coder/install/` is a new one, with its own tach layer and import-linter row, so
add an **Installer (`src/mcp_coder/install/`)** `###` subsection after the CLI one
(`:245-254`), in the same register and length as the shorter entries: one line per module
(`__init__.py` `install()` + re-exports, `_env.py` `InstallConfig` + env helpers,
`_phases.py` the five phases), with its tests (`tests/install/`) and the `domain` layer /
`depends_on = [utils]` boundary. One short paragraph — not a rewrite of §5.

**Scope note:** this file is not in issue #1151's Scope. It is a deliberate Boy Scout fix,
accepted in review because this PR is what makes the section stale (see `Decisions.md` #14).

## DATA

No code, no data structures. Docs only.

## TESTS

None. Verification:

1. `git grep -rn "install\.py\|install\.bat\|install\.sh"` returns nothing outside
   `pr_info/` and git history. This step reaches only `docs/` and `README.md`: `src/` and
   `tests/` were cleared by Step 3's grep, and `tools/reinstall_local.{bat,sh}`'s header
   comments by Step 5. A hit anywhere else means an earlier step's exit criterion was
   skipped — fix it there, not here.
2. `mcp__mcp-tools-py__run_pytest_check` fast selection still green (docstring-adjacent
   tests, help anti-drift).
3. Link check: every path named in the edited docs exists.

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`.
>
> Implement Step 6 only — documentation. Rewrite
> `docs/getting-started/installation.md` around `mcp-coder install`, replace
> `README.md:143-157` (fenced block *and* the orphaned prose after it), and apply the
> point edits to `environments.md`, `repository-setup/internal.md`,
> `repository-setup/README.md` (including the new contracts table),
> `docs/cli-reference.md` and `docs/architecture/architecture.md` (one short new §5
> subsection for `src/mcp_coder/install/`).
>
> Follow the repo's writing style: say it once, cut anything not load-bearing. Trim the
> old rationale prose rather than translating it one-for-one — most of it justified a
> standalone script that no longer exists.
>
> Finish by grepping the repo for `install.py`, `install.bat` and `install.sh` to prove
> nothing outside `pr_info/` still references them. Then run `run_format_code` and the
> fast pytest selection, and commit once.
