# Step 1 — Resolver cross-layer precedence (partially addresses #1154)

> Prerequisite for steps 4–5. **Skip this step entirely if #1154 has already landed on `main`.**
> Steps 2–3 do not depend on it.
>
> **This step does NOT complete #1154 and must not close it.** #1154 specifies hoisting
> `_LAYER_ORDER` itself above `Policy.rank`, and its AC1 reads "at equal specificity a higher layer
> wins over a lower layer regardless of `allow`/`ask`" — which includes a `project` `allow` beating
> a `user` `ask`. This step deliberately delivers only the `local`/`runtime` half of that (see
> **Deliberately narrow** below), so #1154's AC1 stays unmet for the `user` ↔ `project` pair.
> Keep `#1154` out of any closing keyword in the commit message, and leave the issue open with a
> comment recording that its stated key and AC1 need amending — the `user` ↔ `project` widening is
> security-relevant and needs its own decision, not a side effect of #1046.

## Goal

At equal specificity a **personal** layer (`local`, `runtime`) must win over a shared authored one
(`user`, `project`) regardless of `allow` vs `ask`, so that a persisted `local` `allow` overrides
an authored `project` or `user` `ask` — while a `never` in any layer still wins at equal
specificity (fail closed), and the `user` ↔ `project` relationship is left exactly as it is today.

**Deliberately narrow.** Hoisting the whole of `_LAYER_ORDER` above `Policy.rank` — the shape
#1154 spells out — would also flip `user` ↔ `project`: a repo-committed `.icoder/settings.json`
`"allow"` would silently override the user's own global `"ask"` at equal specificity. That is a
security-relevant widening #1046 never asks for — the persist target is only ever `local`, and the
runtime grant only ever `runtime`. So what is hoisted is a **personal bit**, not the layer order.

This is a knowing divergence from #1154, not an oversight: it satisfies everything #1046's persist
scope needs while leaving the `user` ↔ `project` contest for #1154 to decide on its own merits.
Hence the header note — #1154 stays open, and its ACs and proposed key need rewriting before
anyone implements the remainder.

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/resolver.py` | `_PERSONAL_LAYERS` + `_rule_sort_key` key order + three docstring/comment sites |
| `tests/icoder/test_permissions_resolver.py` | Seven new cases; docstring notes on three existing tests |

## WHAT

```python
_PERSONAL_LAYERS = frozenset({"local", "runtime"})

def _rule_sort_key(ir: tuple[int, Rule]) -> tuple[Specificity, int, int, int, int, int]:
```

Signature is unchanged apart from the return type gaining a fifth and sixth `int`. One new
module-level constant. No new call sites, no public API change.

## ALGORITHM

```
index, rule = ir
return (specificity(rule.matcher),                 # primary, unchanged
        1 if rule.policy is Policy.NEVER else 0,   # NEW: never dominates, any layer
        1 if rule.layer in _PERSONAL_LAYERS else 0,# NEW: local/runtime outrank user/project
        rule.policy.rank,                          # unchanged position — still decides
                                                   # ask>allow WITHIN a group
        _LAYER_ORDER[rule.layer],                  # unchanged position, below rank
        -index)                                    # earlier declaration wins
