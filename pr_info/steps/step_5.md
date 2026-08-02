# Step 5 — Startup feedback: list broken skills + a loud degraded-config line

**Read `pr_info/steps/summary.md` first.** Two failure kinds are invisible today: a broken skill (only
knowable by invoking it) and a **degraded** permission config, which silently forces every MCP call to
deny while saying so only via a Textual-swallowed `logger.error`. This step surfaces both in the
startup banner area, as prominent (non-dim) lines. Pure formatting lives in `runtime_banner.py` for
testability; `AppCore` exposes the two inputs; `on_mount` renders them.

## WHERE (all modified)
- `src/mcp_coder/icoder/ui/runtime_banner.py` — new pure `format_startup_permission_notices(...)`
- `src/mcp_coder/icoder/core/app_core.py` — expose `broken_skills` + `permission_degraded`
- `src/mcp_coder/cli/commands/icoder.py` — hoist a `permission_degraded` flag (default `False`) to
  outer scope and pass it to `AppCore` (see HOW; `config` is not in scope at the `AppCore(...)` call)
- `src/mcp_coder/icoder/ui/app.py` — render the notices in `on_mount`
- Tests: `tests/icoder/test_runtime_banner.py`, `test_app_core.py`, `test_cli_icoder.py`,
  `test_app_pilot.py`

## WHAT (signatures)
```python
# runtime_banner.py  (pure, no Textual)
def format_startup_permission_notices(
    broken_skills: Mapping[str, str],   # command/skill name -> reason
    degraded: bool,
) -> list[str]: ...

# core/app_core.py
def __init__(self, ..., permission_degraded: bool = False) -> None: ...
@property
def broken_skills(self) -> dict[str, str]: ...        # {name: reason} from self._skill_frames
@property
def permission_degraded(self) -> bool: ...
```

## HOW
- **`app_core.py`:** store `self._permission_degraded = permission_degraded`. `broken_skills` derives
  from the Step-3 snapshot: `{name: sf.blocked_reason for name, sf in self._skill_frames.items() if
  sf.blocked_reason}`. No new state beyond the flag.
- **`cli/commands/icoder.py`:** the `config` local only exists inside the
  `provider == "langchain" and mcp_config` gate, but `AppCore(...)` is constructed later at outer
  scope — referencing `config.degraded` at the call site would `NameError`. Initialise
  `permission_degraded = False` **before** that gate and set `permission_degraded = config.degraded`
  inside it (right after `config = load_permission_config(project_dir)`), then pass the hoisted
  `permission_degraded` flag to `AppCore`. Non-langchain keeps the `False` default.
- **`ui/app.py` `on_mount`:** after the existing dim runtime banner, build
  `notices = format_startup_permission_notices(self._core.broken_skills,
  self._core.permission_degraded)`; if non-empty, `output.append_text("\n".join(notices),
  style=STYLE_CANCELLED)` (the same attention style used for `permission_warning`). Skip on the
  resume path (mirrors the existing `if self._resume_log_path` guard).

## ALGORITHM (`format_startup_permission_notices`)
```
lines = []
if degraded:
    lines.append("⚠ Permission config is degraded — all MCP tool calls are denied. See logs.")
for name in sorted(broken_skills):
    lines.append(f"⚠ /{name} is disabled: {broken_skills[name]}")
return lines
```

## DATA
- Returns `[]` when nothing is wrong (no line rendered — no noise for healthy startups).
- Broken-skill names are sorted for determinism; the reason is the same `blocked_reason` string the
  invocation refusal (Step 4) prints, so the two surfaces agree.

## TESTS (write first)
- `test_runtime_banner.py`: `format_startup_permission_notices({}, False) == []`;
  degraded-only yields one line mentioning "degraded"; broken-only yields one sorted line per skill;
  both present yields the degraded line first, then the skills.
- `test_app_core.py`: `broken_skills` reflects only frames with a `blocked_reason`;
  `permission_degraded` echoes the constructor flag.
- `test_cli_icoder.py`: `AppCore` receives `permission_degraded=True` when the loaded config is
  degraded (langchain), and `False`/default otherwise.
- `test_app_pilot.py`: drive the Textual pilot on startup with an `AppCore` whose
  `permission_degraded` is `True` **and** whose `skill_frames` carry a `blocked_reason`, and assert the
  output actually renders **both** notice kinds — the degraded-config line and a broken-skill line — so
  the `on_mount` render path (not just the pure formatter + `AppCore` properties) is covered
  ("startup surfaces both failure kinds"), analogous to the Step 3 pilot test for `permission_warning`.
  Assert the fresh-start path renders the notices and the resume path (`resume_log_path` set) skips them.

## LLM PROMPT
> Implement Step 5 of `pr_info/steps/summary.md` (see `pr_info/steps/step_5.md`). Using TDD, write the
> listed tests first, then: add the pure `format_startup_permission_notices` to `runtime_banner.py`;
> expose `broken_skills` and `permission_degraded` on `AppCore` (derive `broken_skills` from the
> existing `skill_frames` snapshot, add the degraded flag to `__init__`); pass
> `permission_degraded=config.degraded` from `cli/commands/icoder.py` (langchain branch); and render
> the notices in `ui/app.py`'s `on_mount` after the dim banner, using the attention style, skipped on
> resume. Run pylint, mypy(strict), pytest (`-n auto` unit-only exclusions) and `lint-imports` until
> green. One commit. This completes issue #1061 — verify every acceptance criterion in the issue is
> covered by a test across Steps 1–5.
