# I1.2 — Self-invocation guard (`disable-model-invocation`) — Implementation Summary

**Issue:** #1040 (part of epic #1038, design ref #1037 §3)
**Scope:** langchain / TUI provider only.

## Nature of this work

This is a **verify + lock-in + document** issue, **not** "build a new guard."
The security boundary already holds *structurally*: a model-emitted `/skill`
never routes into command dispatch. There is exactly one production path from
input to dispatch, and model output flows through a separate, one-directional
render path that never re-parses text as a command.

The job is to make that boundary **explicit, tested, and documented** so a
future change (e.g. M2 skill frames overriding a user `never` policy) cannot
silently break it. **No new production behaviour is added.** The production
edits are documentation only (a module docstring, two marker/field comments).

## Verified facts (as of implementation)

- **Single dispatch call site.** `\.dispatch(` matches exactly one line in
  `src/**`: `AppCore.handle_input` at `app_core.py` (`self._registry.dispatch(text)`).
  The `def dispatch` *definition* (`command_registry.py`) has no leading `.`;
  `dispatch_workflow` (`cli/commands/coordinator/core.py`) is a differently
  named function. A precise `\.dispatch\(` call-site regex therefore excludes
  both automatically — no explicit path-exclusion machinery is needed.
- **Human path:** `InputArea` posts `InputSubmitted` only from `on_key`
  (Enter keypress) → `ICoderApp.on_input_area_input_submitted` (sole caller of
  `handle_input`) → `AppCore.handle_input` → `registry.dispatch`.
- **Model/render path:** `AppCore.stream_llm` → `ICoderApp._stream_llm` worker
  → `call_from_thread(self._handle_stream_event, …)` → `StreamEventRenderer` →
  `OutputLog`. This path **never references the registry**. The replay path
  (`ui/replay.py`) also calls `_handle_stream_event(...)` directly and is
  covered by the same invariant.
- **`InputSubmitted(` construction** appears in `src/**` only inside
  `input_area.py` (the class definition and the single `post_message` site).
- **`disable_model_invocation`** is parsed (`skills.py` field def + loader) but
  never read in production — inert today.
- **`user-invocable: false`** is already honoured: such skills are dropped in
  `load_skills`, so they never reach `register_skill_commands` and are never
  registered as commands.

## Architectural / design changes

There is **no change to runtime architecture or data flow.** The boundary is
locked in by:

1. **Two source-search regression tests** that assert the structural
   invariants directly against `src/**`:
   - exactly **one** `.dispatch(` call site, in `app_core.py` (the load-bearing
     assertion — a future second dispatch site, e.g. routing model output into
     dispatch, breaks this test);
   - `InputSubmitted(` constructed only in `input_area.py` (no production code
     posts the submit message outside the human keypress handler).
2. **Behavioural tests** confirming the two sides of the boundary: user-typed
   `/skill` dispatches and invokes the skill; model-shaped `/skill` text driven
   through the render path (`_handle_stream_event`) renders as plain text and
   never calls `dispatch`.
3. **A registry-level test** that a `user-invocable: false` skill is absent
   from the registry.
4. **Inline documentation** co-located with the code it protects:
   - a **module docstring** boundary note in `app_core.py` (the consolidated
     threat model is owned by I5.6/#1056 — not duplicated here);
   - a **marker comment** at the single `registry.dispatch` call site explaining
     why there must be exactly one;
   - a **field doc-note** at `disable_model_invocation` in `skills.py` stating
     it is structurally satisfied and must **not** gain a runtime reader that
     skips command registration.

The `disable_model_invocation` flag keeps being parsed (Claude-format
fidelity) but is deliberately left unread — documented, not dead.

## Design simplifications (KISS)

- **Regex over AST** for the source-search tests; a precise `\.dispatch\(`
  pattern needs no exclusion lists.
- **`InputSubmitted` "Enter-only" check is a source search**, not a Textual
  pilot — matches the reworded observable ("no production code posts
  `InputSubmitted`" outside `input_area.py`) with no keypress harness.
- **One pilot test** covers the model→render negative case; only this test
  needs the Textual harness.
- Behavioural tests reuse existing fixtures (`app_core`, `make_icoder_app`) and
  live beside sibling tests in existing files.

## Files created / modified

### Created
- `pr_info/steps/summary.md` (this file)
- `pr_info/steps/step_1.md` … `pr_info/steps/step_4.md`
- `tests/icoder/test_self_invocation_guard.py` — source-search invariant tests
  (Steps 1 & 2)

### Modified
- `src/mcp_coder/icoder/core/app_core.py` — module docstring boundary note;
  marker comment at the `registry.dispatch` call site (Step 1)
- `src/mcp_coder/icoder/ui/widgets/input_area.py` — marker comment at the
  `InputSubmitted` post site (Step 2)
- `tests/icoder/test_app_core.py` — user-typed `/skill` dispatch test (Step 3)
- `tests/icoder/test_app_pilot.py` — model-stream-never-dispatches pilot test
  (Step 3)
- `tests/icoder/test_skills.py` — `user-invocable: false` absent-from-registry
  test (Step 4)
- `src/mcp_coder/icoder/skills.py` — field doc-note on
  `disable_model_invocation` (Step 4)

## Step → acceptance-criteria map

| Step | Deliverable | ACs |
|------|-------------|-----|
| 1 | Single-dispatch-site source test + marker comment + module docstring note | AC3 (primary), AC6 (boundary doc), AC7 |
| 2 | `InputSubmitted` post-site source test + marker comment | AC4 |
| 3 | User-typed `/skill` dispatches (unit) + model-stream never dispatches (pilot) | AC1, AC2, AC3 (supporting) |
| 4 | `user-invocable: false` absent from registry + flag doc-note | AC5, AC6 (flag) |

## Quality gates (run after every step)

Per `.claude/CLAUDE.md`, after each edit run all three MCP checks and fix
before proceeding:

- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` with
  `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
- `mcp__tools-py__run_mypy_check`

Each step is exactly one commit: tests + doc edits + all checks passing.
Run `./tools/format_all.sh` (black + isort) before committing.
