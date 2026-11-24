# Summary: scope command-toolkit Bash grants per session; verify flags unused depths (#1451)

## Problem

The four Claude sessions that re-run checks (implement task, its fix turns,
finalisation, CI fix) call `llm_permissions(project_dir, provider)` with
`entry=None`, so they get `Bash(...)` grants for **every** declared action and
depth. The `check_instructions` re-run list comes from
`CommandToolkit.prompt_fragments()`, which also lists every declared step. Depths
that no binding requests (e.g. `check.full`, `test.mutation`, `format.check`)
still get grants and re-run lines. `mcp-coder verify` doesn't flag declared
depths that nothing requests.

## Design (KISS)

### 1. Session grants use the existing `entry` parameter

`llm_permissions(project_dir, provider, entry)` already resolves one binding
entry's requests, including depth fallback. It is used as is:

| Session | Call |
|---|---|
| implement task (`task_processing.py`) | `implement_task` and `implement_final`: two calls, merged in order and deduplicated with `dict.fromkeys` |
| fix turns (`_fix_turn` in `check_loop.py`) | `entry` of the binding being fixed, passed down from `check_and_fix` |
| finalisation (`finalisation.py`) | `"implement_final"` |
| CI fix (`workflow_steps/ci.py`, shared by every `check_and_fix_ci` caller) | `"implement_final"` |

- `llm_permissions` gets no new parameter.
- `entry=None` still means "everything declared".
- `required_mcp_servers` (`mcp_verification.py`) and `toolkit_declares_bash_grants` keep using the union.
- Rebase doesn't change.

### 2. The re-run list is built from the session's grants

`resolve_prompt_slots(text, project_dir, provider, bash_grants)` already
receives the session's grants. When the toolkit declares Bash grants (still
decided over everything declared), the provider is Claude and `bash_grants` is
non-empty, the `check_instructions` value is:

```
RERUN_INTRO + "\n".join(f"- `{grant[len('Bash('):-1]}`" for grant in bash_grants)
```

- A step without a grant (arguments that aren't shell-safe) has no grant, so it is not listed.
- No grants in scope → `""`, as today.
- This needs no change to the `Toolkit` interface and no import of `mcp_coder.toolkits` from `utils`, so the import-linter contract `toolkits_isolation` still holds.
- The same rule fills the injected system prompt (`llm/interface.py` passes the caller's `bash_grants` through). Callers with `bash_grants=None` (create_plan, icoder, the prompt CLI, verify's test prompt) still get `""` for Bash toolkits.
- Toolkits without Bash grants (mcp-tools-py) keep their own `check_instructions` fragment unchanged.
- `RERUN_INTRO` moves from `toolkits/command/toolkit.py` to `utils/prompt_slots.py`. The command toolkit imports it, so the intro text is defined once. `CommandToolkit.prompt_fragments()` output is unchanged.

### 3. `verify`: one row per declared depth

In `cli/commands/verify_toolkit_rows.py`, every request is resolved to the
depth that actually runs (`resolve_depth`). This happens twice:

- `ran`: the normal requests (`commit` counts only while `format_code` is on).
- `ran_any`: `formatting=True`.

Each declared depth gets one row, labelled `action@depth`:

| Case | Row | Toolkits |
|---|---|---|
| in `ran` | ok: `requested by <entries>` (fallback entries included) | all |
| `not can_request(action, depth)` | warning: `no binding can request it; delete it` | command only |
| in `ran_any` but not in `ran` | warning: `unused while format_code is off` | command only |
| otherwise | warning: `not requested by any binding; delete it or add it to a binding` | command only |

- The command toolkit is detected by name: `loaded.name == "command"`.
- Groups are built for the requested actions plus, for the command toolkit, the declared actions.
- `verify()` still runs only for requested actions.
- The existing fallback warning and missing-depth error (`_depth_row`) don't change.
- New helper `can_request(action, depth)` in `utils/toolkit_runner.py` reads the private `_ALLOWED_ACTIONS` / `_FORBIDDEN_REQUESTS` tables. With the current tables, only `format@check` can never be requested.

### 4. Docs

In `docs/configuration/toolkits.md`:

- the npm example drops `check.full`, `test.full`, `test.mutation` and `format.check`;
- the "CI fix (union of all grants)" sentence becomes the per-session scope.

## Files

Modified:

- `src/mcp_coder/utils/prompt_slots.py`: `RERUN_INTRO`, re-run list from grants
- `src/mcp_coder/toolkits/command/toolkit.py`: import `RERUN_INTRO` instead of defining it
- `src/mcp_coder/workflows/implement/task_processing.py`: two-entry grants
- `src/mcp_coder/workflows/implement/finalisation.py`: `implement_final` grants
- `src/mcp_coder/workflow_steps/ci.py`: `implement_final` grants
- `src/mcp_coder/workflows/implement/check_loop.py`: `_fix_turn(entry=...)`
- `src/mcp_coder/utils/toolkit_runner.py`: `can_request`
- `src/mcp_coder/cli/commands/verify_toolkit_rows.py`: declared-depth rows
- `docs/configuration/toolkits.md`
- Tests:
  - `tests/utils/test_prompt_slots.py`
  - `tests/llm/test_interface_prompt_slots.py`
  - `tests/utils/test_toolkit_permissions.py`
  - `tests/utils/test_toolkit_runner.py`
  - `tests/workflows/implement/test_task_processing_bash_grants.py`
  - `tests/workflows/implement/test_finalisation.py`
  - `tests/workflows/implement/test_check_loop_fix_turns.py`
  - `tests/workflows/implement/test_check_loop.py` (if it asserts `_fix_turn` arguments)
  - `tests/workflow_steps/test_ci_bash_grants.py`
  - `tests/cli/commands/test_verify_toolkit_rows.py`

No new modules or packages.

## Steps

1. Re-run list built from the session's grants (`prompt_slots.py`, `RERUN_INTRO` move).
2. Per-session grant scope in the four sessions.
3. `verify` rows for declared depths (`can_request` + `verify_toolkit_rows.py`).
4. Docs in `docs/configuration/toolkits.md`.
