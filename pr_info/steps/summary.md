# I4.1 — Groups & scenarios (#1047)

Adds **reference expansion** to the iCoder permission core: `@group` matcher references in any
`allow`/`ask`/`deny` list, and `use: <scenario>` whole-block references in a skill's `tools:` block,
resolved against the `toolGroups`/`toolScenarios` that I2.2 already loads.

I2.1 defined these as *structure*; I2.2 *loads* them; **I4.1 adds the matching/expansion at load**
(design #1037 §10.6.2 D-M). Read the epic **#1038** and the design reference **#1037** (§3, §8.2,
§8.3, §10.2 D-B, §10.3 DC2+DC4, §10.6.2 D-B+D-M) before implementing.

---

## Architectural / design changes

### 1. The loader becomes two-phase (the one structural change)

Today `_load_layer` parses every token straight into `Matcher`s **per layer**, and merging happens
afterwards. A `@ref` must expand against the **merged** group map (D6/D-M), so a group defined in
`user` and referenced from `project` cannot resolve under the current shape.

New shape inside `loader.py`:

1. **Per layer (unchanged I/O):** read → JSONC → schema-validate → *validate* every matcher token →
   keep rule tokens and group/scenario members **raw**.
2. **Merge:** `toolGroups`/`toolScenarios` merged across layers (last-layer-wins by name, existing
   shadow warning preserved). The merged map is **raw-token-valued**, which is what makes transitive
   expansion (`github-write: ["@github-read", …]`) work across layers.
3. **Expand + build:** expand each rule token in authored order and build `Rule`s.

