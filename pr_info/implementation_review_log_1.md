# Implementation Review Log — Issue #725

**Feature:** Deploy Claude skills via `mcp-coder init`
**Branch:** 725-deploy-claude-skills-via-mcp-coder-init
**Started:** 2026-04-08

## Round 1 — 2026-04-08

**Findings:**
- S1 — `_find_claude_source_dir` doesn't catch `ModuleNotFoundError` from `files("mcp_coder")`
- S2 — `Path(str(files(...)))` lossy for zip-based installs
- S3 — Fallback walk matches any ancestor with `.claude/{skills,knowledge_base,agents}` (foreign-editable-install trap)
- S4 — Dead `monkeypatch.setattr` on `Path.__file__` in `test_falls_back_to_repo_root`
- S5 — `(_ for _ in ()).throw(SystemExit(1))` readability issue in `test_deploy_failure_exits_1`
- S6 — Per-file skip warnings could be demoted to DEBUG
- S7 — `setup.py` `_copy_claude_resources` doesn't remove stale files before copying
- S8 — `# type: ignore[misc]` without explanation in `setup.py`

**Decisions:**
- S1: SKIP — speculative; CLI only runs if the package imports
- S2: SKIP — reviewer notes "will not bite in practice"; speculative
- S3: ACCEPT — real UX bug (silent no-op in foreign editable install), bounded fix via repo marker anchor
- S4: ACCEPT — trivial dead-code cleanup
- S5: ACCEPT — trivial readability fix
- S6: SKIP — conflicts with explicit spec decision #9 ("per-file warnings on skips only")
- S7: ACCEPT — real issue for iterative local builds, bounded fix
- S8: SKIP — cosmetic

**Changes:**
- `src/mcp_coder/cli/commands/init.py` — fallback walk now requires `<ancestor>/src/mcp_coder/__init__.py` marker (S3)
- `tests/cli/commands/test_init.py` — removed dead `Path.__file__` monkeypatch; replaced generator-throw with `_raise_system_exit` helper; added foreign-project marker test; updated `test_falls_back_to_repo_root` to include `src/mcp_coder/__init__.py` in tmp layout; extended stale-file test to assert removal (S3, S4, S5, S7)
- `setup.py` — `_copy_claude_resources` now `shutil.rmtree`s destination before copying (S7)

**Status:** committed (below)

## Round 2 — 2026-04-08

**Findings:** None. Round 2 reviewer verified S3/S4/S5/S7 fixes are correct, tightly scoped, and well-tested. No new concrete concerns.
**Decisions:** n/a
**Changes:** none
**Status:** no changes needed

## Final Status

- **Rounds run:** 2
- **Round 1:** 8 findings → 4 accepted (S3, S4, S5, S7), 4 skipped (S1, S2, S6, S8). Fixes committed as `164119d`.
- **Round 2:** zero findings, zero changes — loop terminates cleanly.
- **Branch status:** CI passed, up-to-date with main, ready to merge.
