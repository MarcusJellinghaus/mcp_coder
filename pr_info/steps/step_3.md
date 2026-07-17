# Step 3 — Resolver: config precedence + default + config-path degrade

**Ref:** `pr_info/steps/summary.md`. One commit: tests + implementation + all checks
green. Depends on Steps 1–2. Covers the `frame=None` path only; frame semantics land in
Step 4.

## WHERE
- Create `src/mcp_coder/icoder/permissions/resolver.py`
- Create `tests/icoder/test_permissions_resolver.py`
- Extend `__init__.py` with `resolve`.
- Modify `vulture_whitelist.py` (whitelist the unread `args` param).

## WHAT (resolver.py — imports matcher + model)

```python
_LAYER_ORDER = {"user": 0, "project": 1, "local": 2, "runtime": 3}

def resolve(
    tool_name: str,
    args: Mapping[str, object] | None,   # intentionally UNREAD in M2 (I5.4 uses it)
    frame: PermissionFrame | None,
    config: PermissionConfig,
) -> Decision:
    """Deterministic tool-call -> Decision. This step: config path (frame ignored)."""

def _resolve_config(tool_name: str, config: PermissionConfig) -> Decision: ...
```

## HOW
- Signature is the fixed cross-issue contract (§10.3) — keep `args` and `frame` even
  though this step reads neither. Suppress the unused-arg finding with a
  `# pylint: disable=unused-argument` on `resolve` and add `args` to
  `vulture_whitelist.py` (decision #9 — do NOT drop the parameter).
- In this step, `resolve(...)` simply delegates to `_resolve_config(tool_name, config)`
  (Step 4 inserts the frame branch above it).
- `matched_rule` uses the provenance hook: report `rule.matcher.origin` if set, else the
  matched `rule` itself.
- `lifted_never` is always `None` here (the authored "specific `always` beats broad
  `never`" carve-out does **not** set it — decision #4).

## ALGORITHM (_resolve_config)
```
if config.degraded:                      # fail-closed, whole config path -> ASK
    return Decision(AFTER_APPROVAL, Degraded(errors=config.errors), None)
cands = [(i, r) for i, r in enumerate(config.rules) if matches(r.matcher, tool_name)]
if cands:
    i, best = max(cands, key=lambda ir: (specificity(ir[1].matcher),
                  ir[1].policy.rank, _LAYER_ORDER[ir[1].layer], -ir[0]))
    matched = best.matcher.origin or best
    return Decision(best.policy, Layer(best.layer), matched, None)
pol = config.default_policy or Policy.ALWAYS      # unset -> ALWAYS (§8.4)
return Decision(pol, Default(), None, None)
```
Key precedence (max over the tuple): specificity (primary, lexicographic) -> policy.rank
(`never>ask>allow`) -> layer order (later wins) -> `-index` (earlier declaration wins).

## DATA
- `resolve` / `_resolve_config` -> `Decision`. `source` is `Layer(name)` on a match,
  `Default()` on fallback, `Degraded(errors=...)` when degraded. `matched_rule is None`
  iff source is `Default`/`Degraded`.

## TESTS (write first — `test_permissions_resolver.py`, all with `frame=None`)
- **Equal-specificity policy precedence**: two same-specificity rules -> `never` beats
  `ask` beats `allow`.
- **Specificity primary**: specific `tool` beats `server__*`; **specific `always` beats
  broad `never`**; specific `always` beats broad (server-wildcard) `ask`.
- **Layering**: equal specificity + equal policy -> later layer wins
  (`user->project->local->runtime`).
- **Declaration order**: equal specificity, equal policy, same layer -> earlier-declared
  rule wins (assert `matched_rule` identity).
- **Wildcards**: `mcp__server__*` matches all tools of that server; a tool of another
  server -> default fallback.
- **Default fallback**: no match, `default_policy=None` -> `ALWAYS`; explicit
  `default_policy=NEVER` -> `NEVER`.
- **Degrade (non-frame)**: `config.degraded=True` -> `ASK` with `source=Degraded`,
  `matched_rule is None` (even when a rule would otherwise match).
- **`after-approval` truthful**: an `ask` rule -> `Decision.policy is AFTER_APPROVAL`
  (not pre-collapsed).
- **origin hook**: a matched rule whose `matcher.origin` is another `Rule` ->
  `matched_rule` is that origin rule.

## CHECKS
Four checks (pylint, pytest with marker exclusions, mypy strict, lint-imports) green.
Confirm `run_vulture_check` no longer flags `args` after the whitelist entry.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Following TDD, first
> write `tests/icoder/test_permissions_resolver.py` for every case in TESTS (all with
> `frame=None`), then implement `src/mcp_coder/icoder/permissions/resolver.py` per
> WHAT/HOW/ALGORITHM: `resolve` delegates to `_resolve_config`; keep the `args`/`frame`
> params (suppress the unused-arg lint and add `args` to `vulture_whitelist.py`).
> Import only from `.matcher` and `.model`. Use MCP tools only. Run pylint, pytest
> (unit-test marker exclusions), mypy(strict), lint-imports, and vulture; fix until
> green. Commit as one change.
