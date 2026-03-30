# Implementation Review Log — Run 1

**Issue:** #624 — CLI: add '--help' hint to argument error messages
**Date:** 2026-03-30

## Round 1 — 2026-03-30

**Findings:**
- C1: Stray `test_parser.py` at repo root (scratch file committed accidentally)
- C2: 5 manual error paths print "Error:" to stdout but help hint to stderr (inconsistent streams)
- S1: `_handle_commit_command` prints `'None'` when no subcommand given
- S2: `_print_message` is a private argparse method
- S3: `self.exit(2, "")` passes no-op empty string argument

**Decisions:**
- C1: **Accept** — junk file on the branch, must delete
- C2: **Accept** — Boy Scout fix, branch touches these exact blocks, bounded effort
- S1: **Skip** — pre-existing behavior, branch only added hint + logger downgrade
- S2: **Skip** — CPython's own `error()` uses `_print_message`; speculative concern
- S3: **Accept** — trivial cleanup

**Changes:**
- Deleted `test_parser.py`
- Added `file=sys.stderr` to 5 `print("Error: ...")` calls in `main.py`
- Changed `self.exit(2, "")` to `self.exit(2)` in `parsers.py`
- Updated 5 test assertions from `captured.out` to `captured.err` in `test_main.py`

**Status:** Committed (497c167)

## Round 2 — 2026-03-30

**Findings:**
- S1: `_print_message` is private API (repeat from Round 1)
- S2: Minor inaccuracy in planning doc (`summary.md` says "delegates to super().error()" but implementation reimplements)

**Decisions:**
- S1: **Skip** — already triaged in Round 1, speculative
- S2: **Skip** — pr_info/ is ephemeral, no code impact

**Changes:** None

**Status:** No changes needed

## Final Status

Review complete. 2 rounds performed, 1 commit produced (497c167). No remaining issues. Branch is CI-green and up to date with main.
