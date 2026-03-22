# Pylint W-Category Cleanup — Results Summary

<!-- PR_SUMMARY_CONTEXT: Use this file when drafting the pull request description.
     It contains the actual outcomes of the pylint warning cleanup work. -->

## What changed

Previously, all pylint W-category warnings were blanket-disabled in `pyproject.toml`.
This branch enables them, fixing what's practical and selectively suppressing the rest.

## Breakdown by warning type

### Genuinely fixed (~80+ instances)

| Warning | Code | What was done |
|---|---|---|
| unused-import | W0611 | ~22 imports removed |
| unused-variable | W0612 | ~43 variables removed |
| unused-argument | W0613 | ~5 prefixed with `_` |
| unspecified-encoding | W1514 | ~23 `open()` calls gained `encoding="utf-8"` |
| raise-missing-from | W0150 | ~5 `raise X` → `raise X from e` |
| unnecessary-pass | W0107 | Removed dead `pass` statements |
| unnecessary-lambda | W0108 | Replaced with direct callable references |
| bare-except | W0702 | Narrowed to `except Exception` |
| implicit-str-concat | W1404 | Fixed string concatenation |

### Suppressed with inline `# pylint: disable=` (247 total)

| Warning | Code | Count | Rationale |
|---|---|---|---|
| broad-exception-caught | W0718 | 223 | Intentional catch-all in CLI/workflow error handling; TODO comments added |
| global-statement | W0603 | 7 | Module-level singletons |
| protected-access | W0212 | 7 | No public API in PyGithub/GitPython/python-jenkins |
| unused-argument | W0613 | 5 | Pytest fixtures / callback signatures |
| unused-import | W0611 | 3 | Conftest re-exports / optional import fallbacks |
| deprecated-argument | W4903 | 2 | `onexc` requires Python 3.12+, using `onerror` for now |

### Suppressed globally in `pyproject.toml` (10 codes)

W1203 (logging-fstring), W0621 (redefined-outer-name), W0511 (fixme),
W0212 (protected-access), W0613 (unused-argument), W0611 (unused-import),
W0404 (reimported), W0718 (broad-exception-caught), W0706 (try-except-raise),
W4903 (deprecated-argument).

## Known redundancy

W0718 `broad-exception-caught` is both globally disabled in `pyproject.toml` **and** has
223 inline disables. The inline comments are currently redundant but serve as documentation
for future narrowing if the global disable is removed.
