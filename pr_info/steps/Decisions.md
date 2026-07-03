# Decisions — Issue #695 plan review

Plan-review round (all items approved before this update; applied as targeted edits).

## install.py env — Option B (single shared env dict)

`session_setup.py` uses ONE shared `build_subprocess_env` dict for all
subprocesses, **including** the `install.py` call, with
`VIRTUAL_ENV=<cwd>/.venv`. Safe because install.py forwards env untouched;
`uv pip install` is pinned via `--python <abs venv python>`, and the only
env-sensitive command (`uv sync`, our `--use-sync` path) targets `<cwd>/.venv`.
Setting `VIRTUAL_ENV=<cwd>/.venv` (not leaking the coordinator venv's) makes
`uv sync` match and avoids uv's "VIRTUAL_ENV does not match" warning.
Invariant: `VIRTUAL_ENV == <cwd>/.venv == target`. Rationale noted in Step 2;
unit test asserting the install.py subprocess env carries the project `.venv`
path added in Step 3.

## Step 5 test coverage — BLOCKER fix

`tests/workflows/vscodeclaude/test_workspace.py` added to the Step 5 port list.
`test_create_startup_script_windows` (asserts script content contains `claude` /
`/implementation_review_supervisor`) and `test_create_startup_script_intervention`
(asserts `INTERVENTION` in content) break under the thin launcher — the launcher
no longer contains that text. The command lives in the spec JSON; the
intervention warning is rendered at runtime by `session_setup.render_banner`.
Both workspace-level tests re-pointed to spec assertions (`commands`,
`is_intervention`); the printed intervention warning is covered by the
`render_banner` test (Step 2) and the intervention-flow test (Step 3).

## Step 5 — end-to-end round-trip test

Added ONE end-to-end `skip_github_install` round-trip chaining the real on-disk
path (`create_startup_script` → `read_session_spec` → `build_install_argv`):
`--skip-overrides` present iff `skip_github_install=True`.

## Step 3 — UTF-8 before banner

Test added asserting `_force_utf8_stdout` (or
`sys.stdout.reconfigure(encoding="utf-8")`) runs before the banner `print`
(guards the emoji-on-cp1252 `UnicodeEncodeError` the issue calls out).

## Step 3 — middle-step warning parity

Middle automated steps still run non-fatal (`check=False`, continue on
non-zero), but now emit `WARNING: Step N encountered an error. Continuing...`
so old-template parity is preserved (no silent swallow). Noted in step + flow
test.

## Step 6 — ci.yml drift-guard comment (doc-only)

The `vscodeclaude-template-install` job comment (~lines 132–166) references the
deleted `templates.py:VENV_SECTION_POSIX` and `_build_github_install_section_posix`.
Updated to point at `session_setup.build_install_argv`. Comment-only — the job
body runs `tools/install.py` directly and does not break.

## Step 2 — banner-title change acknowledged

Old 58-char title truncation and shell-escaping (`_escape_batch_title` / POSIX
quoting) intentionally dropped: banner is now printed by Python (no shell), so
escaping is unnecessary; truncation was cosmetic and is not reproduced.

## summary.md — call-site wording fix

Both `create_startup_script` call sites are in `session_launch.py` (~lines 195
and 450); `session_restart.py` has no direct call. Corrected the
"Unchanged (verified)" note (signature unchanged either way).

## Round 2 — restore in-terminal intervention warning (Finding 1)

Behavior parity: the in-terminal intervention WARNING
(`!! INTERVENTION MODE - Automation may be running elsewhere` / `!! Investigate
manually. No automated analysis will run.`) must be **restored**. Today the
generated startup script prints it right before launching bare `claude`; under
the refactor it is rendered at runtime by `session_setup.py`.

Placement decision: `render_banner` (Step 2) appends the warning for
intervention specs, reusing a template constant `INTERVENTION_WARNING` (Step 4,
kept in Step 6) rather than hardcoding inline — mirroring how the plan reuses
`BANNER_TEMPLATE`. Since `run_session` prints `render_banner(spec)` before
`orchestrate`, the warning shows in the UTF-8-forced terminal before the bare
`claude` launch; no separate print on `orchestrate`'s intervention branch.
The coordinator-console banner and the status-file `Mode: INTERVENTION` line are
out of scope and unchanged.

## Round 2 — intervention render test (Finding 3)

The `render_banner` test (Step 2) and the intervention-flow test (Step 3) assert
that an intervention spec's rendered/printed banner **contains** the
`!! INTERVENTION MODE` warning, and a normal spec's does **not**.

## Round 2 — commands validation now unconditional (Finding 2, note-only)

In the rewritten `create_startup_script`, `commands` list/`str` validation
(raise `ValueError`) runs unconditionally before the intervention branch — a
minor intentional fail-fast change from today, where it only ran on the
non-intervention path. Note-only; kept.

## Informational (no change)

Step 5 is the largest/riskiest step but correctly cannot be split without
leaving the suite red — left as-is.
