# Implementation Review Log — run 1

**Branch**: `fix/install-optional-mcp-config-cli`
**Commit under review**: cdea89e5 — fix(install): stop requiring the mcp-config CLI after install
**Context**: No dedicated issue; the commit references #1151 (follow-up refactor to move the installer into the package). No `pr_info/steps/` plan exists for this branch.

**Scope of the change**
- `tools/install.py` — split the required-CLI list; `mcp-config` becomes optional
- `tests/tools/test_install_py.py` — unit tests for `_phase_versions`
- `docs/architecture/architecture.md`, `docs/getting-started/installation.md` — doc updates

## Round 1 — 2026-09-01

**Findings**
- No critical issues. mypy clean; pytest 5445 passed / 2 skipped; pylint clean on changed lines (one pre-existing `W1510` in the untouched `run()` helper).
- Reviewer verified the "every target ends up with these three" claim holds across all sibling repos, and that `mcp-config-tool` is referenced only by mcp-workspace as an optional extra — so the required/optional split and the architecture.md edit are accurate.
1. `tests/tools/test_install_py.py` — `test_mcp_config_is_optional_not_required` asserts on module constants rather than behaviour; fully implied by the two behavioural tests below it.
2. `tests/tools/test_install_py.py` — binaries picked via `CLI_BINARIES[1:]` / `CLI_BINARIES[0]`, coupling tests to tuple order.
3. `src/mcp_coder/cli/commands/coordinator/command_templates.py` — Windows verification template still probes `where mcp-config` / `mcp-config --version`; prints a misleading "not recognized" on exactly the targets this fix unblocks.
4. Required CLI list still hardcoded in the installer.

**Decisions**
1. **Accept** — tests implementation, not behaviour; deletion is free.
2. **Accept** — literal names read better; trivial, same file.
3. **Accept** — the same hardcoded assumption living in a second place, producing the false alarm this commit's doc change was written to prevent.
4. **Skip** — subject of issue #1151, explicitly out of scope for this targeted fix.

**Changes**
- Deleted the constants-only test; `test_missing_required_cli_exits` now uses explicit literals `["mcp-tools-py", "mcp-workspace"]` and asserts on `"mcp-coder"`.
- Dropped the two `mcp-config` lines from `DEFAULT_TEST_COMMAND_WINDOWS`. The POSIX `DEFAULT_TEST_COMMAND` never probed it, so the templates are now consistent; no label was added because no other line in either template carries one.
- Checks after: pytest 5444 passed / 2 skipped, mypy clean, pylint clean on the touched directories.

**Status**: committed

## Round 2 — 2026-09-01

**Findings**
- No critical issues. Reviewer verified `e7aff7a3` directly: the two removed lines were top-level batch commands, not inside an `if (...)` block, so the Windows template is still valid; it now probes the same three binaries as the POSIX `DEFAULT_TEST_COMMAND`; no test asserted on the removed lines; the reworked test really does hit the required-missing branch.
- pytest 5444 passed / 2 skipped; mypy clean; pylint clean.
1. `docs/environments/environments.md:138` cites `command_templates.py:88-89`; `e7aff7a3` removed two lines above that point, so the citation is off by exactly this commit's edit.
2. `test_all_required_present_succeeds` also seeds the optional binary — the name is slightly broader than what it does.
3. `tests/tools/test_install_py.py:453` still builds its set from `list(install.CLI_BINARIES)`.
4. `tools/install.py:450-458` picks required-vs-optional with an `elif name in CLI_BINARIES` inside a concatenated loop.
- Noted, out of scope: `tools/` is outside the mypy/pylint/ruff target directories, so `install.py` gets no static checking. Subsumed by #1151.

**Decisions**
1. **Accept** — staleness caused by this branch. Fix by dropping the line numbers rather than re-pinning, so it cannot go stale again.
2. **Skip** — cosmetic rename; the test does cover the optional-present branch.
3. **Skip** — here the constant *is* the intent ("all required present, optional absent"), so the coupling is deliberate and self-maintaining.
4. **Skip** — current form is short and readable; splitting it is a style preference, not a defect.

