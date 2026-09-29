# Step 3 — Loader: two-phase load and `@group` expansion for config rules

Read [summary.md](./summary.md) §1 (two-phase load), §4 (provenance), §8 (failure granularity) and
the testing consequence in §8 first. This is the core step.

Scenarios stay a flat token list here and keep today's flat `Mapping[str, tuple[Matcher, ...]]` type —
they are expanded exactly like groups. The `{base, allow, deny}` reshape is step 4.

## WHERE

- `src/mcp_coder/icoder/permissions/loader.py` (modify)
- `tests/icoder/test_permissions_loader_layers.py` (modify — invert/adapt)
- `tests/icoder/test_permissions_loader_expand.py` (create)

## WHAT

```python
class _LayerResult(NamedTuple):
    default_policy: Policy | None
    rule_tokens: list[tuple[str, Policy]]      # was: rules: list[Rule] — now RAW
    groups: dict[str, tuple[str, ...]]         # was: tuple[Matcher, ...] — now RAW
    scenarios: dict[str, tuple[str, ...]]      # was: tuple[Matcher, ...] — now RAW
    errors: list[str]


def _token_errors(token: str, path: Path) -> list[str]:
    """Validate one matcher token, deferring ``@ref`` resolution to the merge."""

def _load_layer(layer: str, path: Path) -> _LayerResult:      # signature unchanged
def load_permission_config(project_dir: Path) -> PermissionConfig:   # signature unchanged
```

Plus two small module-private helpers in `load_permission_config`'s service (keep them tiny; inline
if clearer):

```python
def _merge_named(
    loaded: list[tuple[str, Path, _LayerResult]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    """Merge raw ``toolGroups``/``toolScenarios`` last-layer-wins, warning on shadowing."""

def _expand_rules(
    loaded: list[tuple[str, Path, _LayerResult]],
    groups: Mapping[str, Sequence[str]],
) -> tuple[list[Rule], list[str]]:
    """Expand every rule token in authored order, synthesising origin rules."""
```

## HOW

- `_parse_matchers` is **replaced** by `_token_errors` — the `@` branch becomes a *skip*, not an
  inverted diagnostic, so the special case disappears rather than being rewritten. Use `is_ref` from
  `expand.py` (delete the local `token.strip().startswith("@")` check).
- `_load_layer` keeps its shape: same read → JSONC → schema → walk sections. It now *validates*
  tokens and stores them raw. Per-layer atomicity for structural failures is therefore unchanged —
  it did not move.
- `load_permission_config` collects `list[tuple[str, Path, _LayerResult]]` for the good layers, so no
  `_PendingRule` type is needed: the layer tag and path are already in hand at expansion time.
- `PermissionConfig.groups` stays post-expansion and ref-free: materialise it by calling
  `expand(f"@{name}", raw_groups)` per name and **dropping** the errors — a broken group that no rule
  references must not degrade the config. Add a one-line comment saying so.
- Origin synthesis is 3 lines, in `_expand_rules`, not in `expand.py`. Use
  `dataclasses.replace(m, origin=origin)` (add the import).
- Update the module docstring: replace the Step-5/Step-6 `@ref`-unsupported wording with the
  two-phase description.
- Keep every existing error string format (`f"{path}: …"`) and the existing shadow warnings
  (`"group %r shadowed by %s"`, `"scenario %r shadowed by %s"`).

## ALGORITHM

```
_token_errors(token, path):
    if is_ref(token):  return []                       # resolved after the merge
    _, errs = parse_matcher(token)
    return [f"{path}: {e} (token {token!r})" for e in errs]

load_permission_config(project_dir):
    emit_schema; layers = _discover_layers; if not layers: return PermissionConfig()
    for tag, path in layers:                           # PHASE 1 — per layer, atomic
        r = _load_layer(tag, path)
        if r.errors: errors += r.errors; continue
        loaded.append((tag, path, r)); default = r.default_policy or default
    raw_groups, raw_scenarios = _merge_named(loaded)    # PHASE 2 — merge, still raw
    rules, rule_errors = _expand_rules(loaded, raw_groups)   # PHASE 3 — expand + build
    groups = {n: expand(f"@{n}", raw_groups)[0] for n in raw_groups}     # errors dropped
    scenarios = likewise over raw_scenarios
    degraded = bool(errors + rule_errors); log each; return PermissionConfig(...)

_expand_rules(loaded, groups):
    for tag, path, r in loaded:                        # authored order → members land in place
        for token, policy in r.rule_tokens:
            matchers, errs = expand(token, groups)
            if errs: errors += [f"{path}: {e}" for e in errs]; continue   # D11: this rule only
            if is_ref(token):
                origin = Rule(None, policy, tag, path, ref=token)
                matchers = [replace(m, origin=origin) for m in matchers]
            rules += [Rule(m, policy, tag, path) for m in matchers]
```

## DATA

