# Step 2 — New tool `tools/jenkins_download_log.py` (+ `.sh` / `.bat`), tests and docs

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md`.
> Step 1 is done: `tests/tools/conftest.py` provides the `client` fixture and
> `_FULL_CONFIG`. Write the tests in `tests/tools/test_jenkins_download_log.py` first,
> then the tool `tools/jenkins_download_log.py` and its `.sh` / `.bat` wrappers, then the
> doc and config edits listed below. Do not change anything under `src/`. Do not try to set
> the executable bit on the `.sh` file — that is step 3. Run pylint, pytest (fast unit
> tests, `-n auto`) and mypy; all must pass. Produce exactly one commit.

## WHERE

Created:
- `tests/tools/test_jenkins_download_log.py`
- `tools/jenkins_download_log.py`
- `tools/jenkins_download_log.sh`
- `tools/jenkins_download_log.bat`

Modified:
- `docs/repository-setup/internal.md`
- `.claude/CLAUDE.md`
- `.claude/settings.local.json`
- `tools/jenkins_status_check.md`

## 1. Tests first — `tests/tools/test_jenkins_download_log.py`

Header (same import pattern as the sibling test modules):

```python
"""Unit tests for tools/jenkins_download_log.py (JenkinsClient mocked)."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.jenkins_operations import JenkinsError
from tests.tools.conftest import _FULL_CONFIG

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_builds = importlib.import_module("jenkins_builds")
jenkins_download_log = importlib.import_module("jenkins_download_log")
```

Tests (argv is always `[job_path, number, output_file]`):

| Test | Setup | Assertions |
|---|---|---|
| `test_writes_log_and_prints_path(client, tmp_path, capsys)` | `target = tmp_path / "log.txt"`; `client.get_console_output.return_value = "log ✓"` | `main(["A/B/job", "5", str(target)]) == 0`; `client.get_console_output.assert_called_once_with("A/B/job", 5)`; `target.read_text(encoding="utf-8") == "log ✓"`; `capsys.readouterr().out.strip() == str(target)` |
| `test_creates_missing_parent_dirs(client, tmp_path)` | `target = tmp_path / "a" / "b" / "log.txt"` | rc `0`; file content equals the returned text |
| `test_overwrites_existing_file(client, tmp_path)` | `target` pre-written with `"old content that is longer"`; return value `"new"` | rc `0`; content `== "new"` |
| `test_jenkins_error_returns_1_and_writes_nothing(client, tmp_path, capsys)` | `target = tmp_path / "a" / "b" / "log.txt"`; `side_effect = JenkinsError("build not found")` | rc `1`; `"build not found"` in stderr; `not (tmp_path / "a").exists()` |
| `test_output_file_is_directory_returns_1(client, tmp_path, capsys)` | `target = tmp_path / "existing_dir"`; `target.mkdir()` | rc `1`; `"existing_dir"` in stderr. Do **not** assert the exception type (differs by OS) |
| `test_missing_config_returns_1(monkeypatch, tmp_path, capsys)` | patch `jenkins_builds.get_jenkins_config` → `{**_FULL_CONFIG, "username": None}`; patch `jenkins_builds.JenkinsClient` with `client_cls = MagicMock()` | rc `1`; `"JENKINS_USER"` in stderr; `client_cls.assert_not_called()` |
| `test_invalid_number_exits_2(number, tmp_path)` — `@pytest.mark.parametrize("number", ["0", "abc"])` | — | `pytest.raises(SystemExit)`; `exc_info.value.code == 2` |

No `jenkins_integration` test.

## 2. Tool — `tools/jenkins_download_log.py`

### WHAT

```python
def main(argv: list[str] | None = None) -> int: ...
```

Only `main` plus the `if __name__ == "__main__": sys.exit(main())` guard. No helpers.

### HOW

```python
#!/usr/bin/env python3
"""Download the console log of one Jenkins build.

Writes the log as UTF-8 to the given file, creating missing parent directories
and overwriting an existing file, then prints the file path. All Jenkins logic
lives in ``mcp_coder.utils.jenkins_operations``; this script only parses
arguments, writes the file and sets the exit code.

Usage:
    python tools/jenkins_download_log.py <job_path> <number> <output_file>
