# Step 1 — Resolver cross-layer precedence (issue #1154)

> Prerequisite for steps 4–5. **Skip this step entirely if #1154 has already landed on `main`.**
> Steps 2–3 do not depend on it.

## Goal

At equal specificity a higher config layer must win over a lower one regardless of `allow` vs
`ask`, so that a persisted `local` `allow` overrides an authored `project` `ask` — while a
lower-layer `never` still wins at equal specificity (fail closed).

## WHERE

| File | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/resolver.py` | `_rule_sort_key` key order + three docstring/comment sites |
| `tests/icoder/test_permissions_resolver.py` | Six new cases; docstring notes on three existing tests |

## WHAT

```python
def _rule_sort_key(ir: tuple[int, Rule]) -> tuple[Specificity, int, int, int, int]:
```

Signature is unchanged apart from the return type gaining a fifth `int`. No new module, no new
call sites, no public API change.

## ALGORITHM

```
index, rule = ir
return (specificity(rule.matcher),               # primary, unchanged
        1 if rule.policy is Policy.NEVER else 0, # NEW: never dominates, any layer
        _LAYER_ORDER[rule.layer],                # MOVED above policy.rank
        rule.policy.rank,                        # now only separates ask from allow
        -index)                                  # earlier declaration wins
```

## DATA

`_rule_sort_key` returns a 5-tuple ranked by `max()`. `_LAYER_ORDER` (`user 0 < project 1 <
local 2 < runtime 3`) and `Policy.rank` (`NEVER 2 > AFTER_APPROVAL 1 > ALWAYS 0`) are unchanged.

## HOW — integration points

`_resolve_config`'s R14 runtime partition is **structurally unchanged**: it keeps computing
`top_authored` with `_rule_sort_key` and keeps the `blocked` short-circuit, both of which inherit
the new key. Only its explanatory comment changes.

Three prose sites still describe the old order and must be restated. Do not leave any of them
saying `Policy.rank` outranks the layer:

1. `resolver.py` module docstring (~line 9) — "specificity (primary) -> `never>ask>allow` ->
   layer order ..."
2. `_rule_sort_key`'s `Returns:` block (~line 46) — "The 4-key precedence tuple ..." becomes the
   5-key description.
3. `_resolve_config`'s partition comment (~line 171) — currently justifies the partition with
   "`_LAYER_ORDER` is only the *third* sort key and `Policy.rank` puts AFTER_APPROVAL above
   ALWAYS". After this change layer is still third (the hoisted `never` bit takes slot 2) but now
   outranks `Policy.rank`, so restate the justification in those terms: the partition survives
   because it is *stronger* than layer order — it ignores specificity, which layer order does not.
4. `tests/icoder/test_permissions_resolver.py` module docstring (~line 5) carries the same
   sentence; update it too.

## The fail-closed bound (must hold after the change)

A higher layer **may** override a lower layer for `allow` ↔ `ask` at equal specificity, and for
anything at strictly greater specificity. A higher layer **may not** override a lower-layer
`never`/`deny` at equal specificity (the `never` bit dominates) or at greater specificity
(specificity is primary). The `config.degraded → ASK` path is untouched.

## TDD — tests first

Add to `tests/icoder/test_permissions_resolver.py`. Write all six, watch the first fail against
the current key, then change the key.

| Test | Setup | Expect |
|---|---|---|
| `test_higher_layer_allow_beats_lower_layer_ask_at_equal_specificity` | `local` `allow` + `project` `ask`, same matcher | `ALWAYS`, source `local` |
| `test_higher_layer_allow_loses_to_lower_layer_never_at_equal_specificity` | `local` `allow` + `project` `deny`, same matcher | `NEVER`, source `project` |
| `test_broad_higher_layer_allow_loses_to_specific_lower_layer_never` | `local` `allow` on `s__*` + `project` `deny` on `s__t` | `NEVER` |
| `test_broad_higher_layer_allow_loses_to_specific_lower_layer_ask` | `local` `allow` on `s__*` + `project` `ask` on `s__t` | `AFTER_APPROVAL` (specificity primary) |
| `test_specific_higher_layer_always_beats_broad_lower_layer_never` | `local` `allow` on `s__t` + `project` `deny` on `s__*` | `ALWAYS` (§5 carve-out) |
| `test_user_never_beats_local_allow_at_equal_specificity` | `user` `deny` + `local` `allow`, same matcher | `NEVER` (bound is layer-direction-agnostic) |

Three existing tests keep passing but change meaning; add a docstring note to each rather than
editing the assertions:

- `test_equal_specificity_ask_beats_allow` (`:67`) — unaffected, because **both rules are in layer
  `user`**. Say so, or a reader will think it pins ask-over-allow across layers.
- `test_no_runtime_rules_leaves_authored_precedence_unchanged` (`:612`) — still passes for a
  **different reason**: its `allow` is `user` and its `ask` is `project`, so the `ask` now wins on
  layer order rather than on `Policy.rank`.
- `test_runtime_grant_beats_authored_ask_at_equal_specificity` (`:521`) — still passes, but under
  the new key it would pass **even if the R14 runtime stage were deleted**, since
  `_LAYER_ORDER["runtime"] = 3` wins on layer alone. Note this, so it is clear that
  `test_broad_runtime_grant_beats_more_specific_authored_ask` is now the only regression cover for
  the stage itself.

Every other existing test in the file must pass untouched.

## Acceptance

- The six new cases pass; the full `tests/icoder/test_permissions_resolver.py` passes.
- All #1045 R14 expectations unchanged.
- The four prose sites describe the 5-key order.
- pylint / mypy(strict) / ruff clean.

## Commit

`fix(permissions): let a higher layer win at equal specificity (#1154)`

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`.
>
> Implement step 1 only: the cross-layer precedence fix in
> `src/mcp_coder/icoder/permissions/resolver.py` (issue #1154).
>
> Work TDD: first add the six new test functions listed in step_1.md to
> `tests/icoder/test_permissions_resolver.py` and confirm the first one fails against the current
> `_rule_sort_key`. Then change `_rule_sort_key` to the 5-key order given in the ALGORITHM section
> and confirm all six pass with no other test in that file breaking.
>
> Then update the four prose sites listed under HOW so none of them still says `Policy.rank`
> outranks the layer, and add the three docstring notes to the existing tests that change meaning.
> Do not change `_resolve_config`'s structure — only its comment.
>
> Run `run_format_code`, then pylint, mypy(strict), ruff and the fast unit test selection from the
> summary. Make exactly one commit when everything passes.