- `PermissionConfig.rules` — expanded members only; **no origin rule is ever a member** (D13).
- Each expanded member's `matcher.origin` is the shared synthesised `Rule(matcher=None, …,
  ref="@name")` carrying the authored token and `source_path`.
- `PermissionConfig.groups` — `Mapping[str, tuple[Matcher, ...]]`, unchanged type, now transitively
  expanded and ref-free.
- `degraded` / `errors` — as today, now also fed by per-rule ref failures.

## Tests (write first)

### `tests/icoder/test_permissions_loader_expand.py` (new)

Reuse the `_make_settings` / `get_user_app_data_dir` monkeypatch setup from
`test_permissions_loader_layers.py:38-56`. All of these need on-disk fixtures, which is exactly why
they cannot live in the pure expander file.

1. **Merged map** — group in `user`, `@ref` rule in `project` → resolves (AC).
2. **Transitive across layers** — group in `user` whose member references a group in `project` →
   resolves (proves members stay raw across the merge).
3. **Provenance** — `resolve()` on a `@group`-granted tool returns `matched_rule` = the origin rule
   with `ref == "@git"` and the authored `source_path`, and `source` is the authored layer.
4. **Origin not a candidate** — no member of `config.rules` has `ref` set / `matcher is None`
   (D13).
5. **Member specificity** — a direct `allow` on `mcp__git__log` beats a broad `@git` `ask`
   (AC: the specific direct rule wins).
6. **Multiple groups / earlier authored entry wins** — the two competing rules must share **policy,
   specificity and layer** so the negated declaration index is genuinely the deciding key; assert on
   `decision.matched_rule` (the origin) or on `config.rules` order.
7. **Declaration position** — expanding one `@group` into N rules keeps later rules' relative order;
   assert `config.rules` order.
8. **Reload follows membership** — load, mutate only the group definition on disk, re-load, assert
   the resolved policy changed with the authored `@group` rule untouched (D2).
9. **Unknown ref fails closed** — `degraded is True`, error names the ref and its source file, and
   **assert on `config.rules`**: the containing rule contributed nothing. Do not assert via
   `resolve()` (it would pass from `degraded` alone).
10. **Sibling survival (D11)** — a layer with one bad `@ref` and one good sibling rule: the sibling is
    present in `config.rules` while `degraded is True`.
11. **Structural failure still per-layer (D11's other half)** — a malformed `mcp__…` token discards
    its whole layer, siblings included.
12. **Cycle on disk** — terminates, degrades, contributes no rules.
13. **Unreferenced broken group does not degrade** — a `toolGroups` entry with an unknown nested ref
    that no rule references leaves `degraded is False`.

### `tests/icoder/test_permissions_loader_layers.py` (modify)

- `test_parse_matchers_concrete_token` / `test_parse_matchers_bad_token_names_file_and_token` →
  retarget to `_token_errors` (`[]` vs. an error naming file + token).
- `test_parse_matchers_ref_pre_detected`, `test_load_layer_ref_in_group_member_grants_nothing`,
  `test_load_layer_ref_with_leading_whitespace_group_member` → **invert**: a `@ref` (padded or not)
  now validates cleanly and is carried raw; the group member survives in `result.groups` as a raw
  token. Keep the whitespace case — it now pins whitespace tolerance instead of a diagnostic.
- `test_load_layer_ref_in_rule_list_grants_nothing` → invert: the layer loads cleanly and
  `result.rule_tokens` holds both tokens.
- `test_load_layer_good_allow_ask_deny_policies` → assert on `result.rule_tokens` pairs.
- `test_load_layer_value_set_expands_to_n_rules` → the layer now yields **one token**; move the
  "expands to 3 rules" assertion to the new file (or an existing full-load test).
- `test_load_layer_provenance_absolute_and_layer_tag` → `_load_layer` no longer builds `Rule`s; move
  the layer-tag + absolute-path assertion to a full-load test.
- `test_load_layer_populates_groups_and_scenarios` → members are now raw tokens.
- Update the module docstring's Step 5 description.

## LLM prompt

> Implement **step 3** of `pr_info/steps/summary.md` as described in `pr_info/steps/step_3.md`.
> Read the summary first — §1, §4 and §8 hold the settled decisions D1/D6/D8/D11/D13/D-M.
>
> Test-driven: write `tests/icoder/test_permissions_loader_expand.py` (the thirteen cases listed) and
> apply the `test_permissions_loader_layers.py` inversions first, watch them fail, then restructure
> `loader.py`.
>
> Constraints that matter:
> - Do **not** introduce a `_PendingRule` dataclass and do **not** split `_load_layer` — retype the
>   three `_LayerResult` collection fields to raw tokens instead. The layer tag and path are already
>   available where expansion happens.
> - Group and scenario **members must stay raw across the merge**, or transitive expansion cannot work.
> - Expand in authored order so members land at the authored rule's position; no splice logic.
> - A ref failure kills **only its own rule** (D11); a structural failure still discards its layer.
> - Every fail-closed assertion is on `config.rules`, never through `resolve()` — `degraded`
>   short-circuits `_resolve_config`, so a `resolve()`-based assertion would pass vacuously.
> - Leave `toolScenarios`' shape alone; step 4 owns that.
>
> Then run the checks listed at the end of the summary, and check `loader.py` against the 600-line
> limit with `check_file_size`. One commit.
