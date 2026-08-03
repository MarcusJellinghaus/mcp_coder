# Step 3 — Transport: swap the carrier, wire the frame-map snapshot, delete `build_legacy_frame`

**Read `pr_info/steps/summary.md` first.** This is the coupled, atomic carrier swap: it replaces the
raw-string `allowed_tools` carrier with `skill_name`, builds the `{skill_name: SkillFrame}` snapshot
once at startup (owned by `AppCore`, design §8.1), passes the resolved frame to the service, moves
warning emission to `AppCore`, and **deletes** `build_legacy_frame`. Blocked-skill *refusal* and
*startup listing* are Steps 4–5; here a blocked skill simply runs on its fail-closed frame (safe:
`base="none"` sandboxes it). It cannot be split further without leaving a half-swapped carrier that
fails to type-check.

## WHERE (all modified)
- `src/mcp_coder/icoder/core/types.py`, `src/mcp_coder/icoder/skills.py`,
  `src/mcp_coder/icoder/services/llm_service.py`, `src/mcp_coder/icoder/permissions/gateway.py`,
  `src/mcp_coder/icoder/core/app_core.py`, `src/mcp_coder/icoder/ui/app.py`,
  `src/mcp_coder/cli/commands/icoder.py`, `src/mcp_coder/llm/types.py`, `.importlinter`
- Tests migrated: `tests/icoder/test_types.py`, `test_skills.py`, `test_llm_service.py`,
  `test_permissions_gateway.py`, `test_app_core.py`, `test_app_pilot.py`, `test_cli_icoder.py`

## WHAT (signatures)
```python
# core/types.py
class SendToLLM: text: str; skill_name: str | None = None      # was: allowed_tools: tuple[str,...]|None

# services/llm_service.py  (Protocol + Real + Fake)
def stream(self, question: str, *, frame: PermissionFrame | None = None) -> Iterator[StreamEvent]: ...
#   RealLLMService.__init__: drop `enforce_skill_tools`. FakeLLMService: drop it too; add `last_frame`.

# core/app_core.py
def __init__(self, ..., skill_frames: Mapping[str, SkillFrame] | None = None) -> None: ...
def stream_llm(self, text: str, skill_name: str | None = None) -> Iterator[StreamEvent]: ...

# cli/commands/icoder.py
ENFORCE_SKILL_TOOLS = False   # module-level; #1062 flips this (fail-closed enforcement on langchain)
```

## HOW
- **`skills.py` handler:** `_make_langchain_handler` emits `SendToLLM(text=expanded, skill_name=skill.name)`
  (no token tuple). Claude handler unchanged.
- **`gateway.py`:** delete `build_legacy_frame` and its imports; gateway is enforcement-only now.
- **`services/llm_service.py`:** `RealLLMService.stream` receives the already-built `frame`, calls
  `self._gateway.begin_turn(frame)` then `filter_tools(...)` (as today, minus the build + the warning
  loop). `FakeLLMService.stream(*, frame=None)` records `self.last_frame = frame`.
- **`app_core.py`:** store `self._skill_frames = dict(skill_frames or {})`. In `stream_llm`, look up
  `sf = self._skill_frames.get(skill_name)`; prepend one `{"type":"permission_warning","message":w}`
  per `sf.warnings` **in front of** `self._llm_service.stream(text, frame=sf.frame if sf else None)`
  and feed the combined stream through the **existing** `assembler.add(...)` + `emit("stream_event",
  **event)` loop (see ALGORITHM) so warnings are logged/replayed like any other event, not dropped.
  `handle_input`'s `SendToLLM` branch keeps `replace(action, text=action.text or text)` (skill_name
  already carried).
- **`ui/app.py`:** in the `SendToLLM()` case read `action.skill_name`; `_stream_llm(self, text,
  skill_name=None)` calls `self._core.stream_llm(text, skill_name)`.
- **`cli/commands/icoder.py`:** build the frame map **unconditionally, for every provider**, right
  **after** `skills = load_skills(...)` (so `skills` is in scope) and **before** both
  `register_skill_commands(...)` (Step 4 reads each frame's `blocked_reason`) and the outer-scope
  `AppCore(...)` construction — mirroring Step 5's hoist of `permission_degraded` out of the
  `provider=="langchain" and mcp_config` gate (do **not** build it inside that gate: it runs before
  `load_skills`, so `skills` is not yet defined there):
  `frame_map = {s.name: build_frame(s.tools_block, tuple(s.allowed_tools) or None,
  enforce_skill_tools=ENFORCE_SKILL_TOOLS if provider == "langchain" else False) for s in skills}`.
  **The enforcement flag is langchain-only — do not simplify it back to a bare
  `ENFORCE_SKILL_TOOLS`.** Rationale: the legacy `allowed-tools` path is Claude-provider-**native**
  (`Bash(...)`/`gh`/`git` tokens are real permissions there), so once #1062 flips the constant to
  `True` a bare flag would give every shell-only skill `base="none"` + nothing-survived →
  `blocked_reason`, and Step 4 would refuse it **under the claude provider**, where it works fine.
  Only `tools_block.errors`-driven blocking is provider-agnostic (D12); the legacy path never blocks
  outside langchain. `build_frame` is pure and needs no
  `mcp_config`, so a malformed `tools:` block blocks its skill **regardless of provider** — this
  restores D12's parse-time, provider-agnostic blocking (a `disabled_reason` is set for a broken skill
  even under langchain-without-`mcp_config` or a non-langchain provider). Pass `skill_frames=frame_map`
  to `AppCore`. Only the **gateway enforcement** stays gated on `provider=="langchain" and mcp_config`
  (a `None` gateway simply ignores the forwarded frame). Drop `enforce_skill_tools=False` from the
  `RealLLMService(...)` call.
