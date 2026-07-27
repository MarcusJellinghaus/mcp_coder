# Step 5 — Per-layer load (`_load_layer`)

See [summary.md](./summary.md). Parse one layer end-to-end and turn it into
rules/groups/scenarios/default — or into errors. Any single error fails the
**whole** layer (grants nothing); errors always name the file + offending token.

## WHERE
- `src/mcp_coder/icoder/permissions/loader.py` (extend)
- `tests/icoder/test_permissions_loader.py` (extend)

Add imports from `.model` (`Matcher`, `Policy`, `Rule`) and `.matcher`
(`parse_matcher`).

## WHAT
```python
class _LayerResult(NamedTuple):
    default_policy: Policy | None
    rules: list[Rule]
    groups: dict[str, tuple[Matcher, ...]]
    scenarios: dict[str, tuple[Matcher, ...]]
    errors: list[str]

def _parse_matchers(token: str, path: Path) -> tuple[list[Matcher], list[str]]:
    """Parse one matcher token, pre-detecting @refs. Returns (matchers, errors)."""

def _load_layer(layer: str, path: Path) -> _LayerResult:
    """Read + JSONC-parse + schema-validate one file, then build rules/groups/
    scenarios. On ANY error the layer contributes nothing (errors populated)."""
```

## HOW
- `_parse_matchers` must check `token.startswith("@")` **before** calling
  `parse_matcher` (which would otherwise emit a generic "malformed matcher").
- Every error string is prefixed with the source file, e.g.
  `f"{path}: <detail>"`, and includes the offending token/key.
- `allow`/`ask`/`deny` map to policy via `_POLICY_BY_TOKEN`.
- `groups`/`scenarios` members are parsed with the same `_parse_matchers`
  (concrete `mcp__…` only; an `@ref` member degrades the layer).
- `path` arrives already absolute from `_discover_layers` (Step 4 calls
  `.resolve()`), so `Rule(m, policy, layer, path)` stores absolute provenance as
  required by issue #1042 Decisions + Loop-A refinement.

## ALGORITHM
`_parse_matchers`:
```
if token.startswith("@"):
    return [], [f"{path}: group references (@…) not supported until I4.1: {token!r}"]
matchers, errs = parse_matcher(token)
return (matchers, []) if not errs else ([], [f"{path}: {e} (token {token!r})" for e in errs])
```
`_load_layer`:
```
try: data = json.loads(_strip_jsonc(path.read_text(encoding="utf-8")))
except (OSError, json.JSONDecodeError) as e: return _LayerResult(None,[],{},{},[f"{path}: {e}"])
errors = [f"{path}: {m}" for m in _schema_errors(data)]
rules=[]; groups={}; scenarios={}
for token in data.get("allow"/"ask"/"deny"):        # each section -> its Policy
    ms, errs = _parse_matchers(token, path)
    errors += errs
    rules += [Rule(m, policy, layer, path) for m in ms]
for name, members in data.get("toolGroups"/"toolScenarios").items():   # into groups/scenarios
    collect members via _parse_matchers; accumulate errors; store tuple
default = _POLICY_BY_TOKEN.get(data.get("defaultMode")) if present else None
if errors: return _LayerResult(None, [], {}, {}, errors)   # per-layer atomic: grant nothing
return _LayerResult(default, rules, groups, scenarios, [])
```

## DATA
`_LayerResult` — on success: parsed default + rules/groups/scenarios, empty
errors. On any failure: `default_policy=None`, empty collections, non-empty
`errors` (each naming file + token/key).

## TESTS (write first)
- Good layer: `allow`/`ask`/`deny` → correct `Rule.policy`, each `Rule` carries
  `source_path == path` (and `source_path.is_absolute()`) and `layer == tag`;
  value-set matcher expands to N rules; `toolGroups`/`toolScenarios` populated;
  `defaultMode` parsed.
- `@ref` in a rule list → layer grants nothing, error mentions `@` /
  "not supported until I4.1" and the token.
- `@ref` nested inside a `toolGroups` member → same specific diagnostic.
- Bad matcher (e.g. non-`mcp__`) → layer grants nothing, error names file+token.
- Schema-invalid content (`defaultMode: "maybe"`) → error names the file.
- JSONC with comments inside string values parses to the correct rules.

## VERIFICATION
All four MCP checks pass.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_5.md`. Implement Step 5
> with TDD: add the per-layer tests (good layer + provenance, `@ref` in list and
> in a group member, bad matcher, schema-invalid, JSONC-in-string) first, then
> add `_LayerResult`, `_parse_matchers`, and `_load_layer` to `loader.py` per the
> algorithm. Ensure `@ref` is pre-detected before `parse_matcher` and every error
> names the file + token. Use MCP workspace file tools. Run all four MCP checks;
> fix until green. Single commit.
