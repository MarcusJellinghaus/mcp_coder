# Summary — deptry: replace the hardcoded DEP002 list with `optional_dependencies_dev_groups` (#1290)

## Goal

Drop the hand-maintained `DEP002` ignore list in `[tool.deptry.per_rule_ignores]`.
Instead, set `optional_dependencies_dev_groups` to name every extra that holds
dev-only packages. deptry then exempts those packages from DEP002 and still
reports DEP004 if `src/` imports one of them.

## Architectural / design changes

- **Before:** each dev-only package is listed by name under `DEP002`, grouped by
  where it comes from. Adding a dev tool meant editing two places.
- **After:** dev-only packages are exempt because of the extra they belong to.
  A new dev tool needs no deptry edit as long as it goes into one of the named
  extras. A new extra still has to be added to the setting.
- **Why five groups and not just `dev`:** deptry matches extras by exact name
  and does not expand `mcp-coder[types,test,…]` self-references inside `dev`.
  So `dev`, `types`, `typecheck`, `test` and `tui` are each named. `typecheck`
  is the only extra that declares `mypy`.
- **Excluded on purpose:** `langchain-*` and `mlflow`. `src/` imports them, so
  naming them would turn legitimate imports into DEP004 errors.
- **Unchanged:** `DEP003`, `package_module_name_map`, `known_first_party`, the
  extras themselves, the CI `deptry` job, and `tools/deptry_check.*`.
- **No new test.** Per the issue's decision, the CI `deptry` job already catches
  a missing extra via DEP002. The change is config-only, so there is no
  TDD test to write.

## Files modified

| File | Change |
|---|---|
| `pyproject.toml` | Add the commented `optional_dependencies_dev_groups` setting under `[tool.deptry]`; delete the `DEP002` key and its comment block |
| `docs/repository-setup/python.md` | Update the `[tool.deptry]` Customize note in "Dependency Declaration Hygiene" |

No files or folders are created besides these plan files.

## Steps

1. [step_1.md](./step_1.md): replace DEP002 with `optional_dependencies_dev_groups`, update the docs, and verify with deptry. One commit.
