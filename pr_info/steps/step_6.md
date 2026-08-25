# Step 6 — `verify_jenkins()` and the two verify sections

Read [summary.md](summary.md) first.

`mcp-coder verify` already validates the config file holding `[jenkins]` credentials but never
tests them.

## WHERE

- `src/mcp_coder/cli/commands/verify_jenkins.py` (create)
- `tests/cli/commands/test_verify_jenkins.py` (create)
- `src/mcp_coder/cli/commands/verify.py` (modify, after `:385`)
- `src/mcp_coder/cli/commands/verify_exit_code.py` (modify)
- `src/mcp_coder/cli/commands/verify_formatting.py` (modify, `_LABEL_MAP`)
- `tests/cli/commands/conftest.py` (modify — autouse fixture)

## WHAT

```python
def verify_jenkins() -> tuple[dict[str, Any], dict[str, Any]]:
    """Probe Jenkins connectivity/permissions and per-repo Job/Read access.

    Returns:
        ``(server_result, jobs_result)``. Each is a ``_format_section``-shaped dict —
        ``{key: {"ok": bool | None, "value": str, "error"?: str, "install_hint"?: str}}``
        plus ``"overall_ok"``. Both are ``{}`` (skipped) when ``[jenkins]`` is unconfigured;
        ``jobs_result`` is ``{}`` when no coordinator repos are configured.
    """
```

One function, not two: both sections need the same config and the same authenticated client, and
one function gives tests one mock target.

Target output:

```
JENKINS
  Server            [OK] https://jenkins:8080 reachable
  Authentication    [OK] job_manager (API token valid)
  Overall/Read      [OK] granted

JENKINS JOBS
  my-repo           [ERR] Windows-Agents/Executor (404: 'Windows-Agents' is readable,
                          'Executor' under it is not - wrong name or Job/Read not granted)
                          -> docs/repository-setup/jenkins.md
```

## HOW

```python
from ...utils.jenkins_operations.client import JenkinsClient, _get_jenkins_config
from ...utils.jenkins_operations.diagnostics import (
    DOCS_POINTER, diagnose_403, diagnose_404, job_url_path, probe,
)
from ...utils.user_config import load_config
```

`mcp_coder.cli` sits above `mcp_coder.utils` in `layered_architecture`, so no exemption is needed.

**Credential source: `_get_jenkins_config()` from `client.py`, not `load_config()`.** This is the
same helper `coordinator/core.py` resolves credentials through, and it goes via
`get_config_values`, which applies the `JENKINS_URL` / `JENKINS_USER` / `JENKINS_TOKEN` env
overrides declared in `user_config._CONFIG_SCHEMA`. `load_config()` reads the TOML file only, so
sourcing credentials from it would make `verify` skip the section entirely for an env-var-only
setup, or — worse — probe a *different* server than the coordinator actually dispatches to, which
is precisely the class of confidently-wrong report this issue exists to remove. It returns
`{"server_url": ..., "username": ..., "api_token": ...}` with `None` for anything unset.

**Repo list source:** `load_config().get("coordinator", {}).get("repos", {})` directly — there are
no env overrides for `[coordinator.repos.*]`, so the file is the only source. **Not**
`load_repo_config` from `coordinator/core.py` — `core.py:21` imports `JenkinsClient` and
`core.py:14-20` the GitHub/branch-manager stack, which would pull the whole coordinator into
verify's import graph.

Both calls can raise `ValueError` on malformed TOML; contain both (see ALGORITHM).

**Not reusing `_verify_wildcard_repos`** (`user_config.py:522-563`): it is a pure config parser
rendered inside the CONFIG section, returns a different shape (`{entries, has_error}`, not the
`{key: {ok, value}}` that `_format_section` consumes), and its `has_error` feeds an unconditional
exit 1. No network calls are added to `mcp_coder.utils.user_config`.

**`_format_section` for both sections**, including the per-repo one. It tolerates arbitrary keys
(`_LABEL_MAP.get(key, key)`, `verify_formatting.py:192`) and renders `(error)` plus
`-> install_hint`. `_format_mcp_section` does **not** implement install hints, so cloning it would
silently drop the docs pointer.

`_LABEL_MAP` additions (verified collision-free):