Nothing unexpanded ever reaches the model: `PermissionConfig.groups`/`.scenarios` are
post-expansion and ref-free (what I4.2's group view wants).

**Kept deliberately simple:** no `_PendingRule` dataclass. `_LayerResult` keeps its shape and its
three collection fields simply change from *parsed* to *raw*; the layer tag and source path are
already known at the merge site, so carrying them per rule would be redundant. `_load_layer` itself
is not split, which keeps ~20 existing test call sites intact.

### 2. New pure module `permissions/expand.py`

Operates on **tokens**, not `Matcher`s, and is callable outside the loader (I4.2 builds runtime-layer
rules from the same primitive). Three public names, one of them the real work:

- `is_ref(token)` / `ref_name(token)` — the single home for the `@` convention, replacing the
  duplicated `startswith("@")` checks in `loader.py` and `skill_frame.py`.
- `expand(token, groups) -> (matchers, errors)` — **single-token**, since both callers already work
  a token at a time. Errors are returned pathless; the loader prefixes the source path, exactly as
  `_parse_matchers` does today.

Added to both import-linter contracts (`permissions_leaf_isolation`, `permissions_core_purity`) and
exported from `permissions/__init__.py`.

### 3. Cycles need no cycle detector

A visited-set over **group names** plus one rule — *a top-level ref that expands to zero matchers is
an error* — covers D3 (unknown/unresolvable) and D4 (cycle) together. `@a → @b → @a` contributes
nothing and terminates; an already-visited member contributes once. Cycle *reporting* is I5.1.

Two consequences recorded as accepted behaviour:

- An **unknown name is an error at any depth**; **emptiness is checked only on the top-level
  result**, so a nested reference to a defined-but-empty group does not poison a sibling that
  resolved fine.
- A rule referencing a **defined-but-empty** group (`"spare": []`) therefore degrades, because that
  is indistinguishable from a pure cycle. Fail-closed and consistent with the epic's principle;
  flagged as the one surprising edge.

### 4. Provenance: two model fields, no sentinel

The authored `@group` rule is synthesised as a `Rule` carrying `ref="@github-write"` plus its
`source_path`; each expanded member `Matcher` points at it via `origin`. The resolver already reads
this (`matched = best.matcher.origin or best`), so the read side is untouched.

- `Matcher.origin` gains `field(compare=False)` (D14) so provenance never changes `Matcher`
  equality or hash.
- `Rule.ref: str | None` (D8) — `persist.write_rule(target, matcher: str, section)` takes a raw
  token, so the literal `"@github-write"` must survive expansion for I3.3 write-back and I4.2
  group-edit.
- `Rule.matcher` widens to `Matcher | None`, **still required, no default** (D15) — a default would
  precede two non-defaulted fields and break three positional call sites.
- Origin rules are **provenance-only** (D13): reachable via `Matcher.origin`, never members of
  `config.rules`, so they are never match candidates. This makes the 4 `None` guards in src
  (`resolver.py:63, 177, 206`, `gateway.py:161`) unreachable by construction — they **skip** the
  rule rather than assert, so a future regression degrades closed instead of crashing a session.

### 5. Skills resolve refs by lookup, not by expansion

`PermissionConfig.groups`/`.scenarios` are already transitively expanded and ref-free, so the skill
path needs a **dict lookup**, not a second expansion pass. `build_frame` therefore takes
`config.groups` / `config.scenarios` verbatim — no conversion at the call site, and `skill_frame.py`
never calls `expand`.

Both new parameters are keyword-only with a `None` default, so the 24 existing `build_frame` call
sites compile untouched. The defaults are fail-closed, not fail-open: an absent group makes every
`@ref` unknown → I2.4's drop-and-warn ladder; an absent scenario → the skill is blocked.

Failure handling on the skill path follows I2.4's existing ladder (D10), **not** a global degrade:
dropped + warning on the `allow` side, `base` forced to `none` on the `deny` side, blocked only if
`allow` empties (`two_empties`). An unknown **`use: <name>`** is not covered by that ladder — there
is no side to drop a missing whole block from — so it keeps today's outright block; only the
"unsupported until I4.1" reason string becomes "unknown scenario". A known scenario whose side failed
to expand (non-empty `ScenarioBlock.errors`) is blocked the same way, with the errors surfaced — never
applied with a silently emptied side.

### 6. `toolScenarios` changes shape (D7)

A flat matcher list cannot express `base`, which is the security-relevant half of `use:`. Both sides
become `name → {base, allow, deny}`: the **schema branch** and the **model type** (new frozen
`ScenarioBlock`, `base` required and never defaulted). This restores design §5's shape, which I2.2
flattened. A side that fails to expand is stored as `()`, a failed `deny` forces `base="none"`, and the
errors are logged and kept on `ScenarioBlock.errors` (not `config.errors` — no global degrade, D10). Nothing outside `loader.py`/`model.py` reads `.scenarios` today.

### 7. Load runs for every provider (D9), banner stays gated (D12)

`load_permission_config` hoists **out of** the langchain-only branch in `cli/commands/icoder.py`, so
`build_frame` always has groups/scenarios and skill blocking stays provider-agnostic.
`permission_degraded` **stays** gated on the `langchain and mcp_config` branch: the startup banner
says MCP calls are being denied, which is false under Claude where nothing is enforced. Load
everywhere; surface only where it bites.

### 8. Failure granularity narrows (D11)

An unresolvable/cyclic `@ref` kills **its own rule** (warn + `degraded=True` + `errors`); sibling
rules in the same layer survive into `config.rules`. Structural failures (bad JSONC, schema reject,
malformed `mcp__…` token) keep I2.2's per-layer atomicity. Invisible to `resolve()` — `degraded`
short-circuits `_resolve_config` — but visible to I4.2's manager view and I5.1's report.

**Testing consequence:** because `degraded` short-circuits the resolver, every fail-closed assertion
must be made on **`config.rules`**, never through `resolve()`, or the AC passes vacuously.

### 9. Declaration order is preserved for free

Expanding in one pass over authored order already places members at the authored rule's position, so
no splice logic is needed. "Earlier authored entry wins" rests on the negated declaration index
(`resolver.py:70`), so it still needs an explicit test — one whose two rules share **policy,
specificity and layer**, or the `never` bit / layer order decides it and the test passes for the
wrong reason.

### 10. Accepted behavioural edge (D13)

`gateway.filter_tools` keeps an arg-scoped `NEVER` tool *visible* (refused later at call level) by
reading `decision.matched_rule.matcher.arg`. Under D13 `matched_rule` is the origin rule, whose
matcher is `None`, so an arg-scoped member reached via a `@group` is **hidden outright** instead.
Accepted as fail-closed — hiding is strictly narrower, and arg *evaluation* is deferred to I5.4.

---

## Files created / modified

### Created

| Path | Purpose |
|---|---|
| `src/mcp_coder/icoder/permissions/expand.py` | Pure token→matcher expander (`is_ref`, `ref_name`, `expand`) |
| `tests/icoder/test_permissions_optional_matcher.py` | The D15 widening across model/resolver/gateway |
| `tests/icoder/test_permissions_expand.py` | Pure expander unit tests |
| `tests/icoder/test_permissions_loader_expand.py` | Cross-layer / on-disk expansion tests (keeps the 651-line layers file from growing) |

### Modified

| Path | Change |
|---|---|
| `src/mcp_coder/icoder/permissions/model.py` | `Matcher.origin` `compare=False`; `Rule.ref`; `Rule.matcher: Matcher \| None`; `ScenarioBlock`; `PermissionConfig.scenarios` retype |
| `src/mcp_coder/icoder/permissions/loader.py` | Two-phase load; `_token_errors` replaces `_parse_matchers`; raw `_LayerResult`; merge + expand; `toolScenarios` schema branch |
| `src/mcp_coder/icoder/permissions/skill_frame.py` | `groups`/`scenarios` kwargs; `@ref` lookup in `_classify`; `use:` block substitution |
| `src/mcp_coder/icoder/permissions/resolver.py` | 3 `None`-matcher skip guards |
| `src/mcp_coder/icoder/permissions/gateway.py` | 1 `None`-matcher skip guard |
| `src/mcp_coder/icoder/permissions/__init__.py` | Export `expand`, `ScenarioBlock` |
| `src/mcp_coder/cli/commands/icoder.py` | D9 load hoist; D12 banner gating; pass groups/scenarios to `build_frame` |
| `.importlinter` | `expand` added to both permission contracts |
| `tests/icoder/test_permissions_model.py` | `origin` equality; `Rule.ref`; `scenarios` shape |
| `tests/icoder/test_permissions_loader_layers.py` | Invert the three `@ref` diagnostics; adapt `_load_layer` asserts to raw tokens |
| `tests/icoder/test_permissions_loader_schema.py` | Invert the flat-`toolScenarios` fixture |
| `tests/icoder/test_permissions_skill_frame.py` | `@ref` + `use:` behaviour |
| `tests/icoder/test_icoder_permission_wiring.py` | "loaded but no gateway, no banner" |
| `tests/icoder/test_cli_icoder.py` | Stale docstring |

**Untouched:** `persist.py`, `approval.py`, `skill_tools.py` (D5's `use:` + inline-keys rejection is
already implemented at `skill_tools.py:97-101` and `skill_frame.py:194-199` — a regression assertion,
not new work).

---

## Steps

Each step is exactly one commit: tests first, then implementation, then all checks green.

| Step | Scope |
|---|---|
| [step_1.md](./step_1.md) | Model: `Rule.ref`, `Rule.matcher` widening, `origin` `compare=False`, 4 skip guards |
| [step_2.md](./step_2.md) | `permissions/expand.py` + contracts + export |
| [step_3.md](./step_3.md) | Loader two-phase + `@group` expansion for config rules |
| [step_4.md](./step_4.md) | `toolScenarios` shape (`ScenarioBlock` + schema) |
| [step_5.md](./step_5.md) | `skill_frame`: `@ref` lookup + `use:` substitution |
| [step_6.md](./step_6.md) | CLI wiring: D9 hoist, D12 gating |

## Checks (every step)

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check   # extra_args: ["-n", "auto", "-m", "not <integration markers>"]
mcp__mcp-tools-py__run_mypy_check
mcp__mcp-tools-py__run_ruff_check
mcp__mcp-tools-py__run_lint_imports_check
mcp__mcp-tools-py__run_vulture_check
```

`tests.*` already disables `union-attr` (`pyproject.toml:223-227`), so test readers of
`rule.matcher` need no guards.
