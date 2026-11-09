# Step 2 — `CommandToolkit.describe` and `run` with the parsers

Read `pr_info/steps/summary.md` first. Spec: issue #1196, Scope 4, 5, 6, 7.
Depends on Step 1 (`parse_config`).

## LLM prompt

> Implement Step 2 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_2.md`: add `CommandToolkit` with `describe()` and `run()`,
> including the `exit-code` and `junit` parsers, in
> `mcp_coder.toolkits.command.toolkit` (TDD — tests first). `verify`,
> `prompt_fragments` and registration come in Step 3. Run the code-quality
> checks from CLAUDE.md and make exactly one commit.

## WHERE

- Create `src/mcp_coder/toolkits/command/toolkit.py`.
- `src/mcp_coder/toolkits/command/__init__.py`: export `CommandToolkit`.
- Create `tests/toolkits/command/test_toolkit_run.py`.
- `tests/conftest.py`: add the `fake_npm` fixture (see Tests) so Step 6's
  rebase test can reuse it without a cross-package test import.

Imports: `mcp_coder.utils.toolkit` (`ActionRequest`, `ActionResult`, `Finding`,
`Toolkit`, `ToolkitInfo`), `mcp_coder.utils.subprocess_runner`
(`execute_command`), stdlib `shutil`, `os`, `xml.etree.ElementTree`, `logging`.

## WHAT

```python
_SEVERITY = {"skipped": 0, "ok": 1, "findings": 2, "error": 3}
_TAIL_LINES = 200

class CommandToolkit(Toolkit):
    def describe(self) -> ToolkitInfo: ...
    def run(self, request: ActionRequest) -> ActionResult: ...

def _resolve_exe(argv0: str, project_dir: Path) -> str | None: ...
def _run_step(step: Step, project_dir: Path) -> ActionResult: ...
def _junit_findings(path: Path) -> list[Finding] | str: ...  # str = error message
def _fallback_finding(step: Step) -> Finding: ...
def _tail(stdout: str, stderr: str) -> str: ...
def _merge(results: list[ActionResult]) -> ActionResult: ...
```

## HOW

`describe()`:
- `parsed = parse_config(self.config)`;
  `actions = {a: list(depths) for a, depths in parsed.steps.items()}` (config order);
- `params_schema = {"type": "object", "properties": {}, "additionalProperties": False}`;
- `llm_permissions = {}` if `parsed.global_errors()`; else
  `{a: {d: [s.grant for s in steps if s.grant]}}`.
- Never raises.

`run()`:
```
parsed = parse_config(self.config)
if parsed.global_errors(): return error "command toolkit config: <messages>"
steps = parsed.steps.get(action, {}).get(depth); None -> error "<action>@<depth> not declared"
if parsed.errors_for(action, depth): return error naming them
results = [_run_step(s, project_dir) for s in steps]
return _merge(results)
```

`_resolve_exe`: if `"/" in argv0 or os.sep in argv0` → `shutil.which(str(project_dir / argv0))`,
else `shutil.which(argv0)`.

`_run_step`:
```
exe = _resolve_exe(argv[0]); None -> error "<label>: '<argv0>' not found"
if junit: (project_dir / report).unlink(missing_ok=True)
res = execute_command([exe, *argv[1:]], cwd=str(project_dir), timeout_seconds=step.timeout)
if res.timed_out: error, fix_text = f"{label}: timed out after {timeout} s"   # no partial output
if res.execution_error: error with the message
status = step.exit_codes.get(res.return_code, "error"); output = _tail(res.stdout, res.stderr)
findings only when status == "findings": junit -> parse (str -> error), [] -> fallback; exit-code -> fallback + log degraded
fix_text (findings/error): f"{label}\n" + junit messages (if any) + output
```

- `_fallback_finding`: `Finding(key=step.label, message=f"{label} failed")` — no
  action/depth prefix. Log once per `run` call at INFO: "exit-code parser: rebase
  regression detection is degraded for <label>".
- `_junit_findings`: parse with
  `ElementTree.parse(path)  # noqa: S314  # nosec B314 — report written locally by the project's own test tool`
  (and `# noqa: S405` on the import). One `Finding(key=f"{classname}::{name}",
  message=<failure/error message attr or text>)` per `testcase` with a
  `failure` or `error` child. Missing or unparsable file → error string.
- `_tail`: `"\n".join((stdout + "\n" + stderr).strip().splitlines()[-200:])`.
- `_merge`: status = max by `_SEVERITY`; findings concatenated; `fix_text` = non-empty
  step fix texts joined by `"\n\n"`; summary = one line per step (`label: status`).
  If the worst status is `ok`/`skipped`, pass no findings (ActionResult validates this).

## DATA

`ActionResult(status, summary, findings, fix_text, raw)`; `raw` = combined
untruncated output of the steps.

## Tests (`tests/toolkits/command/test_toolkit_run.py`)

Construct `CommandToolkit(config)` directly. Steps run small Python scripts
written to `tmp_path/scripts/`, started through a launcher named `fakenpm` in
`tmp_path/bin/` (the `fake_npm` fixture writes `fakenpm.cmd` calling `"<sys.executable>"
"%~dp0..\scripts\%1.py"` on Windows, or an executable `fakenpm` with a
`#!<sys.executable>` shebang dispatching to `scripts/<arg>.py` on POSIX) and
prepends `bin/` to `PATH` via `monkeypatch.setenv`. argv is then shell-safe,
e.g. `["fakenpm", "lint"]`, and `shutil.which("fakenpm")` resolves on both
(verified on Windows / Python 3.11: PATH lookup applies PATHEXT; a path with a
directory part and no extension does not).
- Project-relative `argv[0]`: patch `mcp_coder.toolkits.command.toolkit.shutil.which`
  and assert `_resolve_exe("tools/lint", project_dir)` passes
  `str(project_dir / "tools/lint")`; a bare name is passed unchanged.
- `describe`: actions/depths in config order; grants; empty under `"none"` and
  under a global error; depth with only malformed steps still declared.
- exit 0 → `ok`; exit 1 → `findings` with one finding keyed by `name` (and by
  joined argv when no name); unmapped exit 3 → `error`; custom `exit_codes`.
- Worst-status merge across two steps; findings concatenated; `skipped` < `ok`.
- Timeout (`timeout = 1`, script sleeps) → `error`, `fix_text` is label + timeout only.
- `execution_error` (monkeypatched `execute_command`) → `error`, not `findings`.
- `argv[0]` not found → `error`.
- junit: two failed cases → two findings `cls::name`, messages first in `fix_text`;
  stale report deleted before the run (script exits 1 without writing → `error`);
  report with no failed cases → fallback finding; exit 0 ignores the report.
- Malformed step in requested depth → `error`; other depths still run.
- Non-shell-safe argv element (e.g. `"a b"` or `"a,b"`) under `"bash"` is not
  malformed: the step runs and returns `ok` / `findings` (not `error`), and its
  `grant is None`.
- Global config error → every request `error`; undeclared action/depth → `error`.
- `fix_text` capped at the last 200 lines.