```python
# Jenkins section
"server": "Server",
"authentication": "Authentication",
"overall_read": "Overall/Read",
```

Jobs-section keys are repo names and pass through unmapped.

Session access needs one documented protected access:

```python
session = client._http  # pylint: disable=protected-access  # documented probe seam, see client.py
```

`verify.py` wiring, after `:385` (`GITHUB`) and before `BASIC VERIFICATION` (`:392`):

```python
jenkins_result, jenkins_jobs_result = verify_jenkins()
if jenkins_result:
    print(_format_section("JENKINS", jenkins_result, symbols))
if jenkins_jobs_result:
    print(_format_section("JENKINS JOBS", jenkins_jobs_result, symbols))
jenkins_ok: bool | None = None
if jenkins_result:
    jenkins_ok = bool(jenkins_result.get("overall_ok")) and bool(
        jenkins_jobs_result.get("overall_ok", True)
    )
```

`verify_exit_code._compute_exit_code` gets **one** new keyword parameter `jenkins_ok: bool | None
= None` (it already has 12; two would be worse), following the `claude_mcp_ok` / `tools_exposed_ok`
pattern and the MLFLOW gated-failure precedent:

```python
# Jenkins: only fail when [jenkins] is configured (None = unconfigured, neutral)
if jenkins_ok is False:
    return 1
```

An unconfigured `[jenkins]` already trips CONFIG's required-field check, so skipping is safe.

## ALGORITHM

```
try: creds = _get_jenkins_config()      # env overrides applied (JENKINS_URL/USER/TOKEN)
except ValueError: return {}, {}          # malformed TOML - CONFIG already reports it
if any of server_url/username/api_token is None: return {}, {}
try: client = JenkinsClient(creds["server_url"], creds["username"], creds["api_token"])
except ValueError: return {}, {}
session, base = client._http, client.base_url

root = probe(session, base, "/api/json")
server/authentication/overall_read rows from root.status:
   None -> server ERR (unreachable, root.error_text); other two ok=None "not checked"
   401  -> server OK; authentication ERR; overall_read ok=None
   403  -> server OK; authentication OK; overall_read ERR with
           diagnose_403(session, base, root.error_text) as `error`
   200  -> all three OK
   else -> server ERR "unexpected HTTP {status}"
server_result["overall_ok"] = all rows not False

try: repos = load_config().get("coordinator", {}).get("repos", {})
except ValueError: repos = {}             # malformed TOML - CONFIG already reports it
if server_result not ok or not repos: return server_result, {}
for repo_name, repo_cfg in repos.items():
    path = repo_cfg.get("executor_job_path");  skip repo if missing/not a str
    r = probe(session, base, job_url_path(path) + "/api/json")
    200 -> {"ok": True,  "value": path}
    404 -> {"ok": False, "value": path, "error": diagnose_404(session, base, path),
            "install_hint": "docs/repository-setup/jenkins.md"}
    403 -> {"ok": False, "value": path, "error": diagnose_403(session, base, r.error_text),
            "install_hint": "docs/repository-setup/jenkins.md"}
    else-> {"ok": False, "value": path, "error": "unexpected HTTP {status}" or transport error,
            "install_hint": ...}
jobs_result["overall_ok"] = all rows ok
```

Skip the jobs section entirely when the server section failed — every row would repeat the same
upstream cause.

## DATA

- `server_result` keys, in insertion order: `server`, `authentication`, `overall_read`,
  `overall_ok`.
- `jobs_result` keys: one per configured repo (repo name), plus `overall_ok`.
- `{}` means "skipped, exit-neutral" for both.

## TESTS (write first)

**Hermetic-test fixture first.** `execute_verify` reads the real `~/.mcp_coder/config.toml`, so on
a machine with `[jenkins]` configured the new sections would issue live HTTP during the existing
~20 `tests/cli/commands/test_verify*.py` files. Add an autouse fixture to
`tests/cli/commands/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _neutral_jenkins_verify() -> Generator[None, None, None]:
    """Keep execute_verify hermetic: no live Jenkins probes in CLI command tests."""
    with patch(f"{_VERIFY}.verify_jenkins", return_value=({}, {})):
        yield
```

