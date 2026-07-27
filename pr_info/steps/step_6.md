# Step 6 — Public `load_permission_config` (merge + degrade + provenance)

See [summary.md](./summary.md). The public entry point: discover, load each
layer, merge, apply fail-closed degrade, emit the schema, and export from the
package. Includes the end-to-end `resolve()` fail-closed assertion.

## WHERE
- `src/mcp_coder/icoder/permissions/loader.py` (extend)
- `src/mcp_coder/icoder/permissions/__init__.py` (export)
- `tests/icoder/test_permissions_loader.py` (extend)

## WHAT
```python
def load_permission_config(project_dir: Path) -> PermissionConfig:
    """Load all layers into a merged PermissionConfig.

    Concatenates good layers' rules (resolver owns precedence); defaultMode and
    groups/scenarios are last-layer-wins. A present-but-broken layer contributes
    nothing and sets degraded=True (+ errors). Emits settings.schema.json as a
    gated side effect. All layers absent -> default_policy=None (backward compat).
    """
```
Add `load_permission_config` to `__init__.py`'s imports and `__all__`.

## HOW
- Imports `PermissionConfig`, `Policy` from `.model`; uses Step 3–5 helpers.
- `logging.getLogger(__name__)` for diagnostics (mirror `skills.py`).
- Call `emit_schema(project_dir)` once (gated write; ignore return).
- Shadowed group/scenario name (redefined by a higher layer) → `logger.warning`.
- On degrade, `logger.error` each collected error **and** put them in
  `PermissionConfig.errors`.
- `Matcher.origin` and `Degraded.layer` stay `None` (not populated here).

## ALGORITHM
```
emit_schema(project_dir)
layers = _discover_layers(project_dir)
if not layers: return PermissionConfig()          # default_policy None -> resolver ALWAYS
rules=[]; groups={}; scenarios={}; errors=[]; default=None
for tag, path in layers:                           # lowest -> highest
    r = _load_layer(tag, path)
    if r.errors: errors += r.errors; continue      # broken layer grants nothing
    rules += r.rules
    if r.default_policy is not None: default = r.default_policy   # last-wins
    for name, ms in r.groups.items():
        if name in groups: logger.warning("group %r shadowed by %s", name, path)
        groups[name] = ms
    (same for scenarios)
degraded = bool(errors)
for e in errors: logger.error("permission config: %s", e)
return PermissionConfig(tuple(rules), default, groups, scenarios, degraded, tuple(errors))
```

## DATA
`PermissionConfig` — `rules` (concatenated good-layer rules with provenance),
`default_policy` (last-wins or None), `groups`/`scenarios` (last-wins by name),
`degraded` (True iff any present layer failed), `errors` (all diagnostics).

## TESTS (write first)
- Two good layers → rules concatenated; each rule keeps its own `source_path`
  and `layer`; `defaultMode` from the higher layer wins.
- **Fail-closed (three distinct assertions):** one good layer + one broken layer →
  (a) on the returned config: `degraded is True`, `errors` non-empty, the good
  layer's rules **are present**, the broken layer's rules are **absent**;
  (b) separately, `resolve("mcp__x__y", None, None, config).policy ==
  Policy.AFTER_APPROVAL` (never a silent `allow`) even though the good layer had
  an `allow` rule / `defaultMode: allow`. (`resolve()` returns a `Decision`;
  assert on its `.policy`.);
  (c) the degrade diagnostic **is emitted to the logger** — assert via `caplog`
  (at `ERROR`) that the broken-layer error is logged, not only surfaced in
  `errors` (AC: "the diagnostic is emitted (`logger` + `PermissionConfig.errors`)").
- All three layers absent → `degraded is False`, `default_policy is None`, and
  `resolve(...).policy == Policy.ALWAYS` (backward-compat opt-in).
- Shadowed group name across layers logs a warning (use `caplog`) and the higher
  layer's definition wins.
- `emit_schema` accept/reject already covered in Step 3; here assert
  `load_permission_config` writes the schema when `.icoder/` exists.
- `__init__` exports `load_permission_config`.

## VERIFICATION
- All four MCP checks pass.
- `run_lint_imports_check()` PASSED (both `permissions_core_purity` and
  `permissions_leaf_isolation`).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_6.md`. Implement Step 6
> with TDD: add merge/degrade/provenance tests first — including the two-part
> fail-closed test (config state assertions vs a separate `resolve()` assertion),
> the absent-all backward-compat case, and the shadowed-group warning — then add
> `load_permission_config` to `loader.py` per the algorithm and export it from
> `permissions/__init__.py`. Keep `Matcher.origin`/`Degraded.layer` as `None`.
> Use MCP workspace file tools. Run all four MCP checks plus
> `run_lint_imports_check`; fix until green. Single commit.
