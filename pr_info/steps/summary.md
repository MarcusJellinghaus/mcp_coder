# Summary — #1294 verify: support GitHub rulesets in branch protection checks

## Goal

`mcp-coder verify` shows a false negative for repos protected by GitHub
**rulesets**, because only the classic branch-protection API is consulted.
The ruleset evaluation itself is implemented upstream in **mcp-workspace**
(MarcusJellinghaus/mcp-workspace#350, `verify_github()`). This repo only:

1. renders the one new row upstream emits (`require_pull_request`),
2. documents the changed behaviour and token permissions,
3. consumes the upgraded mcp-workspace (environment reinstall — no pyproject edit,
   since `pyproject.toml` lists bare `mcp-workspace` / an unpinned git URL and there
   is no lock file).

## Architectural / design changes

- **No new modules, functions, or control flow.** `_format_section()` in
  `verify_formatting.py` already renders `_BRANCH_PROTECTION_CHILDREN` generically:
  indent 4, `[OK]`/`[ERR]`/`[WARN]` marker, error suffix when `ok is False`, and
  suppression unless the parent `branch_protection` row is `ok is True`.
  Registering the new key in `_LABEL_MAP` and `_BRANCH_PROTECTION_CHILDREN` is the
  whole formatter change.
- **Ordering contract unchanged:** `_format_section` relies on `branch_protection`
  preceding its children in the result dict; upstream emits `require_pull_request`
  after `branch_protection`.
- **Parent value printed verbatim:** the new source-naming text
  (e.g. `main protected (ruleset: "Protect main" + classic)`) comes from
  mcp-workspace; no formatter change needed.
- **Exit codes unaffected:** all protection rows (including the new one) stay
  `severity="warning"` upstream; mcp-coder's exit-code logic is untouched.
- **Backward compatible:** older mcp-workspace results never contain the key, so the
  formatter change is safe before or after the dependency upgrade. Without it, an
  unregistered key would print raw at indent 2 — hence step 1 ships first.

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify_formatting.py` | add `require_pull_request` to `_LABEL_MAP` and `_BRANCH_PROTECTION_CHILDREN` |
| `tests/cli/commands/test_verify_format_section_basic.py` | add key to `_GITHUB_KEYS`; extend existing `TestBranchProtectionNesting` tests |
| `docs/repository-setup/github.md` | permissions wording, "not verifiable" note, security-rows statement, bypass-actors sentence |

No files or folders are created (besides these plan files).

## Steps

1. [step_1.md](./step_1.md) — formatter registration + tests (TDD).
2. [step_2.md](./step_2.md) — docs update, after mcp-workspace#350 is released and its
   permission findings are recorded.
