# Step 3 — `session_setup.py` orchestration + `main`

Read `pr_info/steps/summary.md` first. This step wires the Step-2 pure builders
into the actual run flow: banner → env → `install.py` → session-ID capture →
step chaining → interactive/intervention `claude`. Adds the `python -m` entry
point. `subprocess` calls are the only impure part and are mocked in tests.

## WHERE
- `src/mcp_coder/workflows/vscodeclaude/session_setup.py` (extend)
- `tests/workflows/vscodeclaude/test_session_setup_flow.py` (new)

## WHAT
```python
def _force_utf8_stdout() -> None
def run_first_step(spec, command, env, cwd) -> str        # captured session id
def orchestrate(spec: SessionSpec, cwd: Path, env: dict[str, str]) -> None
def run_session(cwd: Path) -> None
def main(argv: list[str] | None = None) -> None

if __name__ == "__main__":
    main()
```

## HOW
- Use `subprocess.run` (module-level `import subprocess`) so tests can
  `monkeypatch`/`patch` a single symbol and assert on ordered `argv` + `env`.
- First step: `capture_output=True, text=True`; parse `stdout.strip()` as the
  session id; raise `RuntimeError` if empty.
- Middle steps: run **without** `check` (non-fatal — continue on non-zero).
  On a non-zero return, emit a warning (`log`/`print`
  `WARNING: Step N encountered an error. Continuing...`) so the old-template
  parity is preserved — do **not** silently swallow the failure.
- Provisioning + interactive/intervention `claude`: inherit stdio (no capture);
  provisioning uses `check=True`. All calls pass `env=env, cwd=str(cwd)`.
- `main` forces UTF-8 stdout first, then wraps `run_session` in try/except:
  on `Exception` print traceback, `input("Session failed (Enter to close)...")`,
  `sys.exit(0)` (already prompted — avoid launcher double-prompt). Success path
  returns normally (exit 0, no prompt).
- **Intervention warning.** No separate print is needed on `orchestrate`'s
  intervention branch: `run_session` already prints `render_banner(spec)`, which
  (Step 2) appends the `!! INTERVENTION MODE ...` warning for intervention specs.
  So the warning is emitted in the UTF-8-forced terminal before the bare
  `claude` launch — restoring parity with the old `INTERVENTION_SCRIPT_*`
  templates.

## ALGORITHM
```
orchestrate(spec, cwd, env):
    if spec.is_intervention:
        run(build_claude_argv(spec)); return
    cmds = spec.commands
    if not cmds: return                                   # 0-cmd: venv only
    if len(cmds) == 1:
        run(build_claude_argv(spec, prompt=f"{cmds[0]} {spec.issue_number}")); return
    sid = run_first_step(spec, cmds[0], env, cwd)          # step 1 capture
    for i, cmd in enumerate(cmds[1:-1], start=2):
        r = run(build_step_argv(spec, cmd, session_id=sid, issue_number=None))  # non-fatal
        if r.returncode != 0: warn(f"Step {i} encountered an error. Continuing...")
    run(build_claude_argv(spec, prompt=cmds[-1], session_id=sid))           # last

run_session(cwd):
    spec = read_session_spec(cwd); print(render_banner(spec))
    env = build_subprocess_env(spec, cwd)
    run(build_install_argv(spec, cwd), check=True)         # provision project venv
    orchestrate(spec, cwd, env)
```

## DATA
- `run_first_step` -> `str` session id (non-empty).
- others -> `None`. `main` may `SystemExit(0)`.

## TESTS (write first; patch `session_setup.subprocess.run`)
- Intervention: single bare-`claude` call, no `mcp-coder prompt`; the printed
  banner includes the `!! INTERVENTION MODE` warning (assert on captured stdout),
  and a non-intervention flow's banner does not.
- 0 commands: only the `install.py` call, no `claude`/`prompt`.
- 1 command: `install.py` then one interactive `claude` with `"<cmd> <issue>"`.
- Multi (3 cmds): order = install → first prompt (session-id, captured) → middle
  prompt (`--session-id`) → `claude --resume`. Assert the captured id threads
  into middle + last argv.
- Session-id capture: stub first-step stdout `"abc123\n"` => id `"abc123"`;
  empty stdout raises.
- Middle-step non-fatal: middle `run` returns non-zero → flow still reaches the
  last `claude` call **and** a warning is emitted (assert the
  `Step N encountered an error. Continuing...` warning fires; capture log/stdout
  or patch the `warn`/`log` symbol).
- `main` graceful exit: `read_session_spec` raises → `SystemExit` code 0 and
  `input` was called once (patch `builtins.input`).
- Every non-capture call receives `env=` containing the four MCP vars and
  `cwd=str(cwd)`.
- `install.py` env: the env passed to the `install.py` subprocess carries
  `VIRTUAL_ENV` equal to the project `.venv` path (`cwd/.venv`) — confirms the
  shared-env / Option-B invariant end-to-end.
- UTF-8 before banner: `main` forces UTF-8 stdout **before** the banner prints —
  assert `_force_utf8_stdout` (or `sys.stdout.reconfigure(encoding="utf-8")`) is
  invoked before the banner `print` (guards the emoji-on-cp1252
  `UnicodeEncodeError`).

## LLM PROMPT
> Implement Step 3 from `pr_info/steps/step_3.md` (context in
> `pr_info/steps/summary.md`). Extend
> `src/mcp_coder/workflows/vscodeclaude/session_setup.py` with `orchestrate`,
> `run_first_step`, `run_session`, `_force_utf8_stdout`, `main`, and the
> `__main__` guard, reusing the Step-2 builders. Write
> `tests/workflows/vscodeclaude/test_session_setup_flow.py` first, patching
> `session_setup.subprocess.run` and asserting ordered argv, env propagation,
> session-id threading, non-fatal middle steps, and `main`'s graceful exit-0.
> Use MCP workspace tools. Run pylint, pytest (`-n auto` + standard exclusions),
> mypy after each edit; fix all. One commit.
