# Step 3 — Schema: token map, builder, validation, gated emit

See [summary.md](./summary.md). One static schema dict serves both validation
and the emitted editor-hint file. Validation depth is **structure + enums only**
— matcher grammar stays with `parse_matcher` (Step 5).

## WHERE
- `src/mcp_coder/icoder/permissions/loader.py` (extend)
- `tests/icoder/test_permissions_loader.py` (extend)

Add `import json` and `import jsonschema` at the top of `loader.py` this step.

## WHAT
```python
_POLICY_BY_TOKEN: dict[str, Policy] = {
    "allow": Policy.ALWAYS,
    "ask": Policy.AFTER_APPROVAL,
    "deny": Policy.NEVER,
}

def build_settings_schema() -> dict[str, object]:
    """Return the JSON Schema for the on-disk settings.json format."""

def _schema_errors(data: object) -> list[str]:
    """Return a list of human-readable schema-violation messages ([] if valid)."""

def emit_schema(project_dir: Path) -> bool:
    """Write settings.schema.json into <project_dir>/.icoder/ when that dir
    exists and content differs. Return True if a file was written."""
```

## HOW
- `Policy` imported from `mcp_coder.icoder.permissions.model`.
- Schema enum for `defaultMode` = `list(_POLICY_BY_TOKEN)` (one source of truth).
- `_schema_errors` wraps `jsonschema` validation and returns messages as data
  (no raise) — each message names the offending key/value.

## ALGORITHM
`build_settings_schema` (static dict):
```
properties:
  "$schema": {type: string}
  defaultMode: {enum: list(_POLICY_BY_TOKEN)}
  allow/ask/deny: {type: array, items: {type: string}}
  toolGroups/toolScenarios: {type: object, additionalProperties:
                             {type: array, items: {type: string}}}
type: object; additionalProperties: false
```
`_schema_errors`:
```
validator = jsonschema.Draft7Validator(build_settings_schema())
return [f"{e.json_path}: {e.message}" for e in validator.iter_errors(data)]
```
`emit_schema`:
```
icoder = project_dir / ".icoder"
if not icoder.is_dir(): return False
target = icoder / "settings.schema.json"
new = json.dumps(build_settings_schema(), indent=2) + "\n"
if target.exists() and target.read_text(encoding="utf-8") == new: return False
target.write_text(new, encoding="utf-8"); return True
```

## DATA
- `build_settings_schema` → JSON-Schema dict.
- `_schema_errors` → `list[str]` (empty = valid).
- `emit_schema` → `bool` (written?).

## TESTS (write first)
- Schema **accepts** a known-valid config (all sections, valid `defaultMode`).
- Schema **rejects**: `defaultMode: "maybe"`; `allow` not an array; unknown
  top-level key; `toolGroups` value not a string-array.
- `emit_schema`: returns `False` and writes nothing when `.icoder/` absent;
  writes and returns `True` when `.icoder/` exists and file missing; returns
  `False` (no rewrite) on identical content; rewrites when content differs.
  (Use a tmp project dir.)

## VERIFICATION
All four MCP checks pass.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_3.md`. Implement Step 3
> with TDD: add tests for schema accept/reject and `emit_schema` gating first,
> then add `_POLICY_BY_TOKEN`, `build_settings_schema`, `_schema_errors`, and
> `emit_schema` to `loader.py` (add `import json`/`import jsonschema`). Keep the
> schema a static dict validating structure + enums only. Use MCP workspace file
> tools. Run all four MCP checks; fix until green. Single commit.