- **`llm/types.py`:** add a `permission_warning` bullet to the `StreamEvent` known-types docstring.
- **`.importlinter`:** add `mcp_coder.cli.commands.icoder -> mcp_coder.icoder.permissions.skill_frame`
  to the `layered_architecture` `ignore_imports` list (cli↔icoder are the same layer; every such edge
  is listed). No new contract.

## ALGORITHM (`AppCore.stream_llm`)
```
sf = self._skill_frames.get(skill_name)
self._event_log.emit("llm_request_start", text=text)
# Route warnings through the SAME assembler + event-log path as service events so
# they are not dropped from resume/replay logging (today the service yields them
# inside this loop, so they are logged as stream_event — preserve that).
def _events():
    for w in (sf.warnings if sf else ()):
        yield {"type": "permission_warning", "message": w}
    yield from self._llm_service.stream(text, frame=(sf.frame if sf else None))
for event in _events():
    assembler.add(event)
    if event.get("type") != "raw_line":
        self._event_log.emit("stream_event", **event)
    ... existing token-usage / done handling ...
    yield event
```

## DATA
- `SendToLLM` now carries `skill_name: str | None`; every turn installs a frame (`None` for a plain
  message or an unknown skill). Frames are single-turn — the next message runs frameless.
- `FakeLLMService.last_frame: PermissionFrame | None` replaces `last_allowed_tools` for assertions.

## TESTS (write/migrate first)
- `test_types.py`: `SendToLLM.skill_name` defaults `None` and round-trips.
- `test_skills.py`: langchain handler yields `SendToLLM(skill_name="<name>")`.
- `test_permissions_gateway.py`: delete the `build_legacy_frame` tests (behaviour now lives in
  `test_skill_frame.py`); keep filter/interceptor tests.
- `test_llm_service.py`: `stream(frame=<PermissionFrame>)` installs it via `begin_turn` and filters;
  `stream(frame=None)` installs `None`; `FakeLLMService.last_frame` records the frame; remove
  `enforce_skill_tools` usages.
- `test_app_core.py`: `stream_llm(text, skill_name)` looks up the injected `skill_frames`, forwards
  `sf.frame` to the service, and emits `sf.warnings` as `permission_warning` events (assert order:
  warnings precede the stream). `handle_input` preserves `skill_name` across reconstruction.
  **Single-turn / no-leak:** invoking a skill turn (`stream_llm(text, skill_name=\"<name>\")`) forwards
  that skill's `sf.frame`, and the immediately following plain-message turn (`stream_llm(text)` /
  `skill_name=None`) forwards `frame=None` — asserted via `FakeLLMService.last_frame` on each call —
  proving a skill frame never leaks into the next turn (frames are single-turn).
- `test_app_pilot.py`: the UI worker threads `skill_name` and renders `permission_warning`.
- `test_cli_icoder.py`: `RealLLMService` is built **without** `enforce_skill_tools`; `AppCore` receives
  a `skill_frames` map built from the loaded skills **for every provider** (non-empty whenever skills
  exist — not gated on langchain/`mcp_config`); only the gateway wiring stays langchain-gated. Also:
  `build_frame` is called with `enforce_skill_tools=False` for a non-langchain provider even when
  `ENFORCE_SKILL_TOOLS` is patched `True` (guards the #1062 flip against blocking Claude-native
  shell-only skills), and with the constant's value for langchain.

## LLM PROMPT
> Implement Step 3 of `pr_info/steps/summary.md` (see `pr_info/steps/step_3.md`). This is the atomic
> transport swap. Update/migrate the listed tests first, then: change `SendToLLM.allowed_tools` to
> `skill_name: str | None`; make the langchain skill handler emit `skill_name`; give `LLMService.stream`
> a keyword-only `frame` param on the Protocol, `RealLLMService` and `FakeLLMService` (drop
> `enforce_skill_tools` from both; add `FakeLLMService.last_frame`); delete `build_legacy_frame` from
> `gateway.py`; add the `skill_frames` snapshot to `AppCore` and rewrite `stream_llm(text, skill_name)`
> to look it up, emit `SkillFrame.warnings` as `permission_warning` events, and forward the frame;
> thread `skill_name` through `ui/app.py`; add `ENFORCE_SKILL_TOOLS` and build the `{skill_name:
> SkillFrame}` map **for every provider** (after `load_skills`, before `register_skill_commands` and
> `AppCore`) in `cli/commands/icoder.py` — passing
> `enforce_skill_tools=ENFORCE_SKILL_TOOLS if provider == "langchain" else False` — then pass it to
> `AppCore` and drop the
> `enforce_skill_tools` kwarg; document `permission_warning` in `llm/types.py`; and add the one
> `cli.commands.icoder -> permissions.skill_frame` line to `.importlinter`. Run pylint, mypy(strict),
> pytest (`-n auto` unit-only exclusions) and `lint-imports` until green. One commit.
