# Decisions

Decisions taken while updating the plan for issue #1151. One entry per point Marcus
raised in the plan-review handoff.

## 1. The `.sh` wrapper's hard-fail must honour `_SOURCED`

`tools/reinstall_local.sh` is documented as `source`-able and already computes `_SOURCED`
(`:8`). The new driver-resolution hard-fail was specified only in `.bat` form
(`exit /b 1`). Every failure path on `.sh` now uses `return 1` when sourced, `exit 1`
otherwise — a bare `exit 1` would kill the developer's interactive shell.

Applied in `step_5.md`: resolution order item 3, the `.sh` algorithm block, the LLM prompt.

## 2. The existing post-install failure guard is retained, not just the activation tail

`reinstall_local.bat:14-17` and `reinstall_local.sh:15,20-23` hard-fail when the installer
returns non-zero. The rewrite spec preserved only "the existing activate tail", and on
`.sh` the guard structurally *wraps* the invocation line being replaced, so it was easy to
drop — leaving the wrapper to activate a half-built venv and report success. Retention is
now explicit in both wrappers, with the `_SOURCED` form on `.sh`.

Applied in `step_5.md`: both algorithm blocks, a note after them, the LLM prompt.

## 3. Step 3's reference cleanup is defined by a grep, not by an enumeration

Three consecutive review rounds each appended "one more missed reference" to Step 3's
`install.py` lists, and the list was still short by two. The enumerations are demoted to
non-exhaustive examples; the exit criterion is now

```
git grep -n "install\.py\|install_script_path" -- src tests    # must return empty
```

`install_script_path` is in the pattern because it names the retired field and is
invisible to an `install\.py` grep.

Applied in `step_3.md`: WHERE table note, the HOW bullet, the TESTS exit criterion, the
LLM prompt.

## 4. Two previously unowned references added as examples

Both survive the resolver deletion and belonged to no step:

- `workspace.py:554` — `create_startup_script`'s `skip_github_install` Args entry
  ("thread ``--skip-overrides`` into the install.py argv at run time").
- `session_setup.py:115` — "The session spec carrying the resolved
  ``install_script_path``", which only the second grep pattern finds.

## 5. `test_workspace_startup_script_github.py` needs docstring edits, not assertion edits

All six `build_install_argv` call sites (`:54`, `:81`, `:114`, `:144`, `:179`, `:205`)
assert only `"--skip-overrides" in` / `not in` the argv; none names the script path or
`--extras`, so this refactor leaves them valid. The "update the six assertions to the new
form" instruction was removed as unnecessary work. What the file actually needs is its two
`install.py` docstrings updated: `:4` and the class docstring at `:151`.

Applied in `step_3.md` (WHERE row, TESTS bullet, LLM prompt) and `summary.md`'s Modified
table.

## 6. The hard-coded command count is at `test_help.py:66`, not `:38`

`:38` is `assert len(COMMAND_CATEGORIES) == 4` — the category count, unchanged.
`assert len(all_command_names) == 22` is at `:66`. Taken literally the old instruction
edited the wrong assertion. `expected_commands` (`:42-65`) needs no change; it is asserted
as a subset.

Applied in `step_2.md`: WHERE row, the `command_catalog.py` HOW bullet, the LLM prompt.

## 7. Test files mirror their source module

`planning_principles.md` requires it. Renamed and relocated:

| Was | Now | Mirrors |
|---|---|---|
| `tests/install/test_install_config.py` | `tests/install/test_install_env.py` | `install/_env.py` |
| `tests/install/test_install_phases.py` | unchanged | `install/_phases.py` |
| `tests/install/test_install_cli.py` | `tests/cli/commands/test_install.py` | `cli/commands/install.py` |

The `test_<package>_<module>` shape for a private module follows
`tests/llm/providers/langchain/` (`_http.py` → `test_langchain_http.py`). The
parser/dispatch test lands in `tests/cli/commands/` next to `test_init.py`, which already
imports `create_parser` from `cli.main` for the same kind of assertion.

**No conflict with the `.importlinter` change.** Issue #1151's Scope adds `tests.install`
to the `test_module_independence` contract; `tests/install/` still holds two test modules
after the move, so the row stays meaningful, and `tests/cli/commands/test_install.py`
imports only from `mcp_coder.*`, so `tests.cli` / `tests.install` independence is not
touched. No plan adjustment needed.

