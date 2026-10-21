# Summary — Enable ruff `UP` (pyupgrade) (#1166)

Part of epic #1163. Depends on #1164 and #1169 (both landed; `F` is enforced since #1258).

## Goal

Add `"UP"` to `[tool.ruff.lint] select` and make `src` + `tests` UP-clean, using
ruff's autofixes. No `# noqa: UP*` is added, and no `UP*` entry goes into `ignore`.

## Measured baseline (`main` @ `2da86b3`)

529 findings across 10 rules: UP045 192, UP006 135, UP017 76, UP035 68, UP015 21,
UP007 17, UP037 10, UP041 5, UP042 3, UP024 2. Only UP042 needs `--unsafe-fixes`.

## Architectural / design changes

None at the architecture level. The project's lint policy changes, and the rest is a
mechanical rewrite of syntax:

- **Lint policy:** `UP` joins the enforced rule set, so new code must use the modern
  forms. `target-version = "py311"` lets ruff choose the forms (`requires-python >= 3.11`).
- **Annotations:** `Optional[X]`/`Union[X, Y]` → `X | None`/`X | Y`;
  `List`/`Dict`/`Tuple` → builtins; quoted annotations are unquoted. All of these
  evaluate natively on 3.11, so dataclasses, TypedDicts and NamedTuples that read
  annotations at runtime keep working.
- **Imports:** deprecated `typing` imports move to `collections.abc`, and
  `timezone.utc` → `datetime.UTC`. Imports the rewrite leaves unused are removed (`F401`).
- **Aliases:** `IOError` etc. → `OSError`; `socket.timeout`/`asyncio.TimeoutError`
  → `TimeoutError`; redundant `open()` modes are dropped.
- **Enums (only semantic touch):** `LivenessRule` and `SessionAction` in
  `workflows/vscodeclaude/types.py` change from `(str, Enum)` to `StrEnum`. Equality,
  hashing and `json.dumps` behave the same. `str()`/f-string output becomes the
  value. No `src` code formats these enums with `str()` or in f-strings (they are used
  only in `==`, constructor arguments and dict keys), so runtime behaviour is unchanged.

## Files created / modified

| Path | Change |
|---|---|
| `pyproject.toml` | add `"UP"` to `[tool.ruff.lint] select` |
| `src/mcp_coder/**/*.py` | ruff autofix rewrites (~280 sites) |
| `tests/**/*.py` | ruff autofix rewrites (~247 sites) |
| `src/mcp_coder/workflows/vscodeclaude/types.py` | `LivenessRule`, `SessionAction` → `StrEnum` |
| `tests/workflows/review/test_gates.py` | `_UnlistedCIStatus` → `StrEnum`; docstring updated |

No new modules or folders. `tools/` is out of scope because CI does not lint it.

## Steps

There is one step, so one commit. Enabling `UP` makes ruff fail until every site is
fixed, so the config change and the fixes cannot be split into separate green commits.
There is no new test: ruff itself is the enforcement, and mypy `--strict` plus the
full pytest suite cover correctness.

- [Step 1](./step_1.md): enable `UP`, apply safe + UP042 fixes, format, verify.

## Scheduling note

The diff touches most files, so land it in its own PR when few branches are in flight.
