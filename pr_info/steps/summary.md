# I3.3 — Reactive approval modal + scopes + persist write-back (#1046)

Implementation summary for issue **#1046**, part of epic **#1038**, design reference **#1037**
(§5, §8.2, §8.3). Depends on I3.2 (**#1045**, landed) and on the cross-layer precedence fix
(**#1154**, rescoped to the narrow `personal_bit` — step 1 delivers it in full, so this PR closes
it).

**Step 1 satisfies #1154 completely.** The narrow `personal_bit` is #1154's final semantic, not a
stopgap: hoisting the whole `_LAYER_ORDER` would let a repo-committed `"allow"` silently override
the user's global `"ask"` at equal specificity, so the `user` ↔ `project` direction is a recorded
won't-fix on #1154.

## Goal

When an `ask`-gated MCP tool call parks on a human decision, render a Claude-Code-style modal
showing the tool and its arguments, and apply the scope the user picks: `once` (nothing stored),
`session` (in-memory `runtime` rule), or `persist` (minimal-diff JSONC write-back to
`.icoder/settings.local.json`, plus the mirrored runtime rule).

## What already exists (consumed, not authored)

| Piece | Location | Role |
|---|---|---|
| `ApprovalDecision` | `permissions/approval.py` | Frozen `(outcome, scope, reason)`; rejects `deny` + durable scope |
| `ApprovalEngine` | `permissions/approval.py` | Future registry, `approval_request` emit, `resolve_pending`, `cancel_all` |
| Runtime-rule store | `permissions/gateway.py::add_runtime_rule` | Rebinds the frozen `PermissionConfig` with one extra rule |
| UI delegators | `core/app_core.py` | `resolve_pending`, `cancel_pending_approvals`, `add_runtime_rule` |
| Replay exclusion | `llm/types.py::TRANSIENT_EVENT_TYPES` | `approval_request` is never persisted or replayed |
| Args block shape | `ui/widgets/detail_modal.py::_format_args` | Layout precedent only — **not reused**: it truncates long single-line values (see the KISS table) |

## Architectural / design changes

### 1. Resolver precedence: personal-layer bit moves above policy rank (step 1, issue #1154)

`_rule_sort_key` currently ranks `(specificity, policy.rank, layer, -index)`. Because
`Policy.rank` sits above `_LAYER_ORDER`, a persisted `local` `allow` loses to an authored
`project` `ask` at equal specificity — the persisted grant is inert and the user is re-prompted
every launch. The key becomes:

```
(specificity, never_bit, personal_bit, policy.rank, layer, -index)
```

Two bits are hoisted above `Policy.rank`; `_LAYER_ORDER` itself stays where it is.

- `never_bit` keeps the change fail-closed: without it a `local` `allow` could shadow a `project`
  `deny`.
- `personal_bit` (`local`/`runtime` = 1, `user`/`project` = 0) is what lifts a persisted or
  session grant over an authored `ask`. Hoisting the whole `_LAYER_ORDER` instead would also flip
  `user` ↔ `project`, letting a repo-committed `"allow"` silently override the user's global
  `"ask"` — a widening #1046 does not need, since it only ever writes `local` and `runtime`.

Specificity stays primary, so §5's authored carve-out (a more-specific `always` beats a broader
`never`) survives, and `_LAYER_ORDER` still breaks ties inside each group (`runtime` over `local`,
`project` over `user`). #1045's R14 runtime partition is structurally unchanged and inherits the
new key.

### 2. Scope side-effects are applied on the UI thread, by the UI

The `permissions_leaf_isolation` contract forbids `icoder.permissions` a Textual handle, so the
engine cannot own the writes. Both scope side-effects therefore run inline in the modal's dismiss
callback, **before** `resolve_pending`:

```
guard    → parse_matcher(tool_name); on failure grant nothing and write nothing
session  → AppCore.add_runtime_rule(Rule(matcher, ALWAYS, "runtime"))
persist  → persist.write_rule(...) on disk  AND  the same runtime rule
then     → AppCore.resolve_pending(approval_id, decision)   # always, in every branch
```

The guard runs first because `write_rule` validates nothing and `loader._load_layer` is per-layer
atomic: one token `parse_matcher` rejects would fail the whole `local` layer on the next launch and
degrade the config fail-closed.

