# Step 4 — `toolScenarios` becomes `{base, allow, deny}` (D7)

Read [summary.md](./summary.md) §6 first.

D7 is **two** changes — the on-disk schema branch *and* the model type. `ScenarioBlock` is a retype of
an already-parsed structure, not a new parse.

## WHERE

- `src/mcp_coder/icoder/permissions/model.py` (modify — add `ScenarioBlock`, retype `scenarios`)
- `src/mcp_coder/icoder/permissions/loader.py` (modify — schema branch + build)
- `src/mcp_coder/icoder/permissions/__init__.py` (modify — export `ScenarioBlock`)
- `tests/icoder/test_permissions_loader_schema.py` (modify — invert the flat fixture)
- `tests/icoder/test_permissions_model.py` (modify)
- `tests/icoder/test_permissions_loader_layers.py` (modify — scenario asserts)
- `tests/icoder/test_permissions_loader_expand.py` (modify — scenario expansion)

## WHAT

```python
# model.py
@dataclass(frozen=True)
class ScenarioBlock:
    """A whole ``tools:`` block a skill can reference with ``use: <name>``."""

    base: Base                                  # REQUIRED — never defaulted (design §3)
    allow: tuple[Matcher, ...] = ()
    deny: tuple[Matcher, ...] = ()
    errors: tuple[str, ...] = ()                # expansion failures; non-empty => skill blocked


@dataclass(frozen=True)
class PermissionConfig:
    ...
    scenarios: Mapping[str, ScenarioBlock] = field(default_factory=dict)
```

```python
# loader.py
class _RawScenario(NamedTuple):
    """One layer's raw ``toolScenarios`` entry — members still tokens."""

    base: str
    allow: tuple[str, ...]
    deny: tuple[str, ...]
```

`_LayerResult.scenarios` becomes `dict[str, _RawScenario]`.

## HOW

- **Schema** (`build_settings_schema`): `toolScenarios` stops reusing `name_to_string_array` and
  becomes its own object branch:

  ```python
  scenario_block = {
      "type": "object",
      "additionalProperties": False,
      "required": ["base"],
      "properties": {
          "base": {"enum": ["inherit", "none"]},
          "allow": string_array,
          "deny": string_array,
      },
  }
  ```
  with `"toolScenarios": {"type": "object", "additionalProperties": scenario_block}`.
  `name_to_string_array` stays, still used by `toolGroups`.
- `_load_layer`: read `base`/`allow`/`deny` per scenario, validate the member tokens with
  `_token_errors` (both sides), store a `_RawScenario` with raw tokens. The schema already guarantees
  `base` is present and one of the two literals, so no extra validation is needed.