"""

import argparse
import sys
from pathlib import Path

# Sibling script in tools/; resolved at runtime via sys.path[0].
from jenkins_builds import (  # type: ignore[import-not-found]
    make_client,
    positive_int,
)

from mcp_coder.utils.jenkins_operations import JenkinsError
```

Argparse (description `"Download the console log of one Jenkins build."`):
- `job_path` — help: `full job path from the Jenkins root, e.g. Windows-Agents/Executor`
- `number` — `type=positive_int`, help: `build number`
- `output_file` — `type=Path`, help: `file to write; missing parent directories are created, an existing file is overwritten`

Docstring of `main`: Args `argv`; Returns "Exit code: 0 on success, 1 on configuration,
Jenkins or write errors" (argparse exits with 2 on bad arguments).

### ALGORITHM

```
args = parser.parse_args(argv)            # bad args -> SystemExit(2)
client = make_client(); if None: return 1 # make_client prints missing settings
try: text = client.get_console_output(args.job_path, args.number)
     args.output_file.parent.mkdir(parents=True, exist_ok=True)
     args.output_file.write_text(text, encoding="utf-8")
except JenkinsError as e: print(f"Error: {e}", stderr); return 1
except OSError as e: print(f"Error writing log to '{args.output_file}': {e}", stderr); return 1
print(args.output_file); return 0
```

Fetch happens before `mkdir`, so a Jenkins error leaves no directories. `mkdir` is inside
the `OSError` handler (a parent path that is an existing file makes it raise).

### DATA

Return `int` exit code. Stdout: the output path (as the `Path` given). Stderr: error text.

## 3. Wrappers

`tools/jenkins_download_log.sh` — copy `tools/jenkins_download_logs.sh`, changing only the
usage comment and script name:

```bash
#!/usr/bin/env bash
# Download the console log of one Jenkins build. Usage: tools/jenkins_download_log.sh <job_path> <number> <output_file>
...
exec "$PYTHON" "$SCRIPT_DIR/jenkins_download_log.py" "$@"
```

`tools/jenkins_download_log.bat` — copy `tools/jenkins_download_logs.bat`, same two changes:

```bat
REM Download the console log of one Jenkins build. Usage: tools\jenkins_download_log.bat <job_path> <number> <output_file>
...
"%PYTHON%" "%~dp0jenkins_download_log.py" %*
```

Line endings come from `.gitattributes` via `save_file`; nothing to do.

## 4. Docs and config

### `docs/repository-setup/internal.md`

Add after the `tools/jenkins_download_logs.py` row:

```
| `tools/jenkins_download_log.py` (+ `.bat` / `.sh`) | Download the console log of one Jenkins build, given job path and build number, to a chosen file; no default job |
```

### `.claude/CLAUDE.md` (Jenkins section)

After the "Download console logs" line, add:

```
- Download one build's console log: `tools/jenkins_download_log.sh <job_path> <number> <output_file>`, e.g. `tools/jenkins_download_log.sh Windows-Agents/Executor 2935 .scratch/jenkins_logs/Executor_2935.txt`. No default job. The output path must not be gitignored (e.g. not under `logs/`) — `read_file` refuses gitignored paths; `.scratch/` works, delete it afterwards.
```

Reword the existing line starting "Without `--job`, both default to …" to
"Without `--job`, `jenkins_builds` and `jenkins_download_logs` default to …" (rest unchanged).

### `.claude/settings.local.json`

Insert before `"Bash(tools/jenkins_download_logs.bat:*)"`:

```json
      "Bash(tools/jenkins_download_log.bat:*)",
      "Bash(tools/jenkins_download_log.sh:*)",
```

### `tools/jenkins_status_check.md` — step 4

Replace the sentence "If that doesn't settle it, download the logs: `…jenkins_download_logs.sh…`, then `…jenkins_classify_logs.sh…`." with a two-item list, keeping the "Deciding lines:" list after it:

```
4. **Find the cause** for every issue that needs action. Read the failure comment on the issue first (Category / Stage / Error). If that doesn't settle it, download the logs:
   - **One build:** `tools/jenkins_download_log.sh <job_path> <number> <output_file>`, e.g. `tools/jenkins_download_log.sh Windows-Agents/Executor 2935 .scratch/jenkins_logs/Executor_2935.txt`. From the failure comment's `Build` URL (`…/job/<a>/job/<b>/<n>/`): take the `/job/<name>` segments, URL-decode each once and join them with `/` → `<job_path>`; the trailing number → `<number>`. Same rule as `job_path_from_build_url` in `src/mcp_coder/utils/jenkins_operations/diagnostics.py`; `get_console_output` re-encodes. Read the file directly with `read_file`; don't pass it to `jenkins_classify_logs.sh`, which only reads the `index.csv` written by `jenkins_download_logs.py`. The output path must not be gitignored (e.g. not under `logs/`), because `read_file` refuses gitignored paths; `.scratch/` works and is deleted afterwards.
   - **Many builds:** `tools/jenkins_download_logs.sh --limit N --name-pattern ' - #\d+$' --outdir .scratch/jenkins_logs`, then `tools/jenkins_classify_logs.sh --logdir .scratch/jenkins_logs`.

   Deciding lines:
```

(The existing deciding-lines bullets stay as they are.)

## Checks

- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_pytest_check` with the fast-unit-test marker expression and `-n auto`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_format_code` before the commit

## Commit

`feat(tools): add jenkins_download_log for one build's console log`
