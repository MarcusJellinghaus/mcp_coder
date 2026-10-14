# Enable ruff `C4` and `B` (issue #1165)

## Goal

Enable the `C4` (flake8-comprehensions) and `B` (flake8-bugbear) ruff rule
groups in `pyproject.toml`, and fix all 22 current findings with real code
changes — no blanket suppression.

**Known deviation, requires sign-off before merge:** 3 of the 22 findings
(`B009` ×2 in step 5, `B010` ×1 in step 6) are resolved via a scoped
`# noqa`, not a real code fix — a rewrite would trip mypy's
`no-implicit-reexport` check or the `subprocess_isolation` import-linter
contract. This conflicts with issue #1165's acceptance criterion "All 22
findings fixed, not suppressed." Flagged here rather than suppressed
silently — confirm with the issue owner before landing steps 5 and 6, or
find an alternative fix that satisfies both the lint rule and the existing
mypy/import-linter contracts.

## Architectural / design changes

**None.** This is a lint-hygiene change: every fix is a local, behavior-preserving
rewrite (dict-call → literal, comprehension → `dict.fromkeys`, explicit `zip`
`strict=`, dot-attribute access instead of `getattr`/`setattr`, narrower
`pytest.raises` type, an unused loop variable renamed to `_`). No new module,
class, public function, or dependency is introduced. The only non-test file
touched is `src/mcp_coder/cli/commands/coordinator/issue_stats.py`, and that
change is a one-line rename with no behavior change (confirmed: the unused
`label_name` binding doesn't hide a bug — see step 9).

Per-rule decisions that need to be read before implementing, not re-derived:

- **`B905` (`zip()` without `strict=`)** — judged per call site, not blanket.
  Four sites build both zip operands from the same source/length by
  construction (or assert equal length first) → `strict=True`. One site pairs
  a fixed-length name list with a variable-length `args` tuple by design
  (building a merged args/kwargs dict) and one site is the classic
  `zip(xs, xs[1:])` pairwise-consecutive pattern (lengths differ by one by
  design) → both get `strict=False`. See step 4 for the exact mapping.
- **`B009`/`B010` (`getattr`/`setattr` with a constant)** — fixed to dot-access
  where that's a safe, equivalent rewrite. Two `B009` sites
  (`tests/install/test_install_phases.py`) keep `getattr`, with a scoped
  `# noqa: B009` added to the existing documented rationale (dot-access there
  would trip mypy's `no-implicit-reexport` and the `subprocess_isolation`
  import-linter contract) — the same documented-exception pattern already
  used elsewhere in this repo (e.g. `BLE001`, `SIM115`). The one `B010` site
  already carries a `# noqa: B010` with a documented rationale, but on the
  wrong physical line (ruff reports multi-line calls on the opening line), so
  it silently never applied — step 6 repositions it; it does not rewrite the
  `setattr` call.
- **`B007` (`issue_stats.py:266`)** — checked for a hidden bug per the issue's
  acceptance criterion. Conclusion: `label_name` is genuinely unused in that
  loop body (it only sums `len(issues_list)`); no bug. Rename to `_`.

## Order of work

The rule groups are enabled **last** (step 10), once every finding is already
fixed in the code. Every earlier step's commit therefore passes the *current*
ruff config unchanged; step 10 is the only commit that changes
`[tool.ruff.lint] select` and is expected to flip `C4`/`B` from unchecked to
fully green in the same commit.

## Steps

1. `C408` — unnecessary `dict()` calls → literal dicts (2 test files)
2. `C420` — dict comprehension over an iterable → `dict.fromkeys` (3 test files)
3. `C414` — unnecessary `reversed()` inside `set()` (1 test file)
4. `B905` — explicit `zip()` `strict=` per call site (4 test files)
5. `B009` — `getattr` with a constant attribute (3 test files)
6. `B010` — `setattr` with a constant attribute: reposition the existing `noqa` (1 test file)
7. `B011` — `assert False` → `raise AssertionError(...)` (1 test file)
8. `B017` — narrow `pytest.raises(Exception)` to the real exception type (1 test file)
9. `B007` — unused loop variable in `issue_stats.py`, confirmed not a bug (1 src file)
10. Enable `C4` and `B` in `pyproject.toml`; full verification

## Files touched

- `pyproject.toml`
- `src/mcp_coder/cli/commands/coordinator/issue_stats.py`
- `tests/cli/commands/test_check_branch_status_pr_waiting.py`
- `tests/workflows/review/test_reviewer.py`
- `tests/cli/test_help_anti_drift.py`
- `tests/llm/providers/langchain/test_langchain_diagnostics.py`
- `tests/llm/providers/langchain/test_langchain_http.py`
- `tests/workflows/rebase/test_llm_steps.py`
- `tests/llm/providers/claude/test_claude_code_cli.py`
- `tests/llm/providers/langchain/test_mcp_health_check.py`
- `tests/llm/test_interface.py`
- `tests/workflows/review/test_prototype_session_interleave.py`
- `tests/icoder/test_cli_icoder_parser.py`
- `tests/install/test_install_phases.py`
- `tests/llm/test_types.py`
- `tests/llm/session/test_resolver.py`
- `tests/icoder/test_log_inventory.py`

No folders, modules, or files are created or deleted — all changes are edits
to existing files.

## Verification used by every step

```
mcp__mcp-tools-py__run_format_code
mcp__mcp-tools-py__run_ruff_check   (plus a targeted select=[rule_id] check for the step's rule)
mcp__mcp-tools-py__run_pylint_check
mcp__mcp-tools-py__run_pytest_check  (extra_args=["-n","auto", unit-test marker filter from CLAUDE.md])
mcp__mcp-tools-py__run_mypy_check
```

Out of scope here. Enabling `I` (isort) is tracked separately as issue
#1174. Propagating `C4`/`B` to the `mcp-tools-py` and `mcp-workspace` repos
is a *different* out-of-scope item — #1174 does not cover it. Per epic
#1163, that propagation is handled by the epic's separate Chore Propagation
process, not by a specific issue number; flagging it here so the work isn't
dropped for lack of an owner.
