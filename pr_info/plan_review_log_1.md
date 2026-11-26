# review-plan review log 1

## Round 1 — 2026-11-26
**Findings**:
Reviewing the plan for #1444. Next I'm checking the tach and import-linter config, plus the verify.py code the plan touches.Checking tests that depend on when `resolve_mcp_config_path` and `prepare_llm_environment` run, since step 4 moves those calls earlier.Checking `_format_section`'s special cases, since step 2 removes the `token_configured` hint and the Jenkins section may still rely on it.Checking file sizes, since step 4 adds code to `verify.py` and `verify_sections.py`.`pr_info/steps/step_2.md:45` — low — The plan keeps `verify_github_security` exported from `mcp_coder/mcp_workspace_github.py`. After step 2 nothing in `src` uses it, because its only caller (`verify_sections._print_github_security_section`) is deleted and the conftest patch moves to `github_security_rows`. That leaves a dead re-export, which goes against "clean deletion, no legacy artifacts". Drop it from the shim import and `__all__` in step 2.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md (around line 45), add an instruction to remove `verify_github_security` from the import and from `__all__` in `src/mcp_coder/mcp_workspace_github.py`. After step 2 nothing in src uses it: its only caller, `verify_sections._print_github_security_section`, is deleted, and the conftest patch moves to `github_security_rows`. Also have step 2 check that no test or patch target still points to `mcp_workspace_github.verify_github_security`.'], escalate_reason=None)
**Changes**:
applied