This modal never touches the cross-thread Future. It is pushed with
`push_screen(screen, callback)` — never `push_screen_wait`, which would wedge the consumer thread
permanently, since `_handle_stream_event` runs under `call_from_thread` and both streaming
timeouts are suspended while an approval is pending.

### 3. A new leaf writer module for comment-preserving JSONC edits

`permissions/persist.py` is authored here because `loader._strip_jsonc` is a destructive stripper
with no offset mapping. A JSON round-trip is rejected: comment preservation is a hard requirement.
The module rests on **one** primitive — a span tokenizer over the JSONC text, modelled on
`_strip_jsonc`'s string/escape state machine but yielding `(kind, start, end)` spans instead of a
stripped copy. Everything else slices the original text. `_strip_jsonc` is still reused as a
*parser* (to learn what the file contains); only the *locator* is new.

Persist always targets the gitignored `<project_dir>/.icoder/settings.local.json`: a personal
"remember this" must never mutate a committed, team-shared config. The writer needs no
`PermissionConfig` handle and no provenance lookup — it rewrites exactly one file whose path it
already knows. This supersedes design §5's provenance-based write-back for the runtime persist;
§5 remains correct for the I5.2 convert/merge CLI.

### 4. `action_cancel_stream` moves down to `StreamViewApp`

The dismiss callback lives in `ui/stream_view.py` and must call `action_cancel_stream()` on the
`None` branch. The method only touches `_cancel_event` and `_core`, both already `StreamViewApp`
members, so it moves down as a pure move. `ICoderApp.BINDINGS` resolves it by name and is
unaffected. Inlining the two statements instead would give cancellation two implementations that
can drift.

### 5. What is deliberately *not* built

- **No queue and no lock.** #1045's engine emits only the front registry entry and promotes the
  next in `request_approval`'s `finally`, so exactly one `approval_request` is in flight by
  construction.
- **No replay code.** `TRANSIENT_EVENT_TYPES` already excludes `approval_request` from both sinks;
  this issue adds a regression test only.
- **No semantic diff, no target picker, no persistent deny, no arg-scoped persistence** — I4.2 /
  I5.2 / deferred.

## Design decisions taken for simplicity (KISS)

| Decision | Rationale |
|---|---|
| Modal body is one `Static` + one read-only `TextArea` | `Static` cannot scroll or be copied; `TextArea` gives both. No `OptionList`, no selection handler. |
| Digit bindings use `priority=True` | Checked before the focused widget, so a focused `TextArea` cannot swallow `1`–`5`. Removes the focus-management design fork. |
| The modal renders args with its own `format_args_full`, not `detail_modal._format_args` | `_format_args` routes values through `_render_value_full`, which cuts a single-line string over 120 chars to `value[:117] + "..."` — right for an inspection modal, fatal for a security decision, and unreachable by scrolling because the characters never reach the widget. A sibling formatter is smaller than reworking a shared one, and leaves `detail_modal.py` untouched. |
| Persist confirmation is an always-visible line under choice `3`, not a second screen | The issue settles that "the modal choice *is* the explicit apply", so the confirmation is text to display, not a keystroke to collect. |
| Insertion uses one indentation rule | Indent like the existing first array item, else the `[` line's indent + 2. One branch, not a formatting engine. |
| Choice tests are parametrised | Five choices plus `Esc` become one test function over `(key, expected)`. |

## Modal contract

Five numbered, keyboard-first choices; `Esc` = deny once; `ctrl+c` copies and does **not** cancel
(the full args must be copyable for the security decision).

```
1  allow once                          → ApprovalDecision("allow", "once")
2  allow + remember (session)          → ApprovalDecision("allow", "session")
3  allow + remember (persist)          → ApprovalDecision("allow", "persist")
4  deny once                           → ApprovalDecision("deny", "once")   reason=None
5  cancel this turn                    → None  (cancel_pending_approvals; never resolve_pending)
```

`ApprovalDecision.outcome` is `Literal["allow", "deny"]` — there is no cancel outcome — so the
screen is typed `ModalScreen[Optional[ApprovalDecision]]` and `5` dismisses with `None`, exactly
as `SessionPickerScreen(ModalScreen[Optional[Path]])` does. `reason` stays `None` for a real user
deny; it exists only for the two producers that deny without asking anybody.

