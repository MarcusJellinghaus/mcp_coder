# Step 2 — Build the frame (`skill_frame.py`) + `Base` Literal

**Read `pr_info/steps/summary.md` first.** This is the semantic half: the *one* place that maps any
skill to a `PermissionFrame`, implementing the whole mapping table in the summary. It is **pure** — no
I/O, no logging, no clock, and it takes **data, not a `ClaudeSkill`** (so I5.1 can call it from a
raw-frontmatter scan). Blocked-ness is decided **here** (see summary's deviation note) and carried on
`SkillFrame.blocked_reason`.

## WHERE
- **Modified:** `src/mcp_coder/icoder/permissions/model.py` (add `Base` Literal, retype `PermissionFrame.base`)
- **New:** `src/mcp_coder/icoder/permissions/skill_frame.py`
- **New tests:** `tests/icoder/test_skill_frame.py`
- **Modified:** `.importlinter` (add `skill_frame` to `permissions_leaf_isolation` source_modules)
- **Modified:** `src/mcp_coder/icoder/permissions/gateway.py` — one-line typing touch only (annotate the
  `base` local in the still-present `build_legacy_frame` so mypy accepts the `Base` literals; the
  function itself is deleted in Step 3).

## WHAT
```python
# model.py
Base = Literal["inherit", "none"]
# PermissionFrame.base: Base          # was: str

# skill_frame.py
from mcp_coder.icoder.permissions.matcher import parse_matcher
from mcp_coder.icoder.permissions.model import Base, Matcher, PermissionFrame
from mcp_coder.icoder.permissions.skill_tools import SkillToolsBlock

@dataclass(frozen=True)
class SkillFrame:
    frame: PermissionFrame | None            # None only when NO declaration at all
    warnings: tuple[str, ...] = ()           # per-invocation, shown as permission_warning (Step 3)
    blocked_reason: str | None = None        # non-None → skill refuses to run (Step 4)

def build_frame(
    tools_block: SkillToolsBlock | None,
    allowed_tools: Sequence[str] | None,
    *,
    enforce_skill_tools: bool,
) -> SkillFrame: ...
```

## HOW
- `skill_frame.py` imports only the permission leaf (`matcher`, `model`, `skill_tools`) — no `icoder.*`
  outside `permissions`, no langchain, no UI. Add it to `permissions_leaf_isolation` source_modules.
- Internal helper classifies one token per D5 (below); reused for both `allow` and `deny` sides.

## ALGORITHM
Token classifier `classify(token, *, side) -> (matchers, warning|None, dropped: bool)`:
```
if token.startswith("@"):            return ([], warn(@ref unsupported, I4.1), dropped=True)
if not token.startswith("mcp__"):    return ([], None, dropped=False)     # non-mcp → ignored (silent)
ms, errs = parse_matcher(token)
if errs:                             return ([], warn(unparseable), dropped=True)
if any(m.arg is not None for m in ms): warn(arg-scoped elevates whole tool until #1053)
return (ms, that_warning_or_None, dropped=False)
```
`build_frame`:
```
if tools_block is None:              # legacy path
    if not allowed_tools: return SkillFrame(frame=None)
    allow, warns, _ = classify_all(allowed_tools, side="allow")
    base: Base = "none" if enforce_skill_tools else "inherit"
    return SkillFrame(PermissionFrame(base, tuple(allow)), tuple(warns),
                      blocked_reason=two_empties(base, allowed_tools, allow))
# rich path
if tools_block.errors:               # malformed → fail-closed frame, blocked
    return SkillFrame(PermissionFrame("none"), tuple(tools_block.errors), blocked_reason="; ".join(errors))
if tools_block.use is not None:      # bare use: → blocked (D7b)
    return SkillFrame(PermissionFrame("none"), (), blocked_reason="declares use: <...>, unsupported until I4.1")
allow, aw, _        = classify_all(tools_block.allow, side="allow")
deny,  dw, d_drop   = classify_all(tools_block.deny,  side="deny")
base: Base = "none" if d_drop else tools_block.base   # dropped deny entry → force none (fail-closed, D3)
warns = aw + dw + (["deny narrowed to base=none because an entry was dropped"] if d_drop else [])
return SkillFrame(PermissionFrame(base, tuple(allow), tuple(deny)), tuple(warns),
                  blocked_reason=two_empties(base, tools_block.allow, allow))
```
`two_empties(base, declared, parsed) -> reason|None`: return a reason **iff**
`base == "none" and declared and not parsed` (D8 — absorbs "declared but nothing survived"); else `None`.

## DATA
- `SkillFrame.frame is None` **only** for "no declaration at all". A legacy Bash-only skill with the
  flag off yields `PermissionFrame("inherit", allow=())` (a no-op frame, provenance kept) — *not* `None`.
- `blocked_reason is None` ⇒ skill runs; non-`None` ⇒ Step 4 refuses it. The frame is still returned
  (fail-closed `base="none"`) for I5.1's effective-policy report.
- `warnings` are data, never logged.

## TESTS (write first) — one per mapping-table row / AC
Model A (`inherit`+`allow`), B (`inherit`+`deny`), C (`none`+`allow`); `none, allow: []` → runs, no
warning, `blocked_reason is None`; `none` + declared allow all-dropped → `blocked_reason` set; bare
`use:` → blocked; `inherit` all-dropped → runs, `frame.allow == ()`, `frame.deny == ()`; **dropped
`deny` entry forces `base="none"`** asserted for both a `@ref` and an unparseable `mcp__` token;
`@ref` in `allow` dropped + warned, no model change; non-`mcp__` token ignored (no warning); `mcp__s__*`
wildcard produces a matcher (enforced); arg-scoped `allow` token kept + warning naming `#1053`; legacy
`base="inherit"` when `enforce_skill_tools=False` and `base="none"` when `True`; neither block →
`frame is None`; malformed block → fail-closed `base="none"` frame + `blocked_reason`. Add a mypy-level
check that `PermissionFrame.base` rejects a non-literal (implicit via strict run).

## LLM PROMPT
> Implement Step 2 of `pr_info/steps/summary.md` (see `pr_info/steps/step_2.md`). Using TDD, first
> write `tests/icoder/test_skill_frame.py` with one test per row of the summary's mapping table and per
> acceptance criterion. Then add `Base = Literal["inherit","none"]` to `permissions/model.py` and
> retype `PermissionFrame.base`; create the pure `permissions/skill_frame.py` (`SkillFrame` +
> `build_frame` with the token classifier and the two-empties/deny-asymmetry rules); add `skill_frame`
> to `permissions_leaf_isolation` in `.importlinter`; and annotate the `base` local in `gateway.py`'s
> `build_legacy_frame` so it type-checks against `Base` (do not delete it yet). Run pylint, mypy
> (strict), pytest (`-n auto` with the unit-only `-m "not ..."` exclusions) and `lint-imports` until
> green. One commit.
