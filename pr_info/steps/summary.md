# I2.2 — Config: `.icoder/` JSONC reader + layered discovery + schema

## Goal

Turn iCoder's on-disk `.icoder/settings.json` layers into the in-memory
`PermissionConfig` (from I2.1) that the resolver consumes. **Read path only.**
The single *write* this issue owns is emitting the editor-hint
`settings.schema.json`. No changes to the I2.1 model are required — every field
this loader populates (`Rule.source_path`, `Rule.layer`, `PermissionConfig.degraded`,
`errors`, `groups`, `scenarios`, `default_policy`) already exists.

## What is being built

A new I/O-capable module `src/mcp_coder/icoder/permissions/loader.py` that:

1. **Discovers** three layers (lowest → highest precedence):
   - `user`  → `get_user_app_data_dir("mcp_coder")/".icoder"/"settings.json"`
   - `project` → `<project_dir>/.icoder/settings.json`
   - `local` → `<project_dir>/.icoder/settings.local.json`
   Absent layers are skipped silently. `.claude/*` is **never** read.
2. **Parses JSONC** with a stdlib, string/escape-aware comment stripper
   (tolerating trailing commas) → `json.loads`.
3. **Validates** each layer against an emitted JSON Schema (structure + enums
   only — matcher grammar stays owned by I2.1's `parse_matcher`).
4. **Builds** layered `Rule`s (via `parse_matcher`), stored `groups`/`scenarios`,
   and a `defaultMode` scalar, attaching per-rule provenance
   (`source_path` + `layer`).
5. **Fails closed by degrading:** a *present-but-broken* layer emits a prominent
   diagnostic (`logger` + `PermissionConfig.errors`), contributes **nothing**,
   and sets `degraded=True` — good layers still contribute their rules; the
   resolver then forces the session default to `ask`. The session still starts.
6. **Emits** `settings.schema.json` into `<project_dir>/.icoder/` — only when
   that dir already exists and only if content differs (no dir creation, no git
   churn).

## On-disk → model mapping

| On-disk key                | Model target                          |
|----------------------------|---------------------------------------|
| `defaultMode` (allow/ask/deny) | `default_policy` (last-layer-wins) |
| `allow` / `ask` / `deny`   | `rules` (concatenated across layers)  |
| `toolGroups`               | `groups` (last-layer-wins by name)    |
| `toolScenarios`            | `scenarios` (last-layer-wins by name) |

Vocabulary is Claude-style throughout: `allow`→`Policy.ALWAYS`,
`ask`→`Policy.AFTER_APPROVAL`, `deny`→`Policy.NEVER`. This single
`_POLICY_BY_TOKEN` mapping is the one source for rule policies, `defaultMode`,
**and** the schema's enum list.

## Architectural / design changes

- **New module in the permissions package**, but *outside* its pure core.
  `model`/`matcher`/`resolver` remain I/O-free; `loader` is the only member
  allowed to import `json`/`jsonschema`.
- **New narrow import-linter contract** `permissions_core_purity`: a `forbidden`
  contract over `model`/`matcher`/`resolver` forbidding `json` + `jsonschema`.
  The existing package-wide `permissions_leaf_isolation` contract is unchanged
  (loader still may not reach into `ui`/`services`/`textual`/langchain).
- **One new runtime dependency:** `jsonschema` (base dependency — it sits on a
  startup security path), plus `types-jsonschema` for mypy-strict. `json5`
  remains a documented, *undeclared* fallback (not imported).
- **KISS decisions:**
  - The schema is a **static dict** (not a dataclass-reflection walker); the
    same dict is used for validation *and* the emitted file.
  - Validation depth is **structure + enums only**; matcher validity is
    delegated to `parse_matcher` (single source of truth, no drift).
  - The JSONC stripper is **one string/escape-aware char scanner** that also
    drops trailing commas in the same pass (no fragile regex layering).
- **Fail-closed is per-layer atomic:** any single error (bad JSONC, schema
  reject, bad matcher, or an `@ref` token) fails the *whole* layer (grants
  nothing) rather than silently dropping a rule; `degraded=True` is the global
  switch the resolver reads.
- **Stale model comments** on `Degraded.layer` and `Matcher.origin` ("populated
  by I2.2 …") are intentionally **not** acted on — both stay `None` in M2 (no
  consumer until I4.1/I4.3). Flagged, not changed.

## Files created / modified

**Created**
- `src/mcp_coder/icoder/permissions/loader.py` — the loader module.
- `tests/icoder/test_permissions_loader.py` — its tests.

**Modified**
- `pyproject.toml` — add `jsonschema` to `[project.dependencies]`,
  `types-jsonschema` to `[project.optional-dependencies].types`.
- `.importlinter` — add the `permissions_core_purity` contract.
- `src/mcp_coder/icoder/permissions/__init__.py` — export
  `load_permission_config`.

**Unchanged (deliberately)**
- `permissions/model.py`, `matcher.py`, `resolver.py` — no edits.

## Step overview (one commit each)

1. Dependencies + narrow import-linter contract.
2. JSONC preprocessor (`_strip_jsonc`).
3. Schema: `_POLICY_BY_TOKEN`, `build_settings_schema`, validation helper,
   `emit_schema` (gated write).
4. Layer discovery (`_discover_layers`).
5. Per-layer load (`_load_layer`): parse → validate → matcher/`@ref` handling.
6. Public `load_permission_config` (merge + degrade + provenance) + `__init__`
   export + end-to-end `resolve()` fail-closed test.

## Out of scope (do not implement)

Write-back/persist (I3.3), convert/merge CLI + Claude reader (I5.2/I5.5),
group/scenario *matching* & `@ref` expansion (I4.1), TUI surfacing of the
degrade diagnostic (I2.3/I4.3), starter config & `.gitignore` (I5.3), wiring
schema into `SKILL.md` validation (I2.4), `${VAR}` substitution (unsupported).
