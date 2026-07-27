# Step 1 — Dependencies + narrow import-linter contract

See [summary.md](./summary.md). This step lays the foundation: declare the new
runtime dependency and lint-enforce that the pure permission core never imports
serialization libraries. No new Python module yet.

## WHERE
- `pyproject.toml`
- `.importlinter`

## WHAT
No functions. Two config edits:

1. **`pyproject.toml`**
   - Add `"jsonschema>=4.0.0"` to `[project.dependencies]`.
   - Add `"types-jsonschema>=4.0.0"` to `[project.optional-dependencies].types`.

2. **`.importlinter`** — add a new contract *after* the existing
   `permissions_leaf_isolation` block (leave that block unchanged):

   ```ini
   # -----------------------------------------------------------------------------
   # Contract: iCoder Permissions Core Purity
   # -----------------------------------------------------------------------------
   # The pure permission core (model/matcher/resolver) must stay I/O-free: no
   # serialization libraries. Only the loader (not listed here) may import them.
   # -----------------------------------------------------------------------------
   [importlinter:contract:permissions_core_purity]
   name = iCoder Permissions Core Purity
   type = forbidden
   source_modules =
       mcp_coder.icoder.permissions.model
       mcp_coder.icoder.permissions.matcher
       mcp_coder.icoder.permissions.resolver
   forbidden_modules =
       json
       jsonschema
   ```

## HOW
- `jsonschema` is a **base** dependency (startup security path), not an extra.
- The stub goes in the existing `types` extra so mypy-strict resolves it.
- `json5` is **not** added — it stays a documented, unimported fallback.

## ALGORITHM
None.

## DATA
None. Verification only:
- `run_lint_imports_check()` → PASSED (the new contract is green because no core
  module imports `json`/`jsonschema` today).
- `run_mypy_check()` still passes.

## VERIFICATION
- `mcp__tools-py__run_lint_imports_check()` reports PASSED including
  `permissions_core_purity`.
- `mcp__tools-py__run_pylint_check`, `run_pytest_check` (unit subset),
  `run_mypy_check` all pass.

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1
> only: add `jsonschema` to `[project.dependencies]` and `types-jsonschema` to
> the `types` extra in `pyproject.toml`, and add the `permissions_core_purity`
> forbidden contract to `.importlinter` exactly as specified (do not modify the
> existing `permissions_leaf_isolation` contract). Use MCP workspace file tools.
> Then run `run_lint_imports_check`, `run_pylint_check`, `run_pytest_check`
> (unit subset per CLAUDE.md), and `run_mypy_check`; confirm all pass. Produce a
> single commit.
