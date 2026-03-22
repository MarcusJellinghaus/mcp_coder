# Summary: Enable and Clean Up Pylint Warnings (#493)

## Overview

This PR enables pylint W-category warnings for both `src/` and `tests/` by fixing or
inline-disabling all existing occurrences, then updating `pyproject.toml` as the final
commit so CI stays green throughout.

**No new files are created. No logic changes. Pure lint cleanup.**

---

## Architectural / Design Changes

None. This is exclusively a lint-hygiene PR. The approach for each warning type:

| Pattern | Decision | Rationale |
|---------|----------|-----------|
| Unused imports / variables | **Remove** | Dead code; zero risk |
| Unused arguments | **Rename to `_`** | Preserves API contract, signals intent |
| `raise X` inside `except` without `from e` | **Add `from e`** | Proper exception chaining; no behaviour change |
| F-string without interpolation | **Remove `f` prefix** | Trivial fix |
| Broad exception raised (`raise Exception`) | **Use `RuntimeError`** | Minimal specific type |
| Try-except-raise (W0706) | **Add inline disable** | Intentional re-raise pattern for subprocess isolation |
| Deprecated `onerror=` arg (W4903) | **Add inline disable** | `onexc=` requires Python 3.12+; project minimum is 3.11 |
| Protected-access (W0212, `src/` only) | **Add inline disable per line** | Third-party API workaround already documented in comments; no public API exists |
| Global statements (W0603) | **Add inline disable per line** | Module-level singletons; `lru_cache` would break test resets |
| Broad-except (W0718, `src/`) | **Inline disable with justification** | Intentional catch-all boundaries; adding TODO where narrowing is possible |
| `tests/` W0212, W0613, W0611, W0404 | **Per-file-ignores in config** | Standard pytest patterns; not code quality issues |
| `tests/` W0621 | **Global disable in config** | Pytest fixture redefined-outer-name; already intended |
| W0511 (fixme/TODO) | **Global disable in config** | Informational only |
| W1203 (logging f-string) | **Global disable in config** | Project deliberately uses f-strings for readability |

---

## Commit Order (CI-safe, 14 steps)

### src/ steps (8 steps):
1. **Step 1** — src/ W0611: unused imports (36 occurrences)
2. **Step 2** — src/ W0612: unused variables (5 occurrences)
3. **Step 3** — src/ W0613 + W1309: unused arguments + bare f-string (9 occurrences)
4. **Step 4** — src/ W0707 + W0719: raise-missing-from + broad-exception-raised (8 occurrences)
5. **Step 5** — src/ W0706 + W4903: try-except-raise + deprecated arg inline-disables (4 occurrences)
6. **Step 6** — src/ W0603: global-statement inline-disables (7 occurrences)
7. **Step 7** — src/ W0212: protected-access inline-disables (11 occurrences)
8. **Step 8** — src/ W0718: broad-exception-caught inline-disables (181 occurrences)

### tests/ steps (5 steps):
9. **Step 9** — tests/ W0612: unused variables (43 occurrences)
10. **Step 10** — tests/ W1514: unspecified encoding (23 occurrences)
11. **Step 11** — tests/ W0718: broad-exception-caught inline-disables (31 occurrences)
12. **Step 12** — tests/ W0107 + W0108 + W0702 + W0719: small mechanical fixes (10 total)
13. **Step 13** — tests/ W1404 + W0201: string concat + attribute-outside-init (6 total)

### Config step (1 step):
14. **Step 14** — pyproject.toml config change (MUST be last — enables warnings in CI)
