# Step 3 — Modal push + `once`/`session` wiring; remove the interim auto-deny

## Goal

A pending-approval event pushes the modal; the user's decision is applied on the UI thread and
handed to `resolve_pending`. The interim auto-deny disappears.

After this step choice `3` applies the runtime rule but **not yet** the disk write — that is
step 5. This is the only intermediate state in the plan and it is confined to one commit on the
branch.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/loader.py` | add `LOCAL_SETTINGS_RELPATH`; use it in `_discover_layers` |
| `src/mcp_coder/icoder/ui/stream_view.py` | delete `_DENY_NO_UI` + the `TODO(#1046)` branch; push the modal; dismiss callback; receive `action_cancel_stream` |
| `src/mcp_coder/icoder/ui/app.py` | remove `action_cancel_stream` (the `Binding` stays) |
| `tests/icoder/test_app_pilot.py` | replace `:1609`; delete the `:1766` monkeypatch; new tests |

## WHAT

`loader.py`:

```python
LOCAL_SETTINGS_RELPATH = Path(".icoder") / "settings.local.json"
```

The path is currently a literal inside `_discover_layers`. Introduce the constant rather than
letting `persist.py` duplicate it in step 4, and use it for the `local` candidate.

`stream_view.py`:

```python
def _grant_rule(tool_name: str) -> Rule | None: ...          # module-level

class StreamViewApp(App[None]):
    def action_cancel_stream(self) -> None: ...              # moved down from ICoderApp
    def _persist_target(self) -> Path: ...
    def _push_approval_modal(self, event: StreamEvent) -> None: ...
    def _apply_approval(
        self,
        approval_id: str,
        tool_name: str,
        decision: ApprovalDecision | None,
    ) -> None: ...
```

## HOW — integration points

New imports in `stream_view.py`: `Path`, `parse_matcher`, `Policy`, `Rule`,
`LOCAL_SETTINGS_RELPATH`, `ApprovalModal`. The `ApprovalDecision` import stays (now only for the
callback annotation). `ui → permissions` is a permitted direction; only the reverse is forbidden.

`_handle_stream_event`'s `approval_request` branch shrinks to:

```python
if event.get("type") == "approval_request":
    self._push_approval_modal(event)
    return
```

`_DENY_NO_UI` and its explanatory comment are deleted outright.

**`action_cancel_stream` moves from `ICoderApp` to `StreamViewApp`** verbatim, docstring included.
It only touches `_cancel_event` and `_core`, both already `StreamViewApp` members.
`ICoderApp.BINDINGS`'s `Binding("escape", "cancel_stream", ...)` resolves it by name and does not
change. Grep for `action_cancel_stream` afterwards to confirm no caller broke.

## ALGORITHM

```python
def _push_approval_modal(self, event):
    approval_id = str(event.get("approval_id", ""))
    tool_name   = str(event.get("tool_name", ""))
    args        = event.get("args")
    modal = ApprovalModal(
        tool_name=tool_name,
        args=args if isinstance(args, dict) else {},
        source=str(event.get("source", "")),
        persist_target=self._persist_target(),
    )
    self.push_screen(modal, lambda d: self._apply_approval(approval_id, tool_name, d))
```

```python
def _apply_approval(self, approval_id, tool_name, decision):
    if decision is None:                      # choice 5: abandon the turn
        self.action_cancel_stream()           # sets _cancel_event AND cancels the future
        return                                # never resolve_pending
    if decision.scope in ("session", "persist"):
        rule = _grant_rule(tool_name)         # step 5 gates its disk write on this guard
        if rule is not None:
            self._core.add_runtime_rule(rule)
    self._core.resolve_pending(approval_id, decision)
```

```python
def _grant_rule(tool_name):
    matchers, errors = parse_matcher(tool_name)
    if errors or not matchers:
        logger.warning("no runtime grant for %r: %s", tool_name, errors)
        return None
    return Rule(matchers[0], Policy.ALWAYS, "runtime")
```

```python
def _persist_target(self):
    info = self._core.runtime_info
    root = Path(info.project_dir) if info else Path.cwd()
    return root / LOCAL_SETTINGS_RELPATH
```

`push_screen(screen, callback)` — **`push_screen_wait` is forbidden.** `_handle_stream_event` runs
under `call_from_thread`, which blocks the consumer thread until it returns, and both streaming
timeouts are suspended while an approval is pending, so a wedge there would be permanent.

The scope side-effect is applied *before* `resolve_pending`, which only resolves the Future. This
callback never touches the Future itself.

No queue and no lock are added: #1045's engine emits only the front registry entry and promotes
the next in `request_approval`'s `finally`, so exactly one `approval_request` is in flight by
construction.

## DATA

`ApprovalDecision | None` in, nothing out. The runtime grant is
`Rule(matcher, Policy.ALWAYS, "runtime")` with `source_path` left `None` — it has no file.
`parse_matcher` returns `(list[Matcher], list[str])`; a canonical `mcp__server__tool` name always
yields exactly one matcher and no errors, but the guard keeps `mypy --strict` honest and degrades
to "grant nothing, still answer the call" rather than raising on the UI thread.

## TDD — tests first

Deletions, both mandated by the acceptance criteria:

- `test_approval_request_auto_denies_and_renders_nothing` (`:1609`) is **replaced** by
  `test_approval_request_pushes_the_modal`.
- The `TODO(#1046)` monkeypatch inside `test_quit_with_approval_pending_exits_and_unwinds_worker`
  (`:1766`) is **deleted** together with its comment block. It existed only to defeat the
  auto-deny; with the modal in place a pending approval is the natural state at quit time. That
  test must still pass unchanged otherwise.
- The `_DENY_NO_UI` import at the top of the test file goes with it.

New tests:

| Test | Asserts |
|---|---|
| `test_approval_request_pushes_the_modal` | after `_handle_stream_event({"type": "approval_request", ...})` the top screen is an `ApprovalModal` carrying the event's tool name; `engine.resolved == []` (nothing answered yet) |
| `test_approval_choice_resolves_pending_with_decision` | **parametrised** over `("1", "allow", "once")`, `("2", "allow", "session")`, `("4", "deny", "once")`: after `pilot.press(key)` the `_RecordingEngine` recorded exactly one `(approval_id, decision)` with the right `outcome`/`scope`, `approval_id` matching the event, and `reason is None` |
| `test_allow_once_writes_no_runtime_rule` | with a spy on `AppCore.add_runtime_rule`, choice `1` records no call |
| `test_session_choice_writes_a_runtime_rule` | choice `2` records exactly one `Rule` with `layer == "runtime"`, `policy is Policy.ALWAYS`, and a matcher that matches the tool |
| `test_session_grant_is_honoured_by_resolve` | take the captured `Rule`, build `PermissionConfig(rules=(authored_ask, captured))` where `authored_ask` is `Rule(same matcher, AFTER_APPROVAL, "project")`, and assert `resolve(tool, {}, None, config).policy is Policy.ALWAYS` — public API only, and this is what "honoured on a subsequent turn" means |
| `test_session_grant_does_not_survive_a_reload` | author `tmp_path/".icoder"/"settings.json"` with `{"ask": ["mcp__srv__do_it"]}`; apply the session grant via choice `2`; then assert `resolve("mcp__srv__do_it", {}, None, load_permission_config(tmp_path)).policy is Policy.AFTER_APPROVAL` — the grant is gone and the tool asks again (design §8.4 makes this an explicit obligation: session grants do not survive a resume) |
| `test_cancel_turn_cancels_and_never_resolves` | choice `5`: `engine.cancel_calls == 1`, `engine.resolved == []`, `app._cancel_event.is_set()` |
| `test_ctrl_c_does_not_cancel_the_turn` | `pilot.press("ctrl+c")` on the open modal leaves `engine.cancel_calls == 0` and `engine.resolved == []` |
| `test_replayed_log_pushes_no_approval_modal` | drain `core.stream_llm(...)` over a fake service yielding an `approval_request` then `done`; assert the written `.jsonl` contains no `approval_request` line; then `app.do_resume(log_path)` and assert `len(app.screen_stack) == 1` |

`test_session_grant_does_not_survive_a_reload` must assert the *reloaded policy*, not the absence
of a `runtime`-layer rule: `_discover_layers` yields only `user`/`project`/`local` and `loader.py`
has no `runtime` handling at all, so "the reloaded config holds no `runtime` rule" can never fail
and would leave the AC uncovered. Authoring the `ask` on disk is what makes the assertion
falsifiable — it fails if the grant leaks into the loader.

It must also **isolate the user layer** before calling `load_permission_config(tmp_path)`:
`_discover_layers` reads `get_user_app_data_dir("mcp_coder") / ".icoder" / "settings.json"`, a real
machine path outside `tmp_path`. A machine-level user `allow`/`deny` for `mcp__srv__do_it` beats or
changes the authored `project` `ask`, and a malformed user file sets `degraded=True` — either way
the assertion turns on the runner's own config rather than on the code under test. Point the
lookup at an empty directory, as `tests/icoder/test_permissions_loader_layers.py:460`'s
`_empty_user_dir` does:

```python
user_root = tmp_path / "user"
user_root.mkdir(exist_ok=True)
monkeypatch.setattr(
    "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
    lambda _app: user_root,
)
```

The replay test must use a log produced through `AppCore.stream_llm`, not a hand-written one: the
guarantee under test is that `TRANSIENT_EVENT_TYPES` keeps `approval_request` out of the log at
the sink. This step adds **no** replay-mode branch to `_handle_stream_event`.

The existing `test_cancel_stream_also_cancels_pending_approvals` must keep passing after
`action_cancel_stream` moves.

## Acceptance

- All the ACs of #1046 except the four gated on #1154 are met.
- `_DENY_NO_UI` no longer appears anywhere in the repository.
- pylint / mypy(strict) / ruff / lint-imports clean; both pytest selections green.

## Commit

`feat(icoder): push the approval modal and apply once/session scopes (#1046)`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Step 2 must be committed first.
>
> Implement step 3 only: wire `ApprovalModal` into `ui/stream_view.py`, apply the `once` and
> `session` scopes, and remove the interim auto-deny. Do not create `permissions/persist.py` and
> do not add a disk write — choice `3` applies only the runtime rule in this step, and step 5
> completes it.
>
> Work TDD: first delete the two obsolete test artefacts named under "TDD — tests first" and add
> the nine new tests, then make them pass by editing `loader.py`, `stream_view.py` and `app.py` as
> specified under WHAT / HOW / ALGORITHM.
>
> Use `push_screen(screen, callback)`. Do not use `push_screen_wait` — the reason is in the HOW
> section and it is a hard requirement. Move `action_cancel_stream` down to `StreamViewApp` rather
> than inlining its two statements into the callback.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports and both pytest selections
> from the summary. Make exactly one commit when everything passes.
