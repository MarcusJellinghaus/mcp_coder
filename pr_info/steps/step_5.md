# Step 5 — Wire the `persist` choice + end-to-end composition test

> **Gated on steps 1 and 4.**

## Goal

Choice `3` writes the rule to `.icoder/settings.local.json` **and** applies the same rule to the
runtime layer, so the grant is live for the rest of the process and survives the next launch.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/ui/stream_view.py` | add the disk write to `_apply_approval` |
| `tests/icoder/test_app_pilot.py` | persist tests + the end-to-end composition test |

## WHAT

No new signatures. `_apply_approval` gains one branch:

```python
def _apply_approval(
    self,
    approval_id: str,
    tool_name: str,
    decision: ApprovalDecision | None,
) -> None: ...
```

New import in `stream_view.py`: `from mcp_coder.icoder.permissions.persist import write_rule`.

## HOW — integration points

The write happens **on the UI thread, in the dismiss callback, before `resolve_pending`** — the
same place and the same ordering as the `session` grant. The engine never writes: the
`permissions_leaf_isolation` contract forbids `icoder.permissions` a Textual handle, and
marshalling back into the UI thread from the agent loop would be two hops for something the UI
thread can do inline.

The runtime rule is applied for `persist` too, not only for `session`. Without it the user would
have to relaunch before their own grant took effect.

## ALGORITHM

```python
if decision.scope in ("session", "persist"):
    rule = _grant_rule(tool_name)                    # the parse guard, now FIRST
    if rule is None:
        self.query_one(OutputLog).append_text(       # nothing granted, nothing written
            f"Could not remember {tool_name}: not a valid matcher.",
            style=STYLE_CANCELLED,
        )
    else:
        if decision.scope == "persist":
            try:
                write_rule(self._persist_target(), tool_name)
            except OSError as exc:                   # incl. PersistError (unparseable file);
                logger.warning("persist write failed: %s", exc)
                self.query_one(OutputLog).append_text(
                    f"Could not write the permission rule: {exc}", style=STYLE_CANCELLED
                )
        self._core.add_runtime_rule(rule)
