# Summary — Fix `uv sync --extra types` uninstalling AutoRunner-provisioned packages

## Problem

Jenkins `implement` runs fail quality checks because two `uv sync` calls target the
same project `.venv`:

1. AutoRunner (`provisionVenv: true`) runs `uv sync --extra dev`, installing 225
   packages including `langchain-core` / `langchain-mcp-adapters`.
2. The coordinator's command template then runs
   `uv sync --project %WORKSPACE%\repo --extra types`. By default `uv sync` removes
   anything not in the requested extra, so it uninstalls the LangChain packages
   AutoRunner just installed.

## Fix

Add `--inexact` to every `uv sync ... --extra types` invocation in the coordinator
command templates. `--inexact` tells uv to install the requested extra without
removing packages already present, so the type-stub sync becomes additive instead
of exact — safe whether or not a prior provisioning step ran.

## Architectural / design changes

None. This is a flag addition to existing shell/batch string constants — no new
abstractions, modules, or control flow. The templates remain standalone literal
strings, consistent with the existing structure of
`command_templates.py` (each workflow template is a self-contained script, by
design, to keep Jenkins step definitions easy to read and diff). No shared
"sync line" constant is introduced, since that would be a refactor beyond this
issue's scope.

## Files touched

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/coordinator/command_templates.py` | Add `--inexact` to all 12 `uv sync ... --extra types` lines (6 Linux + 6 Windows templates) |
| `tests/cli/commands/coordinator/test_command_templates.py` | Update the 8 existing assertions that check for the literal `--extra types` sync line to also require `--inexact` |
| `docs/configuration/config.md` | Update the dependency-architecture diagram and surrounding prose (≈ lines 867, 880, 903) to show `--inexact` and explain that it preserves packages from an earlier provisioning step |

No files are created or deleted; no new folders/modules.

## Steps

1. **step_1.md** — Update tests to require `--inexact`, then add `--inexact` to all
   12 template occurrences (TDD: tests red → implementation → tests green).
2. **step_2.md** — Update `docs/configuration/config.md` to document `--inexact`.

Each step is one commit: tests + implementation (where applicable) + passing
pylint/pytest/mypy checks.
