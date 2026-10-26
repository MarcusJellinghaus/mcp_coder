# Summary — #1294 verify: support GitHub rulesets in branch protection checks

## Goal

`mcp-coder verify` shows a false negative for repos protected by GitHub
**rulesets**, because only the classic branch-protection API is consulted.
The ruleset evaluation itself is implemented upstream in **mcp-workspace**
(MarcusJellinghaus/mcp-workspace#350, merged via #354, `verify_github()`) and is
already installed in the environment (no pyproject edit: `mcp-workspace` is
unpinned and there is no lock file). This repo only:

1. renders the one new row upstream emits (`require_pull_request`),
2. shows upstream's `error` note on not-verifiable (`ok=None`) protection rows, so
   the failing source (classic or rulesets) is visible,
3. documents the changed "not verifiable" behaviour.

Decisions from the plan review: [Decisions.md](./Decisions.md).

## Architectural / design changes

- **No new modules or functions.** `_format_section()` in `verify_formatting.py`
  already renders `_BRANCH_PROTECTION_CHILDREN` generically: indent 4,
  `[OK]`/`[ERR]`/`[WARN]` marker, suppression unless the parent `branch_protection`
  row is `ok is True`. Registering the new key in `_LABEL_MAP` and
  `_BRANCH_PROTECTION_CHILDREN` renders the row.
- **Error display widened (two conditions):**
  - child rows: `error` shown when `ok is not True` (was: `ok is False`);
  - generic branch: additionally shown when `ok is None` and the key is
    `branch_protection`. Other `ok=None` rows (permissions, security, other
    sections) are unchanged. `ok=True` rows keep hiding `error`.
  - Why: upstream records the failing source only in `error`
    (e.g. `rulesets not verifiable: HTTP 403`); the value alone
    (`not verifiable — HTTP 403`) doesn't say which source failed.
- **New upstream state:** a child can be `ok=None` under an `[OK]` parent (classic
  protected, rulesets unreadable, classic negative on that flag). Renders as
  `[WARN]` via the existing branch.
- **Ordering contract unchanged:** `_format_section` relies on `branch_protection`
  preceding its children in the result dict; upstream emits `require_pull_request`
  right after `branch_protection`.
- **Parent value printed verbatim:** the source-naming text
  (e.g. `main protected (ruleset: "Protect main" + classic)`) comes from
  mcp-workspace.
- **Exit codes unaffected:** all protection rows stay `severity="warning"`.

## Files modified

| File | Change |
|---|---|
| `src/mcp_coder/cli/commands/verify_formatting.py` | add `require_pull_request` to `_LABEL_MAP` and `_BRANCH_PROTECTION_CHILDREN`; widen the two `error` display conditions |
| `tests/cli/commands/test_verify_format_section_basic.py` | add key to `_GITHUB_KEYS`; extend `TestBranchProtectionNesting` tests (upstream key order, flipped 403 assertion); three new error-display tests |
| `docs/repository-setup/github.md` | "not verifiable" note for the merged behaviour; bypass-actors sentence; no permission statement for the ruleset endpoints |

No files or folders are created (besides these plan files).

## Steps

1. [step_1.md](./step_1.md) — formatter registration, error display + tests (TDD).
2. [step_2.md](./step_2.md) — docs update.
