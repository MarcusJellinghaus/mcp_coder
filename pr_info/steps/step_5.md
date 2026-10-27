# Step 5 — `jenkins_builds` tool, wrappers and tests

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement **Step 5** exactly as described in `pr_info/steps/step_5.md`.
> Use TDD: write `tests/tools/test_jenkins_builds.py` first (client mocked), then `tools/jenkins_builds.py` and the `.bat` / `.sh` wrappers.
> Run pylint, the fast pytest set and mypy; all must pass. Then run the formatter. Stage the `.sh` with `git add --chmod=+x tools/jenkins_builds.sh`, then make one commit.

## WHERE

- `tools/jenkins_builds.py` — **new**
- `tools/jenkins_builds.bat` — **new**
- `tools/jenkins_builds.sh` — **new**, committed executable
- `tests/tools/test_jenkins_builds.py` — **new**

## WHAT

```python
# tools/jenkins_builds.py
def parse_statuses(value: str) -> list[str]: ...                 # argparse `type=`
def add_selection_args(parser: argparse.ArgumentParser, default_status: str | None) -> None: ...
def make_client() -> JenkinsClient | None: ...                   # None → caller exits 1
def format_table(builds: list[BuildInfo]) -> str: ...
def main(argv: list[str] | None = None) -> int: ...
```

The tool contains only argparse, output formatting and exit codes; all Jenkins logic is in `jenkins_operations`. `add_selection_args` and `make_client` are also imported by `jenkins_download_logs.py` in step 6.

## HOW

- Imports:
  - `from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsClient, JenkinsError`
  - `from mcp_coder.utils.jenkins_operations.builds import VALID_STATUSES, validate_statuses`
  - `from mcp_coder.utils.jenkins_operations.client import get_jenkins_config`
- `add_selection_args` adds:
  - `--limit` (`int`, default 100). Help: newest N builds across all jobs, default 100; values above 100 use `allBuilds` and may be slow on large servers.
  - `--folder` (default `None`). Help: full folder path from the Jenkins root; default is the whole server.
  - `--status` (`type=parse_statuses`, `default=default_status`). Help: a comma-separated list of the `VALID_STATUSES` values, plus the default (all statuses when `None`).

  argparse applies `type` to string defaults, so step 6's default `"failure,aborted,unstable"` is parsed as well.
- `make_client`:
  - Read `get_jenkins_config()` and map `server_url → JENKINS_URL`, `username → JENKINS_USER`, `api_token → JENKINS_TOKEN`.
  - If any value is `None`, print `Jenkins not configured: missing JENKINS_URL, ...` (only the missing ones) plus a pointer to `~/.mcp_coder/config.toml [jenkins]` to stderr, and return `None`.
- Every script entry point ends with `if __name__ == "__main__": sys.exit(main())`.

## ALGORITHM

```
parse_statuses(value):
    statuses = [s.strip().lower() for s in value.split(",") if s.strip()]
    try: validate_statuses(statuses) except ValueError as e: raise argparse.ArgumentTypeError(str(e)) from e
    return statuses
main(argv):
    args = parser.parse_args(argv); client = make_client(); if client is None: return 1
    try: builds = client.get_recent_builds(limit=args.limit, folder=args.folder, statuses=args.status)
    except JenkinsError as e: print(f"Error: {e}", file=sys.stderr); return 1
    print(format_table(builds) if builds else "No builds found."); return 0
format_table: header TIME/STATUS/FOLDER/JOB/BUILD; time = b.timestamp.astimezone().strftime("%Y-%m-%d %H:%M"); columns ljust to max width
```

## DATA

`format_table` returns one header line plus one line per build, in the order `get_recent_builds` returned them. The build number is the last column. Names are shown exactly as Jenkins returns them (`%2F` kept).

## Wrappers

`.sh`:

```bash
#!/usr/bin/env bash
# List recent Jenkins builds. Usage: tools/jenkins_builds.sh [--limit N] [--folder PATH] [--status a,b]
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/../.venv/Scripts/python.exe"
[ -x "$PYTHON" ] || PYTHON="$SCRIPT_DIR/../.venv/bin/python"
if [ ! -x "$PYTHON" ]; then
    echo "ERROR: project venv Python not found (expected $SCRIPT_DIR/../.venv/Scripts/python.exe or $SCRIPT_DIR/../.venv/bin/python)" >&2
    exit 1
fi
exec "$PYTHON" "$SCRIPT_DIR/jenkins_builds.py" "$@"
```

`.bat` (uses `goto` rather than a parenthesised block, so paths containing `)` are safe):

```bat
@echo off
REM List recent Jenkins builds. Usage: tools\jenkins_builds.bat [--limit N] [--folder PATH] [--status a,b]
set "PYTHON=%~dp0..\.venv\Scripts\python.exe"
if not exist "%PYTHON%" goto novenv
"%PYTHON%" "%~dp0jenkins_builds.py" %*
exit /b %ERRORLEVEL%
:novenv
echo ERROR: project venv Python not found: %PYTHON% 1>&2
exit /b 1
```

## Tests (`tests/tools/test_jenkins_builds.py`)

- Insert `tools/` on `sys.path` (guarded by `if str(_TOOL_DIR) not in sys.path`), then load the tool with `jenkins_builds = importlib.import_module("jenkins_builds")`. Do not use a static `import jenkins_builds`: pylint (E0401) cannot resolve it and ruff flags it as E402.
- Use `monkeypatch` on `jenkins_builds.get_jenkins_config` and `jenkins_builds.JenkinsClient` (a `MagicMock` class whose instance has `get_recent_builds`).

Cases:
- Parsing: defaults (`limit=100`, `folder=None`, `status=None`); `--status failure,ABORTED` → `["failure", "aborted"]`; `--status failed` → `SystemExit(2)` with every valid value in stderr (`capsys`).
- `--help` output names every status and mentions that large limits may be slow.
- `main` passes `limit`, `folder` and `statuses` through to `get_recent_builds`.
- Table output: header plus rows; the time is shown as local `YYYY-MM-DD HH:MM` (compute the expected value with `.astimezone()` in the test); folder, job and number appear; empty result → `No builds found.`
- `get_recent_builds` raises `JenkinsError` → returns 1 and the message is on stderr.
- Config with `api_token=None` → returns 1, stderr names `JENKINS_TOKEN`, and the client is never constructed.
