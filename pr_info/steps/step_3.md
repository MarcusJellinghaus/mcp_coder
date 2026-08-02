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
ENFORCE_SKILL_TOOLS = False   # module-level; #1062 flips this (fail-closed enforcement for everyone)
```

## HOW
- **`skills.py` handler:** `_make_langchain_handler` emits `SendToLLM(text=expanded, skill_name=skill.name)`
  (no token tuple). Claude handler unchanged.
- **`gateway.py`:** delete `build_legacy_frame` and its imports; gateway is enforcement-only now.
- **`services/llm_service.py`:** `RealLLMService.stream` receives the already-built `frame`, calls
  `self._gateway.begin_turn(frame)` then `filter_tools(...)` (as today, minus the build + the warning
  loop). `FakeLLMService.stream(*, frame=None)` records `self.last_frame = frame`.
- **`app_core.py`:** store `self._skill_frames = dict(skill_frames or {})`. In `stream_llm`, look up
  `sf = self._skill_frames.get(skill_name)`; yield one `{"type":"permission_warning","message":w}` per
  `sf.warnings`; call `self._llm_service.stream(text, frame=sf.frame if sf else None)`. `handle_input`'s
  `SendToLLM` branch keeps `replace(action, text=action.text or text)` (skill_name already carried).
- **`ui/app.py`:** in the `SendToLLM()` case read `action.skill_name`; `_stream_llm(self, text,
  skill_name=None)` calls `self._core.stream_llm(text, skill_name)`.
- **`cli/commands/icoder.py`:** in the langchain branch (mirroring the existing `provider=="langchain"
  and mcp_config` gate) build `frame_map = {s.name: build_frame(s.tools_block, tuple(s.allowed_tools)
  or None, enforce_skill_tools=ENFORCE_SKILL_TOOLS) for s in skills}`; pass `skill_frames=frame_map`
  to `AppCore`. Drop `enforce_skill_tools=False` from the `RealLLMService(...)` call. Non-langchain →
  empty map.
- **`llm/types.py`:** add a `permission_warning` bullet to the `StreamEvent` known-types docstring.
- **`.importlinter`:** add `mcp_coder.cli.commands.icoder -> mcp_coder.icoder.permissions.skill_frame`
  to the `layered_architecture` `ignore_imports` list (cli↔icoder are the same layer; every such edge
  is listed). No new contract.

## ALGORITHM (`AppCore.stream_llm`)
```
sf = self._skill_frames.get(skill_name)
self._event_log.emit("llm_request_start", text=text)
for w in (sf.warnings if sf else ()): yield {"type":"permission_warning","message":w}
for event in self._llm_service.stream(text, frame=(sf.frame if sf else None)):
    ... existing assembler / token-usage / done handling ...
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
- `test_app_pilot.py`: the UI worker threads `skill_name` and renders `permission_warning`.
- `test_cli_icoder.py`: `RealLLMService` is built **without** `enforce_skill_tools`; `AppCore` receives
  a non-empty `skill_frames` under langchain and an empty map otherwise.

## LLM PROMPT
> Implement Step 3 of `pr_info/steps/summary.md` (see `pr_info/steps/step_3.md`). This is the atomic
> transport swap. Update/migrate the listed tests first, then: change `SendToLLM.allowed_tools` to
> `skill_name: str | None`; make the langchain skill handler emit `skill_name`; give `LLMService.stream`
> a keyword-only `frame` param on the Protocol, `RealLLMService` and `FakeLLMService` (drop
> `enforce_skill_tools` from both; add `FakeLLMService.last_frame`); delete `build_legacy_frame` from
> `gateway.py`; add the `skill_frames` snapshot to `AppCore` and rewrite `stream_llm(text, skill_name)`
> to look it up, emit `SkillFrame.warnings` as `permission_warning` events, and forward the frame;
> thread `skill_name` through `ui/app.py`; add `ENFORCE_SKILL_TOOLS` and build the `{skill_name:
> SkillFrame}` map (langchain only) in `cli/commands/icoder.py`, passing it to `AppCore` and dropping
> the `enforce_skill_tools` kwarg; document `permission_warning` in `llm/types.py`; and add the one
> `cli.commands.icoder -> permissions.skill_frame` line to `.importlinter`. Run pylint, mypy(strict),
> pytest (`-n auto` unit-only exclusions) and `lint-imports` until green. One commit.
