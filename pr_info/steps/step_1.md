# Step 1 — Replace the DEP002 list with `optional_dependencies_dev_groups`

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md`
> exactly as written. This is a config-and-docs change only, so don't touch any
> Python code or tests. Verify with `deptry src` and the standard checks, run the
> formatter, then make one commit.

## WHERE

- `pyproject.toml`: the `[tool.deptry]` table and `[tool.deptry.per_rule_ignores]`
- `docs/repository-setup/python.md`: section "Dependency Declaration Hygiene",
  the `> **Customize (...)**` note

## WHAT

No functions. This step changes configuration only.

### 1. `pyproject.toml`, `[tool.deptry]`

Directly after `known_first_party = ["mcp_coder"]`, add:

```toml
# Extras holding dev-only packages: deptry exempts them from DEP002 and reports
# DEP004 if src/ imports them. deptry does not expand mcp-coder[...] self-
# references, so each such extra is named explicitly. langchain-* and mlflow
# are left out on purpose: src/ imports them.
optional_dependencies_dev_groups = ["dev", "types", "typecheck", "test", "tui"]
```

### 2. `pyproject.toml`, `[tool.deptry.per_rule_ignores]`

Delete the `# DEP002: ...` comment lines and the whole `DEP002 = [ ... ]` list.
Keep the `DEP003` comment and list, and `[tool.deptry.package_module_name_map]`,
exactly as they are.

### 3. `docs/repository-setup/python.md`

Replace:

```
> **Customize (`[tool.deptry]` in `pyproject.toml`):** Per-rule ignores and the
> package-to-module name map.
```

with:

```
> **Customize (`[tool.deptry]` in `pyproject.toml`):** The dev-only extras
> (`optional_dependencies_dev_groups`), per-rule ignores and the
> package-to-module name map.
```

## HOW

- deptry reads `[tool.deptry]` from `pyproject.toml`. No code or import changes.
- Don't use `pep621_dev_dependency_groups`; it is deprecated.

## ALGORITHM (verification)

```
run `deptry src` (Bash; no MCP equivalent)
if deptry is not installed           -> write one line to pr_info/.blocked.txt and stop
if output contains any DEP002        -> write one line to pr_info/.blocked.txt and stop
if output says "groups were not found" -> write one line to pr_info/.blocked.txt and stop
if deptry reports any other issue    -> write one line to pr_info/.blocked.txt and stop
run pylint, pytest (fast unit set, -n auto), mypy; run_format_code; commit
```

## DATA

Resulting `[tool.deptry.per_rule_ignores]` contains only the `DEP003` key.

## Acceptance

- `deptry src` exits 0 with no "groups were not found" warning.
- `[tool.deptry.per_rule_ignores]` contains only `DEP003`.
- pylint, pytest and mypy pass.

## Commit

`chore(deptry): replace DEP002 list with optional_dependencies_dev_groups (#1290)`
