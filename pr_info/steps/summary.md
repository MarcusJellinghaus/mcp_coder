# Summary: Render branch protection checks in GitHub section

**Issue:** #899

## Goal

Render branch protection sub-checks (CI checks required, strict mode, force push, branch deletion) as indented children under the `Branch protection` line in the `=== GITHUB ===` section of `mcp-coder verify`. This is a **formatter-only change** — the upstream `verify_github()` already returns all required data.

## Design

### Before (current — flat rendering)

```
=== GITHUB ================================================
  Token configured     [OK] configured (scopes: repo, workflow)
  Authenticated user   [OK] MarcusJellinghaus
  Repo URL             [OK] https://github.com/...
  Repo accessible      [OK] MarcusJellinghaus/mcp-coder
  Branch protection    [OK] main protected
  CI checks required   [OK] 8 checks configured
  Strict mode          [OK] enabled
  Force push           [OK] disabled
  Branch deletion      [OK] disabled
```

### After (nested rendering)

```
=== GITHUB ================================================
  Token configured     [OK] configured (scopes: repo, workflow)
  Authenticated user   [OK] MarcusJellinghaus
  Repo URL             [OK] https://github.com/...
  Repo accessible      [OK] MarcusJellinghaus/mcp-coder
  Branch protection    [OK] main protected
    CI checks required [OK] 8 checks configured
    Strict mode          enabled
    Force push         [OK] disabled
    Branch deletion    [OK] disabled
```

When parent fails (children always suppressed):

```
  Branch protection    [WARN] main is not protected
```

### Architectural change

**One constant + ~10 lines of logic in `_format_section`:**

- Add a module-level `_BRANCH_PROTECTION_CHILDREN` frozenset identifying the 4 child keys.
- In the existing `for key, entry in result.items()` loop:
  - Track `branch_protection`'s `ok` state when encountered.
  - For child keys: skip entirely if parent failed; otherwise render at 4-space indent.
  - For `strict_mode`: render value only (no status symbol) — it's informational, not a health check.
- No changes to `_format_section`'s signature, no new parameters, no new abstractions.
- All other sections (Claude, LangChain, MLflow) are unaffected — child keys only exist in GitHub results.

### Key decisions (from issue)

| Topic | Decision |
|-------|----------|
| Nesting scope | Only `branch_protection` children — opt-in via constant, not implicit |
| Strict mode | Neutral/informational — no symbol, just `enabled`/`disabled` |
| Child suppression | Always suppress when `branch_protection.ok is False` |
| Symbols | Existing `[OK]`/`[ERR]`/`[WARN]` — no Unicode |

## Files modified

| File | Change |
|------|--------|
| `src/mcp_coder/cli/commands/verify.py` | Add `_BRANCH_PROTECTION_CHILDREN` frozenset, modify `_format_section` loop |
| `tests/cli/commands/test_verify_format_section.py` | Add tests for nested rendering, child suppression, neutral strict mode |

No new files or modules created.

## Steps

- [Step 1](step_1.md) — Tests for nested rendering and child suppression
- [Step 2](step_2.md) — Implement nested rendering in `_format_section`
