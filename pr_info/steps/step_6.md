# Step 6 — `jenkins_download_logs` tool, wrappers and tests

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 6** exactly as described in `pr_info/steps/step_6.md`.
> Use TDD: write `tests/tools/test_jenkins_download_logs.py` first, then create `tests/tools/conftest.py`, `tools/jenkins_download_logs.py` and the wrappers.
> Run pylint, the fast pytest set and mypy. Also run `run_pytest_check(extra_args=["-n", "auto"], markers=["jenkins_integration"])`; those tests must pass, or skip when Jenkins is not configured. All must pass. Then run the formatter, then make one commit. `tools/jenkins_download_logs.sh` already exists as an executable placeholder: overwrite its content with `save_file`. Its executable mode is already in git, so no chmod is needed.

## WHERE

- `tools/jenkins_download_logs.py` — **new**
- `tools/jenkins_download_logs.bat` — **new**
- `tools/jenkins_download_logs.sh` — **existing placeholder**, replace content (already executable in git)
- `tests/tools/conftest.py` — **new**
- `tests/tools/test_jenkins_download_logs.py` — **new**

## WHAT

```python
# tools/jenkins_download_logs.py
DEFAULT_STATUS = "failure,aborted,unstable"

def main(argv: list[str] | None = None) -> int: ...
```

## HOW

- Import the shared helpers from the sibling script the way `tools/mlflow/` does:

  ```python
  # Sibling script in tools/; resolved at runtime via sys.path[0].
  from jenkins_builds import add_selection_args, make_client  # type: ignore[import-not-found]
  ```

  If mypy reports the ignore as unused, drop the ignore comment instead. Also import `JenkinsError` from `mcp_coder.utils.jenkins_operations` and `log_filename` from `mcp_coder.utils.jenkins_operations.builds`.
- Arguments: `add_selection_args(parser, DEFAULT_STATUS)` plus `--outdir` (`Path`, default `.`; help: created with parents if missing, existing files are overwritten).
- Wrappers: copy the step 5 wrappers and replace `jenkins_builds` with `jenkins_download_logs`. Usage line: `[--limit N] [--folder PATH] [--status a,b] [--outdir DIR]`.
- `tests/tools/conftest.py` re-exports the integration fixtures:

  ```python
  """Test configuration for tools tests."""
  from tests.utils.jenkins_operations.integration_fixtures import jenkins_client as jenkins_client
  from tests.utils.jenkins_operations.integration_fixtures import jenkins_test_setup as jenkins_test_setup
  ```

## ALGORITHM

```
main(argv):
    args = parser.parse_args(argv); client = make_client(); if client is None: return 1
    try:
        builds = client.get_recent_builds(limit=args.limit, folder=args.folder, statuses=args.status)
        args.outdir.mkdir(parents=True, exist_ok=True)
        for b in builds:
            path = args.outdir / log_filename(b.job_path, b.number)
            path.write_text(client.get_console_output(b.job_path, b.number), encoding="utf-8"); print(path)
    except JenkinsError as e: print(f"Error: {e}", file=sys.stderr); return 1
    return 0
```

## DATA

Writes one UTF-8 file per selected build to `<outdir>/<log_filename(job_path, number)>` and prints one path per line. Returns 0 on success and 1 on missing config or `JenkinsError`.

## Tests (`tests/tools/test_jenkins_download_logs.py`)

Load the tools the same way as in step 5: put `tools/` on `sys.path`, then `jenkins_builds = importlib.import_module("jenkins_builds")` and `jenkins_download_logs = importlib.import_module("jenkins_download_logs")` (no static imports). Both resolve to the same `sys.modules` entries the tool uses, so monkeypatching `jenkins_builds.*` reaches the code under test. Patch `jenkins_builds.get_jenkins_config` and `jenkins_builds.JenkinsClient`; `make_client` resolves them in the `jenkins_builds` module.

Unit tests (client mocked):
- Default `--status` → `get_recent_builds` receives `statuses=["failure", "aborted", "unstable"]`; `--status failed` → `SystemExit(2)`.
- Two builds → two files with the expected names (`A_B_job_5.txt`) and contents; the stdout lines are the written paths.
- An existing file with the same name is overwritten.
- A missing nested `--outdir` (`tmp_path / "a" / "b"`) is created.
- `get_console_output` raises `JenkinsError` → returns 1.
- Missing config → returns 1, and stderr names the missing variable.

End-to-end test (`@pytest.mark.jenkins_integration`, no mocks; uses `jenkins_client` and `jenkins_test_setup`):

```
parent = test_job.rpartition("/")[0] or None
if not jenkins_client.get_recent_builds(limit=1, folder=parent): pytest.skip("no builds in test_job's folder")
argv = ["--limit", "1", "--status", ",".join(VALID_STATUSES), "--outdir", str(tmp_path)] + (["--folder", parent] if parent else [])
assert jenkins_download_logs.main(argv) == 0
files = list(tmp_path.glob("*.txt")); assert len(files) == 1 and files[0].stat().st_size > 0
```