**Changes**
- `docs/environments/environments.md`: dropped the line numbers from the `command_templates.py` citation.

**Status**: committed

_Addendum to round 2_: while fixing the cited reference, the engineer found a second stale citation in the same file (line 127 pinned `cd %VENV_BASE_DIR%` at `command_templates.py:49` plus five siblings at `:242`, `:280`, `:318`, `:356`, `:394`; `e7aff7a3` shifted the latter five). Both were replaced with line-number-free references. A `tools/install.py:17` citation was checked and left — that line is above this branch's edits and still accurate.

## Round 3 — 2026-09-01

**Findings**
- No critical issues. Reviewer verified `10d5a9a8` against the source: "six times" is the correct count, the re-wrapped paragraph preserved every clause word-for-word, and the smoke-test claim still matches `DEFAULT_TEST_COMMAND_WINDOWS`. The `tools/install.py:17` citation was checked and is still accurate. No `command_templates.py:<line>` citations remain in the repo.
- The `mcp-config` optionality claim was re-verified independently: `mcp-config-tool` appears only in mcp-workspace's install-from-github list and as its optional `config` extra; mcp-coder's own `pyproject.toml` never references it.
- pytest 5444 passed / 2 skipped; mypy clean; pylint clean.
1. `docs/environments/environments.md:126-127` — the round-2 reword introduced a claim the original did not make: "across all the templates" overstates, since all six `cd %VENV_BASE_DIR%` occurrences are in the Windows templates. The seven POSIX templates use `source .venv/bin/activate`.

**Decisions**
1. **Accept** — a wrong statement introduced by the previous round's fix; one-word correction.

**Changes**
- `docs/environments/environments.md`: narrowed the claim from all templates to the Windows templates.

**Status**: committed

## Round 4 — 2026-09-01

**Findings**: none. The corrected sentence was verified against the source (six `cd %VENV_BASE_DIR%` occurrences, all in the six `*_WINDOWS` templates), and the earlier rewritten citations still hold. Final once-over confirmed `_phase_versions` exits non-zero only for missing *required* binaries, `--check` still short-circuits before the loop, the three tests cover the three real branches, and no other place in the repo requires the `mcp-config` binary.

**Decisions**: nothing to accept.

**Changes**: none.

**Status**: no changes needed — review loop terminates.

## Final Status

**Result**: approved. Four review rounds; rounds 1-3 produced changes, round 4 was clean. No critical issues were found at any point.

**Commits produced by the review**
- `e7aff7a3` fix(review): apply install-optional-mcp-config review findings
- `10d5a9a8` docs(environments): drop stale command_templates.py line numbers
- `7d3616f3` docs(environments): scope the cd %VENV_BASE_DIR% count to Windows templates

**Checks**
- pytest (unit subset, `-n auto`, integration markers excluded): pass. One timing-sensitive test, `tests/llm/providers/langchain/test_approval_stream_bridge.py::test_sub_inactivity_pause_is_excluded_from_the_overall_cap`, flaked once under parallel load and passed in isolation. That file is untouched by this branch (it arrived with #1148 on main) — pre-existing flake, out of scope.
- mypy: clean. pylint: clean. vulture: no output. import-linter: 21 contracts kept, 0 broken.

**Deferred**
- Issue #1151 — move `tools/install.py` into the package and replace the hardcoded required-CLI list with a caller-declared `--require-cli` flag. It also subsumes the fact that `tools/` sits outside the mypy/pylint/ruff target directories, so `install.py` currently gets no static checking. Not touched here by design.

**Working tree note**: `tests/workflows/vscodeclaude/test_assessment_issue_facts.py` carries an unstaged isort rewrap produced by a `run_format_code` run. It is unrelated to this branch and was deliberately kept out of every commit.