Applied in `step_2.md` (WHERE table + note, TESTS headings, LLM prompt) and `summary.md`'s
Created table.

## 8. `subprocess_isolation` gets one row, not a pair — and no `tests.install` row

Marcus decided to fix the plan and leave issue #1151 as it is, accepting the mismatch.

The issue's Scope prescribes both `mcp_coder.install -> subprocess` and
`mcp_coder.install.** -> subprocess`, and states: "Both rows are required: `pkg.**` does
not match `pkg` itself, and a bare module name would not cover `_phases` / `_env`." The
plan intentionally overrides that. `ForbiddenContract.unmatched_ignore_imports_alerting`
defaults to `AlertLevel.ERROR`, so an `ignore_imports` row matching no edge in the graph is
a hard contract failure — and under this plan's layout `subprocess` lives in `_env.py`, so
`src/mcp_coder/install/__init__.py` imports it not at all and the bare row can never match.

The existing config confirms the rule "a row only where a real import exists":
`langchain_library_isolation` carries its bare row because
`llm/providers/langchain/__init__.py:545` genuinely imports `langchain_core`, while the
jenkins rows carry only the `.**` half.

Same reasoning kills the `tests.install` row an earlier round asked for, which this decision
supersedes: the ported tests reach subprocess only as a module attribute
(`install.subprocess.run` / `.CalledProcessError` — `tests/tools/test_install_py.py:367,384,398,400,417`)
and never `import subprocess`, so the row would be unmatched and would fail the contract by
itself. Every existing row in that contract names a concrete module, never a package. The
plan therefore records the constraint for whoever ports the tests instead: keep the
attribute-access form, add no bare `import subprocess`.

Unaffected: `tests.install` is still added to the **`test_module_independence`** contract,
as the issue's Scope requires. Different contract.

Applied in `step_2.md` (the `.importlinter` HOW bullet, a TESTS note on the port, the LLM
prompt) and `summary.md` (§7 and the Modified table).

**Round 2 findings — all five accepted, all mechanical; no user decision needed.**

## 9. The install package's module constants live in `_env.py`, not `__init__.py`

