# Architecture Enforcement

An LLM working on this code sees only part of it and doesn't know the big picture. Asked to fix a problem, it will plausibly import across a boundary or bypass a wrapper — the change looks local and the tests pass. The architecture rules make that fail in CI, so an LLM cannot change or disregard the architecture by accident. The rules live in config files, with each rule's rationale as a comment; this page explains why they exist and how to extend them. What runs where: [Quality and Security Checks](../repository-setup/quality-and-security-checks.md).

## Layers

Dependencies flow downward only. Lower layers stay reusable and testable without the upper ones, and a change at the top cannot ripple down. The layer stack is drawn in [architecture.md](architecture.md#5-building-block-view). Ruleset: the `layered_architecture` contract in [`.importlinter`](../../.importlinter) and the layers in [`tach.toml`](../../tach.toml).

## Independence between sibling modules

Modules on the same level don't import each other, so each can change or be tested alone. This comes from `|` siblings in the layers contract, forbidden contracts such as `jenkins_independence` in [`.importlinter`](../../.importlinter), and the `depends_on` lists in [`tach.toml`](../../tach.toml).

Inside a package, submodules import their siblings directly, never through the parent `__init__.py`. A parent that re-exports everything loads every sibling, which creates dependencies nobody declared. Keep `__init__.py` as a facade for outside consumers only.

## Third-party wrappers

One module owns each external library. An upgrade or a replacement then touches one place, and tests mock one place. The same applies to the `mcp_coder_utils` and `subprocess` shims: everything else imports through them. Ruleset: the forbidden contracts in [`.importlinter`](../../.importlinter).

## Shim boundary

Git and the `mcp_workspace` package are reached only through the shims `mcp_coder.mcp_workspace_git` and `mcp_coder.mcp_workspace_github`. Running `git` as a subprocess, or importing `mcp_workspace.git_operations` / `mcp_workspace.github_operations` directly, would bypass them. import-linter cannot resolve those external subpackages, so `RULES` in [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py) guards both the argv and the import rules.

## No import cycles

Cycles make import order fragile and the layering meaningless. Two guards catch them, at different grain: [pylint `R0401`](https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/cyclic-import.html) ([`pyproject.toml`](../../pyproject.toml)) finds any cyclic import between modules and also runs locally, and tach `forbid_circular_dependencies` ([`tach.toml`](../../tach.toml)) catches cycles between the declared top-level modules. The `mlflow_logger_no_cycles` contract in [`.importlinter`](../../.importlinter) is not a general guard but a specific boundary: the MLflow logger must not import the modules that call it.

## No dead code

Unused code misleads an LLM reading the code and costs context. [vulture](https://github.com/jendrikseipp/vulture) finds it; [`vulture_whitelist.py`](../../vulture_whitelist.py) lists the intentional exceptions (API completeness, enum values, base-class attributes, false positives from TypedDicts, fixtures and argparse). The whitelist is deliberately liberal and may hold items that are now truly dead, so review it now and then.

## Declared dependencies match imports

An import that works only through a transitive dependency breaks when that dependency changes. [deptry](https://deptry.com/) checks this. Ruleset: `[tool.deptry]` in [`pyproject.toml`](../../pyproject.toml).

## Small files

A file must fit an LLM's context window to be read whole. [`mcp-coder check file-size`](../cli-reference.md#check-file-size) enforces the limit. Ruleset: [`.large-files-allowlist`](../../.large-files-allowlist) and the line limit in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

## Why both import-linter and tach

Neither covers everything. [import-linter](https://import-linter.readthedocs.io/en/stable/) handles third-party isolation, `|` siblings and forbidden contracts. [tach](https://docs.gauge.sh/) handles high-level layers, explicit `depends_on` lists and cycle detection, but does not isolate third-party libraries and struggles with `__init__.py` re-exports. Use tach for the coarse layers and import-linter for fine-grained rules.

## Adding or changing rules

- **New external dependency** that one module should own: add a third-party isolation contract (wrapper pattern).
- **New top-level module:** assign it a layer in both [`.importlinter`](../../.importlinter) and [`tach.toml`](../../tach.toml).
- **Two modules that must stay independent:** put them on one `|` row, or add a forbidden contract.
- **Moving or renaming modules:** update the rules; see the [Safe Refactoring Guide](../processes-prompts/refactoring-guide.md).
- **An import that is intentionally allowed despite a rule:** add it to `ignore_imports` with a comment saying why.

## Visualisation

[pydeps](https://github.com/thebjorn/pydeps) draws the actual import graph ([`tools/pydeps_graph.sh`](../../tools/pydeps_graph.sh), output in [dependencies/](dependencies/readme.md)). It is a picture, not a check.
