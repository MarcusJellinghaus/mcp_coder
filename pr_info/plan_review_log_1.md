# Plan Review Log 1 — Issue #926

**Branch**: 926-feat-icoder-show-mcp-coder-utils-version-on-startup
**Date started**: 2026-04-28

## Round 1 — 2026-04-28

**Findings**:
- Step 2 banner test target was wishy-washy ("if X exists extend, otherwise add new")
- Step 1 commit message did not flag the side-effect that mcp-coder lookup also becomes graceful via the new helper
- Step 1 fixture conflict (helper tests must live outside `_mock_externals` scope) — already handled in plan
- Step 3 import-removal lint guarantee — pylint/ruff cannot validate removal; tests are the real guard (already covered)
- Test rename to `test_info_shows_versions` (plural) — already in plan
- `RuntimeInfo` field-ordering change — safe, kwargs-only callers
- Absence of a final "verify everything" step — correctly absent per planning principles

**Decisions**:
- Accept (fix): commit step 2 to a single concrete test path
- Accept (fix): add a one-line reviewer note in step 1 about graceful mcp-coder lookup
- Skip (already correct): items 3-7 above need no change

**User decisions**: none — no design or requirements questions raised this round

**Changes**:
- `pr_info/steps/step_2.md`: removed conditional language; committed to `tests/icoder/ui/test_app.py` with a concrete test function `test_banner_renders_mcp_coder_utils_version`. Evidence: grep of `tests/icoder/**/*.py` for `mcp-coder|mcp_coder_version|banner` showed no existing banner assertion; `test_app.py` mirrors src structure for `src/mcp_coder/icoder/ui/app.py`.
- `pr_info/steps/step_1.md`: appended one-line reviewer note that routing `mcp-coder` through `_get_package_version` makes its lookup graceful (previously raised `PackageNotFoundError`).

**Status**: committed

## Round 2 — 2026-04-28

**Findings**:
- Round 1 fixes (step_1 graceful-mcp-coder note + step_2 concrete test path) verified coherent and correct
- Step 2's new test relied on `make_icoder_app` providing a populated `runtime_info`, but the factory builds `AppCore(llm_service=llm, event_log=event_log)` with no `runtime_info`, and `on_mount` gates the banner block on `if self._core.runtime_info:` — so the test would silently emit zero banner lines and the assertion would fail
- Step 2 still hedged: "If `make_icoder_app` does not already provide a `RuntimeInfo`…, extend the factory" — needed to commit to the extension explicitly

**Decisions**:
- Accept (fix): make the `make_icoder_app` factory extension concrete, not conditional; spell out the new optional `runtime_info` kwarg and update the test snippet to pass a fully populated `RuntimeInfo`

**User decisions**: none — straightforward correctness fix, no design question

**Changes**:
- `pr_info/steps/step_2.md`: replaced hedged "If…" language with two concrete sub-sections — (1) extend `make_icoder_app` to accept `runtime_info: RuntimeInfo | None = None` and pass it through to `AppCore` (default `None` keeps existing tests intact), (2) the new test constructs the full post-Step-1 `RuntimeInfo` (all 9 fields) and passes it via `runtime_info=`. Added a "Files modified" section noting both `app.py` and `test_app.py` are touched.

**Status**: committed
