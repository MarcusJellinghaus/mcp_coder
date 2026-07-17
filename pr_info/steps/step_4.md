# Step 4 — Resolver: frame semantics + degrade interaction + lifted_never

**Ref:** `pr_info/steps/summary.md`. One commit: tests + implementation + all checks
green. Depends on Step 3. Adds the frame-first step to `resolve()` (F4 ordering:
frame-elevation > degrade-override > config default).

## WHERE
- Modify `src/mcp_coder/icoder/permissions/resolver.py`
- Extend `tests/icoder/test_permissions_resolver.py`

## WHAT

```python
def _resolve_frame(
    tool_name: str,
    frame: PermissionFrame,
    config: PermissionConfig,
) -> Decision | None:
    """Frame step. Returns a Decision when the frame governs this tool, else None
    (base='inherit', undeclared -> fall through to config)."""
```
`resolve()` becomes: run `_resolve_frame` first when `frame is not None`; if it returns
a `Decision`, use it; otherwise fall through to `_resolve_config` (Step 3).

## HOW / precedence within the frame
- **Intra-frame `deny` beats `allow`** (DC5): check `deny` first.
- A frame **elevates only what it declares** — an `allow`-declared tool -> `ALWAYS`,
  and if the config base for that tool was `NEVER`, set `lifted_never=Policy.NEVER`
  (for I4.3's louder notice). Undeclared tools are **not** touched under
  `base="inherit"` (an authored `never` still applies via config).
- **Degrade ordering (F4):** the frame step runs *before* degrade. A declared tool
  resolves (`ALWAYS`/`NEVER`) even when `config.degraded`. Only the fall-through and
  `base="none"` sandbox paths consult `config.degraded`.
- Compute the "base policy" for `lifted_never` by calling
  `_resolve_config(tool_name, config)` and inspecting its `.policy`.

## ALGORITHM (_resolve_frame)
```
if any(matches(m, tool_name) for m in frame.deny):
    return Decision(NEVER, Frame(), None, None)          # deny wins, any base
if any(matches(m, tool_name) for m in frame.allow):
    base = _resolve_config(tool_name, config).policy
    lifted = Policy.NEVER if base is Policy.NEVER else None
    return Decision(ALWAYS, Frame(), None, lifted)        # elevates, beats degrade
# undeclared:
if frame.base == "none":                                  # sandbox
    if config.degraded:                                   # decision #8: degrade loosens
        return Decision(AFTER_APPROVAL, Degraded(errors=config.errors), None, None)
    return Decision(NEVER, Frame(), None, None)
return None                                               # base='inherit' -> config path
```

## DATA
- `_resolve_frame` -> `Decision | None`. Frame decisions carry `source=Frame()`
  (or `Degraded` for the sandbox+degrade case), `matched_rule is None`.
- `lifted_never` is `Policy.NEVER` only when a frame `allow` elevates over a config
  base of `NEVER`; otherwise `None`.

## TESTS (extend `test_permissions_resolver.py`)
- **Model A** (`base="inherit"`, `allow`, no `deny`): declared tool -> `ALWAYS`;
  undeclared inherited tool -> resolves via config/base (incl. an authored `never`
  that still applies).
- **Model B** (`base="inherit"`, `deny`): denied tool -> `NEVER` within frame; a
  non-denied tool -> resolves via config.
- **Model C** (`base="none"`): declared tool -> `ALWAYS`; **undeclared -> `NEVER`**;
  `frame=None` -> config-only (regression with Step 3 behaviour).
- **Elevation over never**: `allow`-declared tool whose config base is `never` ->
  `ALWAYS` with `lifted_never is Policy.NEVER`.
- **Intra-frame deny > allow**: a tool in both `allow` and `deny` -> `NEVER`.
- **Degrade x frame (F4)**: `config.degraded=True` + frame-**declared** tool ->
  `ALWAYS`; + non-frame tool (or `frame=None`) -> `ASK`.
- **Degrade x sandbox (decision #8)**: `base="none"` + **undeclared** tool +
  `config.degraded=True` -> `ASK`; same tool with healthy config -> `NEVER`.

## CHECKS
Four checks green (pylint, pytest with marker exclusions, mypy strict, lint-imports).
Full `resolve()` now satisfies every acceptance-criteria row in #1041.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Following TDD, first
> extend `tests/icoder/test_permissions_resolver.py` with every case in TESTS (all
> three frame models incl. model A, elevation-over-never, intra-frame deny>allow, and
> both degrade x frame and degrade x sandbox rows), then add `_resolve_frame` and wire
> the frame-first branch into `resolve()` per WHAT/HOW/ALGORITHM, preserving the F4
> ordering (frame-elevation > degrade > config default). Use MCP tools only. Run
> pylint, pytest (unit-test marker exclusions), mypy(strict), and lint-imports; fix
> until green. Commit as one change.
