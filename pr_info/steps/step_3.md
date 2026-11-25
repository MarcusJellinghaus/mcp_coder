# Step 3 — Retry at the uv install/sync call sites

## LLM prompt
> Read `pr_info/steps/summary.md` (§2 and "Unchanged on purpose") and this file.
> Implement step 3 only: pass `retry_on=UV_TRANSIENT_SIGNATURES` at every
> `uv pip install` / `uv sync` call in `src/mcp_coder/install/`, and nowhere else.
> Write the table-driven test first, then the code, then the two doc lines. Run ruff
> check, pylint, mypy and the fast unit tests (CLAUDE.md), format, and make one commit.
> Precondition: `_env.run()` accepts `retry_on` and `_env.UV_TRANSIENT_SIGNATURES`
> exists (step 2). If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE
- `src/mcp_coder/install/_phases.py`
- `src/mcp_coder/install/__init__.py`
- `tests/install/test_install_phases.py` (new test class)
- `docs/configuration/setup.md` — section "Built-in `python`"
- `docs/cli-reference.md` — section `### install`

## WHAT
Import `UV_TRANSIENT_SIGNATURES` from `._env` in `_phases.py` and `__init__.py`, and add
`retry_on=UV_TRANSIENT_SIGNATURES` to exactly these `run()` calls:

| Function | Call |
|---|---|
| `phase_bootstrap_pip_uv` | the `uv_bootstrap` branch (`uv pip install --python … pip uv`) |
| `phase_install_main` | `--source git` install |
| `phase_install_main` | `--source pypi` install |
| `phase_install_main` | `--use-sync` `uv sync` (keeps `cwd=config.local_path`) |
| `phase_install_main` | editable `uv pip install -e …` |
| `phase_overrides` | `overrides.packages` install |
| `phase_overrides` | `overrides.packages_no_deps` install |
| `phase_overrides` | editable re-link (`-e … --no-deps`) |
| `install()` | `extra_packages` install |

Not changed: `uv venv` and `python -m venv` (`phase_venv`), the in-venv pip fallback in
`phase_bootstrap_pip_uv`, `--version` and `uv pip show` (`phase_report_versions`), the
dry echo in `phase_post_install_checks`, `ensure_system_uv`.

## HOW (test — write first)
New class `TestRetryCallSites` in `tests/install/test_install_phases.py`:

- Record every `run()` call: patch `mcp_coder.install._phases.run` **and**
  `mcp_coder.install.run` with one recorder
  `def _rec(cmd, **kwargs): calls.append((cmd, kwargs)); return 0`.
- Patch `mcp_coder.install.ensure_system_uv` → `_STUB_UV` and `shutil.which` → `_STUB_UV`
  (or `None` for the fallback case).
- Run `install(InstallConfig.from_args(_namespace(check=False, …)))` — `check=False` so
  the version report runs (it returns early in `--check`); nothing real executes because
  `run` is patched and no post-install checks are declared.
- Parametrize:
  - `source="git"`;
  - `source="pypi"`;
  - `source="local"`, `local_path=tmp_path`, pyproject with `packages` and
    `packages_no_deps`, `extra_packages="langchain"`;
  - `source="local"`, `local_path=tmp_path`, `use_sync=True`;
  - `source="git"` with `shutil.which` → `None` (stdlib venv + in-venv pip fallback).
- Rule, asserted for every recorded call:

```python
def _is_uv_install(cmd):
    return cmd[0] == _STUB_UV and (cmd[1:3] == ["pip", "install"] or cmd[1] == "sync")

assert (kwargs.get("retry_on") == UV_TRANSIENT_SIGNATURES) == _is_uv_install(cmd)
```

- Sanity per case: at least one recorded call satisfies `_is_uv_install` and at least one
  does not (e.g. `uv pip show`), so the rule is never checked against an empty set.

## Docs
- `docs/configuration/setup.md`, "Built-in `python`" — add one bullet:
  `- uv install/sync commands are retried once, after 10 s, on a transient PyPI network
  error or a uv-cache "Access is denied" — only when stderr is not a terminal (e.g. Jenkins).`
- `docs/cli-reference.md`, `### install` — one sentence after the post-install checks
  paragraph, same content.

## ALGORITHM
None — keyword argument additions.

## DATA
No signature changes.
