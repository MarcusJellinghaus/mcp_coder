# Summary — #1420 Jenkins tools: download one build's console log by job path and number

## Goal

New tool `tools/jenkins_download_log.py` (+ `.sh` / `.bat`):

```
tools/jenkins_download_log.sh <job_path> <number> <output_file>
```

Downloads the console log of exactly one build, e.g. the build named in a failure
comment's `**Build:** <BUILD_URL>`. Today this needs `jenkins_download_logs.py` with a
name pattern and a full status list.

## Architectural / design changes

- **No library change.** `JenkinsClient.get_console_output(job_path, build_number)`
  (`src/mcp_coder/utils/jenkins_operations/client.py`) already fetches `consoleText`,
  re-encodes URL-encoded segments and produces the 404 / 403 diagnoses.
- **Thin CLI script, same pattern as its siblings.** `tools/` scripts only parse arguments,
  write files and set exit codes; Jenkins logic stays in `mcp_coder.utils.jenkins_operations`.
  The new script imports `make_client` and `positive_int` from the sibling
  `tools/jenkins_builds.py` (resolved via `sys.path[0]`, as `jenkins_download_logs.py` does).
- **Interface:** three required positionals, no flags, no job resolution (no
  `resolve_job` fallback, no config default job).
- **Order of operations:** fetch the log first, then create parent dirs and write. A Jenkins
  error therefore leaves nothing on disk.
- **Exit codes:** `0` success; `1` missing config / `JenkinsError` / `OSError` while writing;
  `2` bad arguments (argparse).
- **Error messages:** `JenkinsError` → `Error: <e>`; `OSError` →
  `Error writing log to '<output_file>': <e>` (new wording, distinct from the sibling's
  `Error writing logs to '<outdir>'`). Both on stderr.
- **Test infrastructure cleanup:** the `client` fixture and `_FULL_CONFIG`, currently
  duplicated in `test_jenkins_builds.py` and `test_jenkins_download_logs.py`, move to the
  existing `tests/tools/conftest.py`. The conftest imports the tool by its bare name
  (`importlib.import_module("jenkins_builds")` after inserting `tools/` into `sys.path`) so
  it patches the same module object the scripts use — `tools.jenkins_builds` would be a
  different module object.
- **Executable bit:** `tools/jenkins_download_log.sh` must be `100755` like the other
  `tools/*.sh`. The implement workflow has no Bash, so the last step only writes a blocked
  marker; a human sets the bit.

## Files

### Created

| File | Purpose |
|---|---|
| `tools/jenkins_download_log.py` | The tool (`main(argv) -> int`) |
| `tools/jenkins_download_log.sh` | Bash wrapper (copy of the `jenkins_download_logs.sh` pattern) |
| `tools/jenkins_download_log.bat` | Windows wrapper (copy of the `jenkins_download_logs.bat` pattern) |
| `tests/tools/test_jenkins_download_log.py` | Unit tests, `JenkinsClient` mocked |

### Modified

| File | Change |
|---|---|
| `tests/tools/conftest.py` | Add `_TOOL_DIR` / `sys.path` block, `jenkins_builds` module ref, `_FULL_CONFIG`, `client` fixture; keep existing re-exports |
| `tests/tools/test_jenkins_builds.py` | Remove local fixture and `_FULL_CONFIG`; import `_FULL_CONFIG` from conftest |
| `tests/tools/test_jenkins_download_logs.py` | Same as above |
| `vulture_whitelist.py` | Comment above `_.fixture_client` points to `tests/tools/conftest.py` |
| `docs/repository-setup/internal.md` | Tools table row |
| `.claude/CLAUDE.md` | Jenkins section: new tool line; reword "both default to" line |
| `.claude/settings.local.json` | Allow `Bash(tools/jenkins_download_log.bat:*)` and `.sh` |
| `tools/jenkins_status_check.md` | Step 4: single-build log, Build URL → arguments |

No changes under `src/`.

## Steps

1. **Shared test fixture** — move the `client` fixture and `_FULL_CONFIG` into
   `tests/tools/conftest.py` (refactor, no behaviour change).
2. **New tool + tests + docs** — `jenkins_download_log.py` / `.sh` / `.bat`, its unit tests,
   docs and permission entries.
3. **Executable bit** — no file changes; write the blocked marker for the human.

## Out of scope

Archived build artifacts (follow-up issue), Build-URL input, integration tests, client
changes.