This patches the *import site* in `verify.py`. `test_verify_jenkins.py` imports from
`mcp_coder.cli.commands.verify_jenkins` directly, so it is unaffected.

`tests/cli/commands/test_verify_jenkins.py` — patch `_get_jenkins_config`, `load_config`,
`JenkinsClient` and `probe`:

- unconfigured `[jenkins]` → `({}, {})`, no client constructed
- partially configured (`server_url` only) → `({}, {})`
- `_get_jenkins_config` raising `ValueError` → `({}, {})`, exception contained
- `load_config` raising `ValueError` while credentials resolve → server section still rendered,
  `jobs_result == {}`, exception contained
- **env-override test**: with no `[jenkins]` section in the config file but `JENKINS_URL` /
  `JENKINS_USER` / `JENKINS_TOKEN` set via `monkeypatch.setenv` (and `_get_jenkins_config` *not*
  patched), the section is rendered and `JenkinsClient` is constructed with the env values. This
  is the regression guard for sourcing credentials from `load_config()` instead of
  `_get_jenkins_config()`.
- all probes 200, two repos → both sections `overall_ok is True`, three server rows, two job rows
- root probe 403 → `overall_read` `ok is False`, its `error` contains
  `"Overall/Read"` and `"docs/repository-setup/jenkins.md"`; jobs section is `{}`
- root probe 401 → `authentication` fails, `overall_read` is `ok is None` (not a hard fail)
- root probe transport failure → `server` fails and carries the transport message
- repos configured but job probe 404 → that repo's row has `ok is False`, an `error` naming both
  path segments, and `install_hint == "docs/repository-setup/jenkins.md"`
- server ok, no repos configured → `jobs_result == {}`
- a repo whose `executor_job_path` is missing is skipped without raising

Rendering and exit code:

- `_format_section("JENKINS JOBS", jobs_result, STATUS_SYMBOLS)` on a failed row emits both
  `(error)` and a following `-> docs/repository-setup/jenkins.md` line — the documented mechanism
  for the docs pointer
- `_compute_exit_code(..., jenkins_ok=False)` → `1`; `jenkins_ok=None` and `jenkins_ok=True` → `0`
  (add to `tests/cli/commands/test_verify_exit_codes.py`)
- one orchestration test in `test_verify_jenkins.py` that overrides the autouse fixture and asserts
  `execute_verify` prints `=== JENKINS ` between the `GITHUB` and `BASIC VERIFICATION` headers

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Steps 1-3 must be committed first.
>
> Implement step 6 test-first. Add the autouse `_neutral_jenkins_verify` fixture to
> `tests/cli/commands/conftest.py` first — without it the existing verify suite starts making live
> network calls. Then write `tests/cli/commands/test_verify_jenkins.py`, watch it fail, then write
> `src/mcp_coder/cli/commands/verify_jenkins.py` and wire it into `verify.py` after `:385`.
>
> One `verify_jenkins()` returning a tuple of two dicts — not two functions. One new
> `jenkins_ok: bool | None` parameter on `_compute_exit_code` — not two. Use `_format_section` for
> both sections, including the per-repo one; `_format_mcp_section` would silently drop the
> `install_hint` docs pointer.
>
> Source the **credentials** from `_get_jenkins_config()` in
> `utils/jenkins_operations/client.py`, **not** from `load_config().get("jenkins", {})` — only the
> former applies the `JENKINS_URL` / `JENKINS_USER` / `JENKINS_TOKEN` env overrides, so
> `load_config()` would make verify skip or probe different credentials than the coordinator uses.
> Get the **repo list** from `load_config()` directly (no env overrides exist for it), never from
> `coordinator/core.py` — importing it would drag the whole coordinator into verify's import
> graph. Contain the `ValueError` both can raise on malformed TOML.
>
> Run, with MCP tools only: `mcp__tools-py__run_pylint_check`, `mcp__tools-py__run_mypy_check`,
> `mcp__tools-py__run_lint_imports_check`, `mcp__workspace__check_file_size` with
> `max_lines=750`, and `mcp__tools-py__run_pytest_check` with
> `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`.
> Fix everything they report, then `./tools/format_all.sh` and commit as one commit.
