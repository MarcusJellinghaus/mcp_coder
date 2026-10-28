# Step 3 — Create `enforcement.md`, point the badge and the docs index at it

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` exactly.
> Write `docs/architecture/enforcement.md`: short, why-not-what, following the CLAUDE.md
> writing style. Take facts from the ruleset files, not from the existing docs. No contract
> lists, no layer tables, no counts. Then update the README badge and `docs/README.md`.
> Make one commit.

## WHERE
- `docs/architecture/enforcement.md` (new)
- `README.md` (the `architecture` badge on line 5)
- `docs/README.md` (*Architecture & Design* list)

## WHAT — structure of `enforcement.md`

```
# Architecture Enforcement
<intro: 3–5 sentences>
## Layers
## Independence between sibling modules
## Third-party wrappers
## Shim boundary
## No import cycles
## No dead code
## Declared dependencies match imports
## Small files
## Tools
```

- **Intro (the LLM angle):** an LLM sees only part of the codebase and doesn't know the big
  picture. It will plausibly "fix" a problem by importing across a boundary or bypassing a
  wrapper. The rules make that fail in CI, so the LLM cannot change or disregard the
  architecture. The rules live in config files with their rationale as comments; this page
  explains why they exist. What runs where: link to
  `../repository-setup/quality-and-security-checks.md`.
- **Concept sections:** 2–4 sentences each, why only. Name the ruleset file, don't describe the rules:
  - *Layers:* dependencies flow downward, so lower layers stay reusable and testable without
    the upper ones. Ruleset: `layered_architecture` in `.importlinter` and `tach.toml`.
  - *Independence:* sibling modules don't import each other, so each can change or be tested
    alone. Mechanism (one sentence, no "independence contracts"): `|` siblings in the layers
    contract, forbidden contracts such as `jenkins_independence`, tach `depends_on`.
  - *Third-party wrappers:* one module owns each external library, so an upgrade or replacement
    touches one place. Includes the `mcp_coder_utils` and `subprocess` shims (import-linter contracts).
  - *Shim boundary:* git and mcp_workspace only via their shims (`mcp_coder.mcp_workspace_git`,
    `mcp_coder.mcp_workspace_github`). Guarded by `RULES` in `tools/check_forbidden_calls.py`.
    Describe the rules that are in `RULES` at implementation time (#1350 may have moved the import
    rules to `.importlinter`; if so, say the argv rule is in forbidden-calls and the import rules are
    in `.importlinter`).
  - *No import cycles:* cycles make import order fragile and the layering meaningless. Four
    guards: the `mlflow_logger_no_cycles` contract in `.importlinter`, pycycle (`tools/pycycle_check.sh`),
    pylint `R0401` (`pyproject.toml`), tach `forbid_circular_dependencies` (`tach.toml`).
  - *No dead code:* unused code misleads an LLM reading the code and costs context. Ruleset:
    `vulture_whitelist.py`.
  - *Declared dependencies:* an import that works only through a transitive dependency breaks when
    that dependency changes. Ruleset: `[tool.deptry]` in `pyproject.toml`.
  - *Small files:* a file must fit an LLM's context window to be read whole. Ruleset:
    `.large-files-allowlist`, 750-line limit in `.github/workflows/ci.yml`.
- **`## Tools`:** a bullet list, one line per tool: name linked to its docs — concept(s) — ruleset link.
  - import-linter — https://import-linter.readthedocs.io/en/stable/ — layers, independence, wrappers, cycles — `.importlinter`
  - tach — https://docs.gauge.sh/ — layers, independence, cycles — `tach.toml`
  - pycycle — https://pypi.org/project/pycycle/ — cycles — `tools/pycycle_check.sh`
  - pylint `R0401` — https://pylint.readthedocs.io/en/stable/user_guide/messages/refactor/cyclic-import.html — cycles — `pyproject.toml`
  - forbidden-calls — shim boundary — `tools/check_forbidden_calls.py`
  - vulture — https://github.com/jendrikseipp/vulture — dead code — `vulture_whitelist.py`
  - deptry — https://deptry.com/ — declared dependencies — `pyproject.toml`
  - `mcp-coder check file-size` — `../cli-reference.md#check-file-size` — small files — `.large-files-allowlist`, `ci.yml`
  - pydeps — https://github.com/thebjorn/pydeps — visualisation only, not a check — `tools/pydeps_graph.sh`

Relative links from `docs/architecture/`: the repo root is `../../` (e.g. `../../.importlinter`).

## HOW — other edits
- `README.md` line 5: replace the `architecture` badge with
  `[![architecture](https://img.shields.io/badge/architecture-enforced-blue)](docs/architecture/enforcement.md)`.
  Leave the other badges on the line untouched.
- `docs/README.md` *Architecture & Design*: after *Architecture Overview*, add
  `- **[Architecture Enforcement](architecture/enforcement.md)** - Why the architecture rules are enforced mechanically`.

## ALGORITHM
None.

## DATA
None.

## Checks
- Every relative link in `enforcement.md` resolves (`list_directory` / `search_files` for each target).
- `search_files(pattern="import--linter", glob="README.md")` returns no hits.
- `search_files(pattern="\\d+ contracts", glob="docs/architecture/enforcement.md")` returns no hits.

## Commit
`docs(architecture): explain why the architecture rules are enforced`