The modal states the over-grant explicitly, because a "remember" grant is whole-tool — it covers
all future calls with **any** arguments, not just the arguments shown:

```
⚠ Remembering allows every future call to <tool> — with any arguments, not just these.
```

## Steps

| # | Title | Commit scope |
|---|---|---|
| 1 | Resolver cross-layer precedence (closes #1154) | `resolver.py` + resolver tests |
| 2 | `ApprovalModal` widget | `approval_modal.py` + modal tests |
| 3 | Modal push + `once`/`session` wiring; remove the interim auto-deny | `stream_view.py`, `app.py`, `loader.py` + pilot tests |
| 4 | `permissions/persist.py` JSONC write-back | `persist.py`, `.importlinter` + writer unit tests |
| 5 | Wire the `persist` choice + end-to-end composition test | `stream_view.py` + pilot/e2e tests |

Steps 4 and 5 are gated on step 1. If #1154 is landed separately on `main` first, skip step 1 and
renumber nothing — steps 2–5 are unaffected.

## Files created

| Path | Purpose |
|---|---|
| `src/mcp_coder/icoder/ui/widgets/approval_modal.py` | `ApprovalModal` screen (step 2) |
| `src/mcp_coder/icoder/permissions/persist.py` | Span tokenizer + `write_rule` (step 4) |
| `tests/icoder/test_permissions_persist.py` | Unmarked `tmp_path` unit tests for the writer (step 4) |

## Files modified

| Path | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/resolver.py` | `_PERSONAL_LAYERS` + 6-key `_rule_sort_key`; five prose sites — module docstring, `_rule_sort_key` `Returns:`, `_resolve_config` docstring, its partition comment and its R14 bound comment (step 1) |
| `src/mcp_coder/icoder/permissions/loader.py` | Add `LOCAL_SETTINGS_RELPATH`; use it in `_discover_layers` (step 3) |
| `src/mcp_coder/icoder/ui/stream_view.py` | Delete `_DENY_NO_UI` + the `TODO(#1046)` auto-deny; push the modal; dismiss callback; receive `action_cancel_stream` (steps 3, 5) |
| `src/mcp_coder/icoder/ui/app.py` | Remove `action_cancel_stream` (binding stays) (step 3) |
| `.importlinter` | Add `permissions.persist` to `permissions_leaf_isolation` `source_modules` (step 4) |
| `tests/icoder/test_permissions_resolver.py` | Seven new precedence cases; docstring notes on two existing tests (step 1) |
| `tests/icoder/test_app_pilot.py` | Replace the auto-deny test; delete the `TODO(#1046)` monkeypatch; modal + scope + replay tests (steps 2, 3, 5) |

## Folders

No new packages. `ui/widgets/` and `permissions/` each gain one module; `tests/icoder/` gains one
test file.

## Checks (every step)

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_mypy_check          # strict
mcp__mcp-tools-py__run_ruff_check
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration"])
mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto"], markers=["textual_integration"])
```

## Constraints carried from the issue

- **`.gitignore` seam is OPEN.** An entry for `.icoder/settings.local.json` is not committed at
  HEAD; wiring it remains I5.3's obligation. Independently, the MCP file tools refuse gitignored
  paths, so every write-back test uses `tmp_path`, never an in-repo fixture.
- **`.icoder/` may not exist.** `_discover_layers` only picks up existing files and `emit_schema`
  bails when `.icoder` is not a directory, so the writer creates the directory as well as the file.
- **`source` on the event is a bare string** (`user`/`project`/`local`/`runtime`/`frame`/`default`),
  not a `Decision.Source`. `degraded` is unreachable — #1045 R15 denies `Degraded`-sourced
  decisions before the engine is reached.
- **R17 stands:** there is no correlation key between `approval_request` and the on-screen tool
  row. The modal identifies the call by tool name + args only.
- **A runtime rule added mid-turn** is visible to later call-level `resolve()`s in the same turn,
  but cannot un-hide a `never` tool — `filter_tools` is a turn-start snapshot.
- CI file-size gate is 750 lines (`.github/workflows/ci.yml:107`); `tests/icoder/test_app_pilot.py`
  is on `.large-files-allowlist`.
