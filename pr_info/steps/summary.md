# I2.1 — Permission model + resolver (#1041)

## Goal

Build the pure, provider-agnostic **core** of the iCoder permission system: an
in-memory data **model** plus a deterministic resolver
`resolve(tool_name, args, frame, config) -> Decision` that maps any tool call to
`ALWAYS | AFTER_APPROVAL | NEVER` **plus its source**. No file/network/clock/global
access; fully unit-testable. Everything downstream (config loaders I2.2, langchain
gateway I2.3, groups I4.1, arg-matching I5.4, `/permissions` UI I4.2/I4.3) builds on
this.

This issue defines **structure + resolution semantics only**. Group/scenario
*matching*, `@ref` expansion, and arg-predicate *evaluation* are deferred (structure
is defined and populatable, but not exercised here).

## Architectural / design changes

- **New pure leaf package** `src/mcp_coder/icoder/permissions/` with three modules,
  mirroring the frozen-dataclass + tagged-union style already used in
  `icoder/core/types.py` (`Action = Quit | ClearOutput | ...`):
  - `model.py` — frozen dataclasses / enum only (no logic, no I/O).
  - `matcher.py` — the "matcher engine": parse + rank + match (pure string logic).
  - `resolver.py` — the single `resolve()` entry point.
- **Dependency direction** is strictly linear and acyclic:
  `resolver.py -> matcher.py -> model.py`. The package imports **nothing** from
  `icoder.ui`, `icoder.services`, langchain, or Textual.
- **Import-linter contract added** (`.importlinter`) pinning the package leaf-level.
  No `tach.toml` change is needed: with `exact = false` the subpackage inherits the
  `icoder` (presentation) layer automatically, and the leaf guarantee is enforced by
  the new forbidden contract.
- **KISS choices** (within the settled design decisions of #1041/#1037):
  - `Policy` is a plain `enum.Enum` (closed set, no payload); `Source` is a tagged
    union of frozen dataclasses (members carry data — decision #3).
  - Specificity is a `NamedTuple` (`arg_rank`, `concrete_tool`, `concrete_server`) —
    compares lexicographically for free **and** exposes the `arg_rank` field name
    downstream issues rely on.
  - Wildcards are the `"*"` string sentinel on `server`/`tool` — no type hierarchy.
  - The parser returns failures **as data** (`tuple[list[Matcher], list[str]]`) — no
    logging (keeps the pure package honest); the *caller* (I2.2/I2.4) emits warnings.
  - `config.rules` is one flat **ordered** `tuple[Rule, ...]`; each `Rule` carries its
    `layer`, tuple order = declaration order (drives the final tie-break).
  - `resolve()` is one linear function with two small helpers
    (`_resolve_frame`, `_resolve_config`).

## Precedence (design §5 — uniform specificity)

1. **Frame first.** A frame-declared tool -> `ALWAYS` (may override base/authored
   `never`, recording `lifted_never`); intra-frame `deny` beats `allow`. `base="none"`
   undeclared -> `NEVER` (healthy config) / `ASK` (degraded — the one place degrade
   *loosens*). `base="inherit"` undeclared -> fall through to config. Frame elevation
   beats degrade (F4).
2. **Config rules.** Most-specific matcher wins (primary) -> `never>ask>allow` at equal
   specificity -> layer order (`user->project->local->runtime`) -> declaration order.
   A degraded config forces the whole config path to `ASK` (fail-closed).
3. **No match.** `ASK` if `config.degraded` else `default_policy` (`ALWAYS` when unset).

`resolve()` returns the true 3-valued `Decision`; the `ask->deny` collapse for M2 is
the caller's job (I2.3).

## Folders / modules / files

**Created**
- `src/mcp_coder/icoder/permissions/__init__.py` — public exports.
- `src/mcp_coder/icoder/permissions/model.py` — data model.
- `src/mcp_coder/icoder/permissions/matcher.py` — parse + rank + match.
- `src/mcp_coder/icoder/permissions/resolver.py` — `resolve()`.
- `tests/icoder/test_permissions_model.py`
- `tests/icoder/test_permissions_matcher.py`
- `tests/icoder/test_permissions_resolver.py`

**Modified**
- `.importlinter` — add `permissions_leaf_isolation` forbidden contract.
- `vulture_whitelist.py` — whitelist the intentionally-unread `args` param of
  `resolve()` (decision #9).

## Steps (one commit each)

1. **step_1.md** — `model.py` + `__init__.py` + import-linter contract (data types).
2. **step_2.md** — `matcher.py`: `parse_matcher`, `specificity`, `matches`.
3. **step_3.md** — `resolver.py`: config precedence + default + config-path degrade
   (`frame=None`).
4. **step_4.md** — `resolver.py`: frame semantics (models A/B/C, `base=none/inherit`,
   frame x degrade, degrade x sandbox) + `lifted_never`.

Each step is TDD (tests first, then implementation) and must leave pylint, pytest, and
mypy(strict) green before commit.
