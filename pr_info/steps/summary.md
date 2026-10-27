# Summary — Jenkins tools: list recent builds by status and download console logs (#1335)

## Goal

Two thin command-line tools in `tools/`:

- `jenkins_builds` prints recent builds (time, status, folder, job, build number).
- `jenkins_download_logs` saves the console logs of the selected builds.

All Jenkins logic lives in `mcp_coder.utils.jenkins_operations`, so the tools can later become MCP tools without a rewrite.

## Architectural / design changes

| Layer | Change |
|---|---|
| `jenkins_operations/models.py` | New frozen dataclass `BuildInfo` (exported from the package `__init__`). |
| `jenkins_operations/builds.py` (new) | Pure, I/O-free functions: status mapping, job-path splitting, `tree=` query construction, tree flattening, sort/truncate/filter, status validation, log filename. Unit-tested on plain dicts with no mocks. |
| `jenkins_operations/client.py` | Two thin methods on `JenkinsClient`: `get_recent_builds` (one `get_info` request) and `get_console_output` (one `jenkins_open` request). Both route `JenkinsException` through the existing `_wrap_jenkins_error`, so the existing 403/404 diagnostics apply. |
| `tools/jenkins_builds.py` (new) | argparse, config check, table output and exit codes. Also holds the selection-argument and client-factory helpers that `jenkins_download_logs.py` imports, the same way the sibling imports work in `tools/mlflow/`. |
| `tools/jenkins_download_logs.py` (new) | argparse, writes one file per build, exit codes. |
| `.bat` / `.sh` wrappers | Always run the repo's `.venv` Python; fail clearly if it is missing. |
| Tests | Integration fixtures move from `test_integration.py` to a plain module, `integration_fixtures.py`. The two conftests re-export them, so no Jenkins setup is added to the root conftest. |
| Docs / agent setup | Row in `docs/repository-setup/internal.md`, `## Jenkins` block in `.claude/CLAUDE.md`, four allow entries in `.claude/settings.local.json`. |

### Key design decisions

- **One request for the whole tree.** `api/json?tree=jobs[...]` nests `jobs[...]` down to `MAX_DEPTH = 4`, because Jenkins has no recursive tree syntax. Jobs nested deeper than that are not reported.
- **Jenkins range syntax.** The range goes after the sub-field list: `builds[number,building,result,timestamp,duration,url]{0,N}`. The query uses `builds` when `limit <= 100` and `allBuilds` above 100 (Jenkins caps `builds` at 100 per job).
- **`limit` is a time window.** Merge across all jobs → sort newest first → keep `limit` → only then filter by `statuses`.
- **Statuses:** `running`, `success`, `unstable`, `failure`, `aborted`, `not_built`, `unknown`. An unknown value raises `ValueError` before any request is sent and outside the `try`, so it is never turned into a `JenkinsError`.
- **`job_path` comes from Jenkins `fullName`**, never from the URL. Multibranch branch names stay URL-encoded (`feature%2Fx`) everywhere.
- **Folder scope:** `get_info(item="job/A/job/B", ...)`. Pass the folder segments unencoded, because `get_info` already applies `quote()` to `item`. A folder that does not exist → `NotFoundException` → `_wrap_jenkins_error(job_path=folder)`, which runs `diagnose_404`.
- **Console log:** `jenkins_open(Request("GET", base_url + job_url_path(job_path) + f"/{n}/consoleText"))`. This avoids `get_build_console_output`, which hides 404s. A 404 is wrapped with `build_number`, so `diagnose_build_404` runs.
- **Logging:** `get_console_output` has no `@log_function_call` (a whole log would be logged); it logs only the length.

## Files

### Created
- `src/mcp_coder/utils/jenkins_operations/builds.py`
- `tests/utils/jenkins_operations/test_builds.py`
- `tests/utils/jenkins_operations/test_client_builds.py`
- `tests/utils/jenkins_operations/integration_fixtures.py`
- `tools/jenkins_builds.py`, `tools/jenkins_builds.bat`, `tools/jenkins_builds.sh`
- `tools/jenkins_download_logs.py`, `tools/jenkins_download_logs.bat`, `tools/jenkins_download_logs.sh`
- `tests/tools/conftest.py`
- `tests/tools/test_jenkins_builds.py`
- `tests/tools/test_jenkins_download_logs.py`

### Modified
- `src/mcp_coder/utils/jenkins_operations/models.py` — `BuildInfo`
- `src/mcp_coder/utils/jenkins_operations/__init__.py` — export `BuildInfo`
- `src/mcp_coder/utils/jenkins_operations/client.py` — `get_recent_builds`, `get_console_output`
- `tests/utils/jenkins_operations/conftest.py` — re-export the integration fixtures
- `tests/utils/jenkins_operations/test_integration.py` — fixtures removed; new integration tests
- `docs/repository-setup/internal.md`
- `.claude/CLAUDE.md`
- `.claude/settings.local.json`
- `tools/forbidden_calls_check.sh`, `tools/ruff_check.sh`, `tools/mlflow/start_mlflow.sh` — mode set to executable

## Steps

1. `BuildInfo` + pure functions in `builds.py` (TDD, no mocks)
2. `JenkinsClient.get_recent_builds` / `get_console_output` (TDD, python-jenkins mocked)
3. Move integration fixtures to `integration_fixtures.py` (refactor, no behaviour change)
4. Integration tests for the two client methods
5. `jenkins_builds` tool + wrappers + tests
6. `jenkins_download_logs` tool + wrappers + `tests/tools/conftest.py` + tests (unit + end-to-end)
7. Docs and agent setup (`internal.md`, `.claude/CLAUDE.md`, `.claude/settings.local.json`)

## Checks for every step

Run these before committing; all must pass:

```
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_format_code
```

In steps 4 and 6, also run `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto"], markers=["jenkins_integration"])`. These tests skip when Jenkins is not configured.