- Phase 2 merge and the shadow warning are unchanged in shape — the map value type changes only.
- Phase 3: build `ScenarioBlock(base, …)` by expanding each `allow`/`deny` member token against the
  merged **group** map (`raw_groups`) — a `@x` among scenario members is a *group* reference, so
  resolving it against `raw_scenarios` would report it as unknown. Change step 3's `_expanded_members`
  to return `(matchers, errors)` so the errors are kept, not discarded. A side with any expansion error
  still fails **wholesale** (`()`, never partial), and the failure is **never silent**:
  - a failed `deny` side forces `base` to `"none"` — the same fail-closed rule as a dropped skill deny
    (D10 / I2.4's D3), so an emptied deny can never leave an `inherit` block with no denies;
  - every expansion error (either side) is recorded on `ScenarioBlock.errors` (naming the scenario) and
    logged with `logger.warning`; step 5's `build_frame` blocks any `use:` of a block with errors.
  - The errors do **not** go into `config.errors`/`degraded`: that would force the whole session to
    `ask` for one scenario's typo, which D10 rules out. Failing the referencing skill is the scoped
    equivalent of D11's "the referencing rule degrades".
- Narrow `base` inline: `block_base: Base = "inherit" if raw.base == "inherit" else "none"`. Do **not**
  import `as_base` from `skill_frame` — the loader must not depend on the frame builder.
- `emit_schema` is content-gated, so the regenerated `settings.schema.json` in any repo with
  `.icoder/` will be rewritten once. Expect (and commit) that churn if this repo has one.

## ALGORITHM

```
_load_layer, toolScenarios branch:
    for name, block in data.get("toolScenarios", {}).items():
        allow, deny = tuple(block.get("allow", [])), tuple(block.get("deny", []))
        for token in allow + deny: errors += _token_errors(token, path)
        scenarios[name] = _RawScenario(block["base"], allow, deny)

phase 3:
    # _expanded_members now returns (matchers, errors): every member token expanded
    # against the merged GROUP map (raw_groups), never raw_scenarios; a side fails
    # wholesale (()) on any error, and the errors are kept.
    for name, raw in raw_scenarios.items():
        allow, allow_errs = _expanded_members(raw.allow, raw_groups)
        deny, deny_errs = _expanded_members(raw.deny, raw_groups)
        base = "none" if deny_errs else narrow(raw.base)      # failed deny => fail closed
        errs = tuple(f"scenario {name!r}: {e}" for e in allow_errs + deny_errs)
        for e in errs: logger.warning("permission config: %s", e)
        scenarios[name] = ScenarioBlock(base, allow, deny, errs)
    # errs stay out of config.errors — step 5 blocks the referencing skill instead
```

## DATA

- `PermissionConfig.scenarios: Mapping[str, ScenarioBlock]` — expanded, ref-free, `base` always a
  `Base` literal; `errors` non-empty iff a side failed to expand (then that side is `()`, and a failed
  `deny` has also forced `base="none"`).
- `_LayerResult.scenarios: dict[str, _RawScenario]` — raw tokens, layer-local.

## Tests (write first)

`tests/icoder/test_permissions_loader_schema.py`:

1. **Invert** `test_schema_accepts_full_valid_config` (`:109-110`): the flat
   `toolScenarios: {"review": [...]}` becomes `{"review": {"base": "none", "allow": [...]}}`.
2. New: a flat array value is now **rejected**, and the message names `toolScenarios`.
3. New: a block **missing `base`** is rejected (D7: `base` is required, never defaulted).
4. New: `base: "maybe"` is rejected; an unknown key inside the block is rejected.

`tests/icoder/test_permissions_model.py`:

5. `ScenarioBlock` requires `base` and defaults `allow`/`deny` to `()`.
6. `PermissionConfig.scenarios` round-trips a `ScenarioBlock` mapping (update the existing
   `cfg.scenarios == scn` test at `:282` and the empty-default test at `:88`).

`tests/icoder/test_permissions_loader_layers.py`:

7. Update `test_load_layer_populates_groups_and_scenarios` to the new on-disk shape and the
   `_RawScenario` value.

`tests/icoder/test_permissions_loader_expand.py`:

8. A scenario whose `allow` contains `@group` expands to the group's members, with `base` preserved.
9. A scenario referencing a group defined in **another layer** resolves (same merged-map guarantee).
10. An unreferenced scenario with an unknown ref in `allow` leaves `degraded is False`, the `allow`
    side is `()` (wholesale, not partial), and `ScenarioBlock.errors` names the scenario and the ref.
11. A scenario `{base: "inherit", deny: ["@nope"]}` → `deny == ()`, `base == "none"` (fail closed, not
    an `inherit` block with no denies), `errors` non-empty, `degraded is False`.

## LLM prompt

> Implement **step 4** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_4.md`.
> Read the summary first (§6) for D7 and why `base` is required.
>
> Test-driven: write/invert the eleven test cases listed first, watch them fail, then change the schema
> branch, add `ScenarioBlock`, retype `PermissionConfig.scenarios`, and build the blocks in the
> loader's expansion phase.
>
> `base` must be **required** in the schema and un-defaulted in `ScenarioBlock`. Keep
> `name_to_string_array` for `toolGroups`. Do not import anything from `skill_frame` into `loader.py` —
> narrow `base` with an inline ternary. Expand scenario members against the merged **group** map with
> step 3's `_expanded_members` (now returning its errors): a side with any error fails wholesale (`()`,
> never partial), a failed `deny` forces `base="none"`, and every error is logged and recorded on
> `ScenarioBlock.errors` — never silently dropped. Keep them out of `config.errors` so one broken
> scenario does not degrade the whole session (D10); step 5 blocks the skill that uses it.
>
> Then run the checks listed at the end of the summary. If the repo has an `.icoder/` directory, the
> regenerated `settings.schema.json` is expected churn — include it. One commit.
