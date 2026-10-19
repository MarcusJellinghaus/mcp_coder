
# Summary — Remove `uv sync --inexact --extra types` from coordinator templates

## Problem

The Jenkins coordinator's generated `command.bat` / shell script provisions the
target repo's venv via `mcp-coder install --use-sync`, which honors
`[tool.mcp-coder.install-from-github]` overrides (installing mcp-coder's own
sibling packages from git). The very next step in every generated script,
`uv sync --inexact --extra types`, re-resolves the lockfile and reverts those
git-sourced packages back to their PyPI-pinned versions — `--inexact` only
stops uv from *removing* extra packages, it does not preserve version pins
that differ from the lockfile.

## Fix

Delete the type-stub sync step from every coordinator command template
(Windows and Linux/Docker, 8 templates each = 16 occurrences). Type stubs
are no longer installed by a separate per-run step; they flow solely through
the target repo's own `[tool.mcp-coder.install] extras` setting, consumed by
`mcp-coder install` in the same pass that applies `install-from-github`
overrides. A target repo that wants type stubs in CI must list a `types`
extra (or an extra that includes it) in its own `pyproject.toml` — that is
the target repo's configuration responsibility, not something this change
audits.

## Architectural / design changes

- **No new abstractions, modules, or code paths.** This is a deletion of a
  redundant provisioning step from plain string constants, plus a doc
  correction. The two-environment model (execution venv vs. project venv)
  is unchanged; only the *mechanism* that populates the project venv's type
  stubs changes — from "two separate steps that can fight each other" to
  "one step (`mcp-coder install`) that is the single source of truth".
- **Test coverage inverts polarity**: tests that asserted the step's
  *presence* on 4/8 templates per platform are replaced with tests
  asserting its *absence* on all 8/8 templates per platform.
- **`vscodeclaude` launcher is untouched** — confirmed not affected by this
  bug; already the target pattern (single `mcp-coder install` call, no
  second sync step).

## Files created or modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Remove the type-stub sync step from all 8 Windows and all 8 Linux template constants |
| `tests/cli/commands/coordinator/test_command_templates.py` | Replace `TestLinuxTemplatesUseTypesExtra` / `TestWindowsTemplatesInstallTypeStubs` with absence assertions covering all 8 templates per platform (16 assertions total) |
| `docs/configuration/config.md` | Rewrite "Test Command Script" sample/narrative and "Why Type Stubs Need Separate Installation" section to describe the single-step mechanism |

No files are created; no files are deleted; no new symbols are introduced.

## Steps

1. **step_1.md** — Remove the sync step from `command_templates.py`; invert and extend the template tests. One commit (tests + implementation).
2. **step_2.md** — Rewrite the two affected sections of `docs/configuration/config.md`. One commit (docs only).
