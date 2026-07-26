# Plan Review Log — Run 2

Issue: #1085 — `mcp-coder rebase`: execute git in Python, LLM only for conflict resolution; add CLI progress output
Branch: 1085-mcp-coder-rebase-execute-git-in-python-llm-only-for-conflict-resolution-add-cli-progress-output
Date: 2026-07-26
Reviewer: plan_review_supervisor

Note: branch is behind origin/main by one docs-only commit (5357e07, `.claude/CLAUDE.md`, forbids AskUserQuestion tool); review proceeds since it cannot affect the plan. Run 1 (rounds 1–2) already applied and committed 11 decisions — see `pr_info/plan_review_log_1.md` and `pr_info/steps/Decisions.md`.

## Round 1 — 2026-07-26

**Findings** (fresh engineer, full re-verification incl. library sources):
- Round-1/2 edit consistency check: PASS — all 11 prior decisions correctly and consistently applied; all codebase/library claims re-verified (pytest crash dict, `error_info` semantics, permissions list, `LLM_INACTIVITY_TIMEOUT_SECONDS`, `session_id` support, import-linter contract, SKILL.md abort rules).
1. CRITICAL — step_2/summary: collector outcome `skipped` (module-level `pytest.importorskip` / `pytest.skip(allow_module_level=True)`) keyed as failure via `c.outcome != "passed"`; a new self-skipping module from base becomes a phantom regression → 2 futile fix attempts → reset + exit 1. Evidence: `pytest_jsonreport` serializes collector outcome verbatim; `mcp-tools-py` parsers.py:100-102 passes it through; in-repo instance `tests/llm/providers/langchain/test_langchain_models.py:42`.
2. IMPROVEMENT — step_6: first OUTPUT line sits after guards/no-op short-circuit, so the everyday up-to-date run prints nothing at OUTPUT level (partially reproduces issue defect 1).
3. COSMETIC — step_2: DATA contract says `CheckRunError` names the failing checker, but the extractor-raised path re-raises bare.
4. COSMETIC — step_2/summary: "line numbers never enter the key" not fully achievable for messages embedding line refs in text (mypy "already defined on line N", pylint R0801) — known limitation, bounded by 2-attempt cap.

**Decisions**: accept all 4 at triage (1 = factual correction extending settled decisions 1+4; 2 = direct issue-requirement fix; 3–4 mechanical clarity). No user escalation.

**User decisions**: none needed.

**Changes** (applied via /plan_update):
- step_2.md: collectors keyed only on outcome `"failed"` (skipped collectors excluded like skipped tests) + rationale + TDD case (skipped collector → no key); `_run_all_checks` wraps extractor-raised `CheckRunError` with the checker name; known-limitation note on line numbers embedded in message text.
- step_6.md: first OUTPUT line ("Starting automated rebase...") before any guard; no-op branch upgraded to OUTPUT ("Already current with origin/<base>; nothing to do"); TDD case 10 extended to assert the no-op OUTPUT line.
- summary.md: baseline-key bullets aligned ("plus failed collectors; skipped collectors excluded like skipped tests") + known-limitation parenthetical.
- Decisions.md: "## Round 3" section appended with decisions 12–15.

**Status**: committed
