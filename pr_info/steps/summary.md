# Summary — #1452 command toolkit: `exit_codes` keys may be ranges (e.g. `1-125`)

## Goal

Some tools exit with a count (dependency-cruiser exits with its number of error
violations; `npm run` passes the code on). Today `exit_codes` maps single codes
only, so exit 3 is `error` unless every count is listed. A table without `0`
also turns a clean run into `error`.

After this change:

- `exit_codes = { 0 = "ok", 1-125 = "findings" }` maps exit 7 to `findings`
  and exit 126 to `error`.
- `exit_codes = { 1 = "findings" }` maps exit 0 to `ok` (unlisted-`0` rule).
- Reversed ranges, overlapping keys, malformed keys and invalid values are
  config errors. `parse_config` still never raises.

## Architectural / design changes

All changes stay inside `src/mcp_coder/toolkits/command/`; the
`toolkits_isolation` import contracts are unaffected.

1. **New table type.** `ExitCodes = dict[int | tuple[int, int], str]` in
   `config.py`. Single codes stay `int` keys; a range `N-M` is stored as the
   tuple key `(N, M)`. The table holds exactly what the user wrote: no implicit
   `0`, ranges not expanded (Windows exit codes are 32-bit).
   `DEFAULT_EXIT_CODES` keeps its contents `{0: "ok", 1: "findings"}`; only its
   annotation widens. `Step.exit_codes` and `_Defaults.exit_codes` use the alias.
2. **Strict key parsing** in the existing `_exit_codes_errors` loop: a key must
   be a `str` that fully matches `([0-9]+)(?:-([0-9]+))?` (ASCII digits only;
   `fullmatch` so a trailing newline fails) with start <= end. `int()` stays
   inside the existing `try/except ValueError`, which also catches keys over
   Python's 4300-digit limit. `+3`, `1_0`, `-1`, `" 3 "`, `"3\n"`, non-ASCII
   digits and non-string keys become config errors.
3. **Overlap check**: every pair of parsed keys, normalised to `(lo, hi)`, is
   compared with `itertools.combinations`; any shared code is a config error
   (covers range/range, code inside a range, and `1` vs `01`). So a code
   matches at most one key.
4. **Lookup lives next to the parser**: new
   `exit_code_status(table: ExitCodes, code: int) -> str` in `config.py`.
   First matching key wins (keys cannot overlap); no match gives `"ok"` for
   code `0`, else `"error"`. `toolkit.py::_run_step` calls it instead of
   `step.exit_codes.get(code, "error")`.
   **Behaviour change:** a table without `0` now maps a clean run to `ok`.
5. **Unchanged**: "replace, no merge" (step table replaces command-level table,
   which replaces the default); a bad command-level table is a global error and
   keeps the default; a bad step table drops the step. Key error messages keep
   the form `exit_codes key must be …, got {key!r}`.

Error messages:

- `exit_codes key must be a code or a range N-M with N <= M, got {key!r}`
- `exit_codes key must not overlap another key, got {key!r} (overlaps {other!r})`
- `exit_codes value for {key!r} must be one of ok, findings, skipped, error, got {status!r}` (unchanged)

## Files

Modified:

- `src/mcp_coder/toolkits/command/config.py` — `ExitCodes` alias, strict key
  parsing, overlap check, `exit_code_status` (steps 1, 2)
- `src/mcp_coder/toolkits/command/toolkit.py` — use `exit_code_status` (step 2)
- `tests/toolkits/command/test_config.py` — `TestExitCodes` (steps 1, 2)
- `tests/toolkits/command/test_toolkit_run.py` — `TestExitCodes` (step 2)
- `docs/configuration/toolkits.md` — two `exit_codes` rows and a
  dependency-cruiser rule (step 3)

Created: none (besides these plan files).

## Steps

1. `step_1.md` — range keys, strict key parsing and overlap check in the parser.
2. `step_2.md` — `exit_code_status` lookup with the unlisted-`0` rule, used by `toolkit.py`.
3. `step_3.md` — documentation in `docs/configuration/toolkits.md`.