`_phases.py` consumes all three: `_phase_install_main` builds the git spec from
`MCP_CODER_REPO`, `_phase_versions` iterates `REPORT_BINARIES` / `REPORT_PACKAGES`. Since
`__init__.py` imports `_phases` to implement `install()`, defining them in `__init__.py`
closes an `__init__ ↔ _phases` cycle — the same hazard the Decision 11/12 note already
handled for `InstallConfig`, which `pycycle` (in Step 2's own gates) would catch. They now
get the identical treatment: defined in `_env.py`, re-exported from `__init__.py`, imported
by `_phases` from `._env`.

Applied in `step_2.md` (WHERE rows, both WHAT blocks, LLM prompt) and `summary.md`'s
Decision 11/12 note, whose reasoning now covers the constants rather than `InstallConfig`
alone.

## 10. Step 5 owns the two `reinstall_local` header comments

`reinstall_local.bat:3` and `.sh:3` say "Delegates to install.{bat,sh} in the same dir" —
the last unowned `install.bat` / `install.sh` references outside `pr_info/`. Step 6 is
doc-only and cannot reach `tools/`, yet its verification demands a clean whole-repo grep;
Step 5's grep matched only `install\.py`. Step 5 now rewrites both headers and greps all
three patterns over `tools/`. Same failure mode round 1 fixed for `src`/`tests`, where the
pattern was widened but Steps 5 and 6 were not.

Applied in `step_5.md` (WHERE rows, a WHAT note, TESTS §2, LLM prompt) and `step_6.md`'s
verification §1, which now says which step owns which tree.

## 11. `run_vulture_check` is added to Steps 2 and 3

CI runs vulture (`ci.yml:197`) in the same PR-only architecture job as tach, lint-imports
and pycycle (`ci.yml:194-197`) — gates both steps already run. Step 2 moves ~570 lines of
never-vulture-scanned code into `src/`; Step 3 deletes two functions. Only Step 5 ran it.

Applied in `summary.md`'s per-step extra-checks list and both steps' LLM prompts.

## 12. Six line citations corrected

`step_2.md` — pylint disable list `:199-212` (was `:212-223`); tach `tests`' `depends_on`
`:470-488` (was `:472-488`, and the issue itself says `:470-488`). `summary.md` — ruff
`ci.yml:103` (was `:104`, the unit-tests row); pycycle `ci.yml:196` (was `:197`, which is
vulture — see #11). `step_3.md` and this file — the six `build_install_argv` assert lines
are `:54`, `:81`, `:114`, `:144`, `:179`, `:205`; four were off by one.

The substantive claims attached to each citation were verified and kept.

## 13. `tests/cli/commands/test_help.py` added to `summary.md`'s Modified table

`step_2.md`'s WHERE table already carried the `== 22` → `23` bump.

**Round 3 findings — six items. Two needed Marcus's call (#14, #15); the rest are
mechanical.**

## 14. `docs/architecture/architecture.md` §5 gains an `install/` subsection

**Marcus's call, made in the round 3 handoff:** "It is **not** in issue #1151's Scope — I am
accepting it deliberately as a bounded Boy Scout fix, since this change creates the
staleness and Step 6 is already the docs step."

§5 "Building Block View" carries one subsection per top-level package (`llm/`, `cli/`,
`icoder/`, `utils/`, `workflows/`). `src/mcp_coder/install/` becomes a new top-level package
with its own tach layer and import-linter row, so the section goes stale the moment Step 2
lands. Bounded to one short subsection matching the length and register of the existing
per-package entries.

Applied in `step_6.md` (WHERE row, a WHAT block with an explicit scope note, LLM prompt) and
`summary.md`'s Modified table.

## 15. One reader of the extras key, not two

Marcus raised this as a preference, conditional on `step_4.md`'s recorded rationale not
being load-bearing. It is not. The rationale read: "`get_install_extras` cannot serve here
because it returns `"dev"` both when the repo declares `"dev"` and when it declares
nothing." That is true only of the `-> str` signature the plan had chosen for it, not of the
key it reads — so it argued against one shape of the function, not against a single reader.

`get_install_extras` now returns `str | None` (`None` == not declared) and the `"dev"`
fallback moves to its one consumer, `InstallConfig.from_args`. Step 4's warn row becomes
`get_install_extras(folder_path) is None`. `install_extras_declared` is dropped: two public
functions reading the same key, with the same lax-load semantics, collapse into one.

Applied in `step_1.md` (WHAT, HOW, ALGORITHM, DATA, TESTS, LLM prompt), `step_2.md`
(`from_args` ALGORITHM, LLM prompt), `step_4.md` (WHERE, WHAT, HOW, ALGORITHM, TESTS, LLM
prompt) and `summary.md` (§6 and the Modified table). Nothing in the issue names
`install_extras_declared`, so its Tests section is unaffected; the mapping lives in the
steps' TESTS sections, which were updated.

## 16. `TestGithubOverridesParser` is deleted, not ported

`step_2.md` TESTS listed it among the classes ported into
`tests/install/test_install_phases.py`, while HOW drops the function it tests — the local
`github_overrides`, replaced by `pyproject_config.get_github_install_config`. Its coverage
already exists against the replacement in
`tests/utils/test_pyproject_config.py::TestGetGithubInstallConfig` (`:11-56`) for four of its
five cases; the two single-field cases (`packages` alone, `packages-no-deps` alone) are
carried over there instead. The `_write_pyproject` helper stays — `TestPhaseOverridesDryRun`
still uses it.

## 17. The argv-level tests get a `Namespace` harness inside `tests/install/`

`_run_install_check` (`tests/tools/test_install_py.py:113-116`) and all of
`TestUseSyncTargetGuard` (`:311-351`) drive `install.main([*argv, "--check"])`, but the plan
drops both `main` and `parse_args`, leaving the only parser in `cli/parsers.py`
(Decision 14). Several `test_install_env.py` bullets are phrased at flag level, so the step
had to name a harness or invite one of two wrong turns: re-adding `parse_args`, or coupling
`tests/install/` to `mcp_coder.cli`.

Chosen: a local `_namespace(**overrides)` helper in each `tests/install/` module, feeding
`InstallConfig.from_args` / `install` directly. This keeps the package's own tests off
`mcp_coder.cli`, matching the split Decision 7 already set — `tests/cli/commands/test_install.py`
is the only module allowed `create_parser()`. It also pins the parser defaults `_namespace`
mirrors there, so the two cannot drift. `TestUseSyncTargetGuard` stops being an argv test
altogether: the guard now raises `ValueError` inside `from_args`.

Applied in `step_2.md` (a TESTS harness note, the `tests/cli/commands/test_install.py`
bullets, LLM prompt).

## 18. `run_ruff_check` added to Steps 1, 3 and 4

`summary.md` states ruff "is not optional" for every step and Step 2's prompt lists it, but
these three did not — though all three change Python under `src/`. Steps 5 and 6 touch no
Python and are left alone. Same shape as #11: a CI gate missing from a step's block, not
per-rule detail.

## 19. Step 5 must preserve the job-local `env:` in the CI block it rewrites

The step names the two comment ranges to rewrite (`ci.yml:136-143`, `:164-171`) but not the
`env: UV_GIT_SHALLOW: "0"` at `:158-160`, which sits between them and is tied by its own
comment to #817 (full clone so setuptools_scm can read sibling tags). There is no
workflow-level `env:`, so it is job-local and a wholesale replacement of `:136-183` would
lose it — precisely when this step adds sibling installs that need it.

Applied in `step_5.md` (a WHAT clause after the CI block, LLM prompt).

**Round 4 findings — three items, all mechanical; two more considered and skipped.**

## 20. The retired `install-env` name is scrubbed from the ported user-facing strings

`prog="install-env"` disappears with `parse_args`, so once the standalone script becomes a
subcommand the name identifies nothing the user can invoke — yet four strings still print
it: the two
`_ensure_system_uv` `sys.exit` messages (`tools/install.py:500`, `:510`), inside a function
Step 2 ports verbatim, and the header and footer prints (`:553`, `:566`), which `install()`
re-creates. No step owned them: Step 3's grep (`install\.py|install_script_path`) and Step
5/6's (`install\.py|install\.bat|install\.sh`) match file names, not the tool name. All
four now say `mcp-coder install`.

Applied in `step_2.md`: a HOW bullet, the LLM prompt.

## 21. The `.sh` rewrite must initialise and unset `MC`

`tools/reinstall_local.sh` is source-able and ends with
`unset _SOURCED _SCRIPT_PATH _SCRIPT_DIR REPO_DIR VENV_BIN` (`:42`). The driver-resolution
block introduces `MC` and the loop variable `p` with neither an initializer nor an unset.
Since `[ -z "$MC" ]` is the only guard, a second `source` in the same shell would reuse the
previous run's `MC`, and both variables would leak into the interactive shell. `MC=""` now
precedes the loop and both names join the closing `unset`. The `.bat` side needs neither —
it already does `set "MC="` and runs inside `setlocal`.

Applied in `step_5.md`: the `.sh` algorithm block, a note after it, the LLM prompt.

## 22. The CI block rewrite preserves one more line

The replacement block drops the `# shellcheck disable=SC1091` comment above
`source .venv/bin/activate` (`ci.yml:180`). No CI job runs shellcheck, so nothing breaks,
but it is the same kind of one-line preservation as #19's job-local `env:` clause — so that
clause was extended to cover it rather than given a paragraph of its own.

Applied in `step_5.md`: the existing preservation clause after the CI block, the LLM prompt.

## Left deliberately untouched

- Per-lint-rule detail (specific ruff/pylint rule codes and their line numbers) was not
  extended anywhere. The per-step verification block runs the gates; that is the right
  level. A CI gate *missing from* a step's block is a different thing — see #11 and #18.
- Line-number citations were not audited or re-verified as a class this round; precise line
  numbers are explicitly not crucial per
  `.claude/knowledge_base/software_engineering_principles.md`.
- `step_3.md:116`'s "module docstring's `install.py` sentence (`:8`)" actually spans
  `:7-9`. Left as-is: the grep exit criterion covers it.
- **Round 4, skipped as speculative:** hardening the `_namespace` default pin to cover the
  whole namespace (`source`, `ref`, `extra_packages` and the five `store_true` flags, or a
  whole-dict comparison). The pin already works in the direction that matters —
  `tests/cli/commands/test_install.py` asserts the parser defaults, so a future parser
  change trips a test that points at `_namespace` — and the three pinned defaults are
  exactly the ones this refactor changes. Per `software_engineering_principles.md`, a change
  that only matters if someone later makes a mistake is speculative.
- **Round 4, skipped as optional:** moving the duplicated `_namespace` helper into
  `tests/install/conftest.py`. Raised as a preference; duplicating a small helper across two
  test modules is unremarkable.