self._core.resolve_pending(approval_id, decision)
```

**The `_grant_rule` parse guard moves ahead of the disk write** (step 3 computed it after; that
ordering is only safe while there is no write). `write_rule` inserts the matcher string verbatim
and validates nothing, while `loader._load_layer` is per-layer atomic: one token `parse_matcher`
rejects fails the **whole** `local` layer, which sets `degraded=True` and drives every tool to ASK
on every future launch until the user hand-edits the file. So a name the resolver could never have
matched must not reach disk. It is reachable: `gateway.interceptor` builds
`f"mcp__{request.server_name}__{request.name}"`, and `matcher._parse_token` requires exactly two
`__`-separated parts, so a tool whose own name contains `__` yields `mcp__srv__do__it` — which
never matches a rule, and therefore prompts under `defaultMode: "ask"`.

A failed disk write degrades to a session grant and says so. Neither branch may raise on the UI
thread or leave the parked interceptor unanswered — `resolve_pending` still runs in every case,
including the unparseable-matcher one.

`except OSError` is the single degrade branch and it must cover **every** `write_rule` failure,
not just an unwritable target. Step 4 raises `PersistError(OSError)` for an unparseable
`settings.local.json` and for a non-object root precisely so this one clause suffices; do not add
a second `except ValueError`, and do not narrow this clause to `PermissionError`. Anything that
escapes here runs on the UI thread inside the dismiss callback, skips `resolve_pending`, and
wedges the turn permanently.

The section is always `"allow"`: deny is once-only in v1, so `persist` can only ever carry an
allow. `write_rule`'s `section` parameter keeps its default and is not passed here.

## DATA

`_persist_target()` (added in step 3) returns
`Path(runtime_info.project_dir) / LOCAL_SETTINGS_RELPATH`, i.e.
`<project_dir>/.icoder/settings.local.json`. Persist **always** writes there, for new and existing
matchers alike — it never edits a `project`- or `user`-layer file, because a personal "remember
this" must not mutate a committed, team-shared config. There is no picker in v1; the resolved
target is already shown read-only in the modal (step 2).

## TDD — tests first

Add to the approval section of `tests/icoder/test_app_pilot.py`. All of these need a real
`project_dir`, so construct the `AppCore` with a `RuntimeInfo` pointing at `tmp_path`.

**Every test here that calls `load_permission_config(tmp_path)` must isolate the user layer
first**, exactly as step 4's `_reload` helper does:

```python
user_root = tmp_path / "user"
user_root.mkdir(exist_ok=True)
monkeypatch.setattr(
    "mcp_coder.icoder.permissions.loader.get_user_app_data_dir",
    lambda _app: user_root,
)
```

`_discover_layers` reads `get_user_app_data_dir("mcp_coder") / ".icoder" / "settings.json"` — a
real machine path outside `tmp_path` — so without this both load-bearing assertions below are
environment-dependent: a machine-level user `ask`/`deny` for `mcp__srv__do_it` changes
`test_persist_end_to_end_yields_always_after_reload`'s resolved policy, and a malformed user file
sets `degraded=True`, which falsifies `test_unparseable_tool_name_is_never_written_to_disk`'s
`degraded is False` while the code under test is perfectly correct. The precedent is
`tests/icoder/test_permissions_loader_layers.py:460`'s `_empty_user_dir`.

| Test | Asserts |
|---|---|
| `test_persist_choice_writes_the_rule_to_settings_local` | after `pilot.press("3")`, `tmp_path/".icoder"/"settings.local.json"` exists and its parsed `allow` list contains the tool exactly once |
| `test_persist_choice_also_applies_the_runtime_rule` | the `add_runtime_rule` spy recorded one `Rule(layer="runtime", policy=ALWAYS)` — the grant is live this process, not only next launch |
| `test_persist_choice_resolves_pending_with_persist_scope` | the `_RecordingEngine` recorded `("allow", "persist")` and the write happened **before** the resolve (assert ordering, e.g. by recording both into one list) |
| `test_persist_end_to_end_yields_always_after_reload` | `tmp_path/".icoder"/"settings.json"` authored with `{"ask": ["mcp__srv__do_it"]}`; drive choice `3`; then `load_permission_config(tmp_path)` + `resolve("mcp__srv__do_it", {}, None, config)` is `Policy.ALWAYS` |
| `test_unparseable_tool_name_is_never_written_to_disk` | the `approval_request` carries `tool_name="mcp__srv__do__it"` (three `__`-separated parts, so `parse_matcher` rejects it); after `pilot.press("3")` **no** `settings.local.json` exists, `add_runtime_rule` recorded nothing, `resolve_pending` was still called with `("allow", "persist")`, and the output log carries a message. Then assert the next launch is unharmed: `load_permission_config(tmp_path)` over the authored `.icoder/settings.json` returns `degraded is False`. Without the guard the file holds a token `_load_layer` rejects, which degrades the whole layer and drives every tool to ASK forever. |
| `test_persist_write_failure_degrades_to_a_session_grant` | **parametrised** over an unwritable target (create `.icoder/settings.local.json` as a **directory**), invalid UTF-8 bytes (`b'{"allow": ["\xff\xfe"]}'`), a malformed file (`{"allow": [`), a non-object root (`["x"]`), a non-list section value (`{"allow": "mcp__a__b"}`) and a duplicate top-level key whose item cannot be located (`{"ask": [], "ask": ["mcp__srv__do_it"]}`, which drives the move branch); in all six, choice `3` still calls `add_runtime_rule`, still calls `resolve_pending`, and the output log carries a message. The last five are what prove `PersistError` reaches the `except OSError` branch rather than escaping onto the UI thread as a `ValueError`/`TypeError` and wedging the turn |

`test_persist_end_to_end_yields_always_after_reload` is the only test that proves #1046 and #1154
actually compose, and it is exactly the failure the persist-precedence correction exists to
prevent: before step 1, an authored `project` `ask` beat a persisted `local` `allow` at equal
specificity and this test would return `AFTER_APPROVAL`. Do not weaken it into a
"file contains the string" assertion.

## Acceptance

- Every acceptance criterion of #1046 is now met, including the four gated on #1154.
- `run_pylint_check`, `run_mypy_check` (strict), `run_ruff_check`, `run_lint_imports_check`,
  `run_tach_check`, `check_file_size` all clean.
- Both pytest selections green.
- `.scratch/` deleted if any probe was written (`delete_directory(".scratch", recursive=True)`) —
  CI blocks any PR carrying one.

## Commit

`feat(icoder): persist approval grants to settings.local.json (#1046)`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Steps 1–4 must be committed first.
>
> Implement step 5 only: wire the `persist` choice in `ui/stream_view.py::_apply_approval` per the
> ALGORITHM section — `_grant_rule`'s parse guard first, then the disk write, then the mirrored
> runtime rule, then `resolve_pending`. A tool name `parse_matcher` rejects must reach neither the
> runtime layer nor the file: writing it would fail the whole `local` layer on the next launch.
> A failed write degrades to a session grant with a message in the output log and must not raise
> on the UI thread. The single `except OSError` clause must catch step 4's `PersistError` too —
> an unparseable, non-object or non-list-section `settings.local.json` must degrade, not wedge the
> turn.
>
> Work TDD: add the six tests from the table to the approval section of
> `tests/icoder/test_app_pilot.py` first, watch them fail, then make them pass.
>
> `test_persist_end_to_end_yields_always_after_reload` must go through
> `load_permission_config` + `resolve` — it is the only test proving that #1046 and #1154 compose.
> Do not weaken it to a string assertion on the file.
>
> Finally, re-read the acceptance criteria of issue #1046 and confirm each one is now met, calling
> out any that is not. Run `run_format_code`, then pylint, mypy(strict), ruff, lint-imports, tach,
> `check_file_size` and both pytest selections. Delete `.scratch/` if it exists. Make exactly one
> commit when everything passes.