```

Both new bits sit **above** `Policy.rank`; everything below it is byte-for-byte the old key. The
result is exactly two behaviour changes, both required by #1046: a `local`/`runtime` `allow` now
beats a `user`/`project` `ask`, and a `never` is no longer beaten by a higher layer.

## DATA

`_rule_sort_key` returns a 6-tuple ranked by `max()`. `_LAYER_ORDER` (`user 0 < project 1 <
local 2 < runtime 3`) and `Policy.rank` (`NEVER 2 > AFTER_APPROVAL 1 > ALWAYS 0`) are unchanged,
and `_LAYER_ORDER` keeps its old position below `Policy.rank` — it still breaks ties *within* the
personal group (`runtime` over `local`) and *within* the shared group (`project` over `user`).

## HOW — integration points

`_resolve_config`'s R14 runtime partition is **structurally unchanged**: it keeps computing
`top_authored` with `_rule_sort_key` and keeps the `blocked` short-circuit, both of which inherit
the new key. Only its explanatory comment changes.

Three prose sites still describe the old order and must be restated. Do not leave any of them
implying the key is 4 keys, and do not let any of them say the *layer order* was hoisted — it was
not; only the personal bit was:

1. `resolver.py` module docstring (~line 9) — "specificity (primary) -> `never>ask>allow` ->
   layer order ..." becomes "specificity (primary) -> `never` -> personal layers
   (`local`/`runtime`) -> `ask>allow` -> layer order -> declaration order".
2. `_rule_sort_key`'s `Returns:` block (~line 46) — "The 4-key precedence tuple ..." becomes the
   6-key description, naming what each of the two new bits is for.
3. `_resolve_config`'s partition comment (~line 171) — currently justifies the partition with
   "`_LAYER_ORDER` is only the *third* sort key and `Policy.rank` puts AFTER_APPROVAL above
   ALWAYS". `_LAYER_ORDER` is now the *fifth* key and `Policy.rank` the fourth, but the personal
   bit above both already lifts `runtime` over an authored `ask`, so restate it: the partition
   survives because it is *stronger* than the personal bit — it ignores specificity, which the
   personal bit does not.
4. `tests/icoder/test_permissions_resolver.py` module docstring (~line 5) carries the same
   sentence; update it too.

## The fail-closed bound (must hold after the change)

A **personal** layer (`local`, `runtime`) **may** override a shared authored layer (`user`,
`project`) for `allow` ↔ `ask` at equal specificity, and anything may override anything at
strictly greater specificity. Nothing may override a `never`/`deny` at equal specificity (the
`never` bit dominates) or at greater specificity (specificity is primary). The `user` ↔ `project`
contest is **unchanged in both directions**: `Policy.rank` still decides it, so a project-authored
`allow` cannot silently override the user's global `ask`. The `config.degraded → ASK` path is
untouched.

## TDD — tests first

Add to `tests/icoder/test_permissions_resolver.py`. Write all seven, watch the first fail against
the current key, then change the key.

| Test | Setup | Expect |
|---|---|---|
| `test_local_allow_beats_project_ask_at_equal_specificity` | `local` `allow` + `project` `ask`, same matcher | `ALWAYS`, source `local` |
| `test_user_ask_still_beats_project_allow_at_equal_specificity` | `user` `ask` + `project` `allow`, same matcher | `AFTER_APPROVAL`, source `user` — the non-personal pair is untouched, and a committed repo config must not downgrade the user's own `ask` |
| `test_local_allow_loses_to_project_never_at_equal_specificity` | `local` `allow` + `project` `deny`, same matcher | `NEVER`, source `project` |
| `test_broad_local_allow_loses_to_specific_project_never` | `local` `allow` on `s__*` + `project` `deny` on `s__t` | `NEVER` |
| `test_broad_local_allow_loses_to_specific_project_ask` | `local` `allow` on `s__*` + `project` `ask` on `s__t` | `AFTER_APPROVAL` (specificity primary) |
| `test_specific_local_always_beats_broad_project_never` | `local` `allow` on `s__t` + `project` `deny` on `s__*` | `ALWAYS` (§5 carve-out) |
| `test_user_never_beats_local_allow_at_equal_specificity` | `user` `deny` + `local` `allow`, same matcher | `NEVER` (bound is layer-direction-agnostic) |

Two existing tests keep passing but change meaning; add a docstring note to each rather than
editing the assertions:

- `test_equal_specificity_ask_beats_allow` (`:67`) — unaffected, because **both rules are in layer
  `user`**. Say so, or a reader will think it pins ask-over-allow across layers.
- `test_runtime_grant_beats_authored_ask_at_equal_specificity` (`:521`) — still passes, but under
  the new key it would pass **even if the R14 runtime stage were deleted**, since the personal bit
  lifts `runtime` over an authored `ask` on its own. Note this, so it is clear that
  `test_broad_runtime_grant_beats_more_specific_authored_ask` is now the only regression cover for
  the stage itself.

`test_no_runtime_rules_leaves_authored_precedence_unchanged` (`:612`) needs no note: its `allow` is
`user` and its `ask` is `project`, both non-personal, so the `ask` still wins on `Policy.rank` for
exactly the reason it always did.

Every other existing test in the file must pass untouched.

## Acceptance

- The seven new cases pass; the full `tests/icoder/test_permissions_resolver.py` passes.
- All #1045 R14 expectations unchanged.
- `user` ↔ `project` precedence is provably unchanged (the second new case).
- The four prose sites describe the 6-key order.
- pylint / mypy(strict) / ruff clean.

## Commit

`fix(permissions): let a personal layer win at equal specificity (#1046)`

Body: `Partially addresses #1154 — the user <-> project half is not implemented.`
The reference is deliberately `#1046`, and deliberately not a closing keyword on `#1154`: the step
leaves that issue's AC1 unmet, so it must survive this PR.

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only: the cross-layer precedence fix in
> `src/mcp_coder/icoder/permissions/resolver.py`. It **partially** addresses #1154 — do not close
> that issue and do not use a closing keyword for it in the commit message.
>
> Work TDD: first add the seven new test functions listed in step_1.md to
> `tests/icoder/test_permissions_resolver.py` and confirm the first one fails against the current
> `_rule_sort_key`. Then change `_rule_sort_key` to the 6-key order given in the ALGORITHM section
> and confirm all seven pass with no other test in that file breaking.
>
> Hoist a **personal-layer bit** (`local`/`runtime`) above `Policy.rank`, not `_LAYER_ORDER`
> itself: `_LAYER_ORDER` keeps its old position below `Policy.rank`, so `user` ↔ `project` keeps
> today's behaviour. `test_user_ask_still_beats_project_allow_at_equal_specificity` pins that and
> must pass both before and after the change.
>
> Then update the four prose sites listed under HOW so none of them still describes a 4-key tuple,
> and add the two docstring notes to the existing tests that change meaning.
> Do not change `_resolve_config`'s structure — only its comment.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff and the fast unit test selection from the
> summary. Make exactly one commit when everything passes.
