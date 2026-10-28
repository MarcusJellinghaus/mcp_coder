# Architecture Enforcement

An LLM working on this code sees only part of it and doesn't know the big picture. Asked to fix a problem, it will plausibly import across a boundary or bypass a wrapper — the change looks local and the tests pass. The architecture rules make that fail in CI, so an LLM cannot change or disregard the architecture by accident. The rules live in config files, with each rule's rationale as a comment; this page explains why they exist. What runs where: [Quality and Security Checks](../repository-setup/quality-and-security-checks.md).

## Layers

Dependencies flow downward only. Lower layers stay reusable and testable without the upper ones, and a change at the top cannot ripple down. Ruleset: the `layered_architecture` contract in [`.importlinter`](../../.importlinter) and the layers in [`tach.toml`](../../tach.toml).

## Independence between sibling modules

Modules on the same level don't import each other, so each can change or be tested alone. This comes from `|` siblings in the layers contract, forbidden contracts such as `jenkins_independence` in [`.importlinter`](../../.importlinter), and the `depends_on` lists in [`tach.toml`](../../tach.toml).

## Third-party wrappers

One module owns each external library. An upgrade or a replacement then touches one place, and tests mock one place. The same applies to the `mcp_coder_utils` and `subprocess` shims: everything else imports through them. Ruleset: the forbidden contracts in [`.importlinter`](../../.importlinter).

## Shim boundary

Git and the `mcp_workspace` package are reached only through the shims `mcp_coder.mcp_workspace_git` and `mcp_coder.mcp_workspace_github`. Running `git` as a subprocess, or importing `mcp_workspace.git_operations` / `mcp_workspace.github_operations` directly, would bypass them. import-linter cannot resolve those external subpackages, so `RULES` in [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py) guards both the argv and the import rules.

## No import cycles

Cycles make import order fragile and the layering meaningless. Four guards catch them: the `mlflow_logger_no_cycles` contract in [`.importlinter`](../../.importlinter), pycycle ([`tools/pycycle_check.sh`](../../tools/pycycle_check.sh)), pylint `R0401` ([`pyproject.toml`](../../pyproject.toml)) and tach `forbid_circular_dependencies` ([`tach.toml`](../../tach.toml)).

## No dead code

Unused code misleads an LLM reading the code and costs context. Ruleset: [`vulture_whitelist.py`](../../vulture_whitelist.py) lists the intentional exceptions.

## Declared dependencies match imports

An import that works only through a transitive dependency breaks when that dependency changes. Ruleset: `[tool.deptry]` in [`pyproject.toml`](../../pyproject.toml).

## Small files

A file must fit an LLM's context window to be read whole. Ruleset: [`.large-files-allowlist`](../../.large-files-allowlist) and the line limit in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml).

## Tools

- [import-linter](https://import-linter.readthedocs.io/en/stable/) — layers, independence, wrappers, cycles — [`.importlinter`](../../.importlinter)
- [tach](https://docs.gauge.sh/) — layers, independence, cycles — [`tach.toml`](../../tach.toml)
- [pycycle](https://pypi.org/project/pycycle/) — cycles — [`tools/pycycle_check.sh`](../../tools/pycycle_check.sh)
- [pylint `R0401`](https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/cyclic-import.html) — cycles — [`pyproject.toml`](../../pyproject.toml)
- forbidden-calls — shim boundary — [`tools/check_forbidden_calls.py`](../../tools/check_forbidden_calls.py)
- [vulture](https://github.com/jendrikseipp/vulture) — dead code — [`vulture_whitelist.py`](../../vulture_whitelist.py)
- [deptry](https://deptry.com/) — declared dependencies — [`pyproject.toml`](../../pyproject.toml)
- [`mcp-coder check file-size`](../cli-reference.md#check-file-size) — small files — [`.large-files-allowlist`](../../.large-files-allowlist), [`ci.yml`](../../.github/workflows/ci.yml)
- [pydeps](https://github.com/thebjorn/pydeps) — visualisation only, not a check — [`tools/pydeps_graph.sh`](../../tools/pydeps_graph.sh)
