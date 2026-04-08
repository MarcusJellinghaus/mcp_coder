# Plan Decisions — Issue #725

Log of decisions made during plan review round 1 (2026-04-08).

## Design decisions (from user)

1. **Deploy failure behavior** — `_find_claude_source_dir()` exits 1 with a **detailed** error message: what was sought (packaged Claude resources), every path tried (importlib.resources path + each ancestor checked), and a remediation hint (`pip install --force-reinstall mcp-coder`). Tests assert the message contains these elements. (Applied in step 3.)

2. **Self-deploy detection** — Before deploying, `execute_init()` resolves source and target paths and compares them. If `source_dir.resolve() == target_base.resolve()`, skip deploy silently with a single info log line (`"Skipping deploy: running inside mcp-coder source repo"`). Prevents warning spam when `mcp-coder init` is run inside the mcp-coder source repo. Test case added. (Applied in step 4.)

3. **Missing `--project-dir` path** — `execute_init()` validates the `--project-dir` path EARLY (before deploy and config creation). If the path does not exist, exit 1 with a clear error (`"Project directory does not exist: <path>"`). Test case added. (Applied in step 4.)

4. **setup.py test strategy** — Keep three unit tests that load `setup.py` via `importlib.util.spec_from_file_location` to exercise `_copy_claude_resources()` directly. **Also add** one slow integration test that runs `python -m build --wheel` against a tmp copy of the repo and inspects the resulting wheel (via `zipfile`) to confirm `resources/claude/skills/`, `resources/claude/knowledge_base/`, and `resources/claude/commands/` files are present inside it. Marked slow so it is excluded from fast unit runs. (Applied in step 1.)

5. **MANIFEST.in** — Do NOT add MANIFEST.in. The wheel integration test is the authoritative check and will catch any packaging miss. (Applied in step 1.)

## Straightforward fixes

6. **Step 1 imports** — Added `import shutil` and `from pathlib import Path` to the `setup.py` skeleton.

7. **Step 2 unused-argument** — After renaming `_args` → `args` in `execute_init()`, add a harmless no-op reference (`_ = (args.just_skills, args.project_dir)`) to avoid `unused-argument` pylint errors in the intermediate step-2 commit. Step 4 replaces it with real usage. Chose the no-op access over `# pylint: disable=unused-argument`.

8. **Step 3 importlib.resources pattern** — Mirror `src/mcp_coder/utils/data_files.py` precisely. Explicit `from importlib.resources import files` added to the imports shown.

9. **Step 3 contradiction** — Removed the "at most 3 levels" note. Uses unbounded `.parents` walk for the editable-install fallback.

10. **Step 3 DEPLOY_SUBDIRS exercising** — Keep the constant defined in step 3. Validate that **all three** subdirs exist under the resolved source (not just `skills/`), which exercises the constant in the same step it is introduced.

11. **Step 4 duplicate test** — Kept `TestExecuteInitWithDeploy::test_deploy_failure_exits_1` and added a rationale comment marking it as an integration smoke test complementing step 3's unit tests for `_find_claude_source_dir`.
