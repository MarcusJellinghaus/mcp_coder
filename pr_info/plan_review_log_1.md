# Plan Review Log — Issue #993

**Issue:** verify: add `_LABEL_MAP` entry for the `network_proxy` GitHub check
**Branch:** 993-verify-add-label-map-entry-for-the-network-proxy-github-check
**Supervisor run:** 1

## Round 1 — 2026-07-02

**Findings** (from `/plan_review` engineer):
- All of the plan's factual claims about the current code hold: `_LABEL_MAP` has `api_base_url` and no `network_proxy` entry; `_format_section` uses `_LABEL_MAP.get(key, key)` over `result.items()` skipping `overall_ok`; `_GITHUB_KEYS` + `test_all_github_keys_in_label_map` (stale "9" count) and `test_format_section_renders_github_labels` exist; key names match.
- Dependency claim verified true for the project `.venv` (`mcp-workspace 0.1.13.dev8` emits `network_proxy`). NIT: the Jenkins tool env is on `dev7` which lacks it — unit tests are self-contained and unaffected, but manual `mcp-coder verify` acceptance must run against the project venv.
- [NIT] The render test uses `ok=False` for `network_proxy` but did not assert the `[ERR]` marker the issue rationale documents as expected for a failed probe.
- No blockers; step sizing (one step = one commit, TDD) and scope are compliant.

**Decisions**:
- Accept the `[ERR]` assertion NIT — it locks in a decision the issue explicitly documents. Applied via plan edit.
- Skip/note the version-skew NIT — informational only, not a plan defect, no scope/architecture impact.

**User decisions**: none required (no design/requirements questions).

**Changes**: `pr_info/steps/step_1.md` — added `assert "[ERR]" in output` to the `test_format_section_renders_github_labels` extension (item 3) and mirrored it in the LLM prompt section for consistency.

**Status**: plan changed — committing; loop continues with a fresh review round.

## Round 2 — 2026-07-02

**Findings** (from `/plan_review` engineer):
- Re-validated all factual claims against current source — all still hold. The newly added `assert "[ERR]" in output` is consistent: sample `network_proxy` has `ok=False` → `_format_section` renders `[ERR]`, while the two `ok=True` rows still produce `[OK]`.
- [NIT] `step_1.md` "Verification" and "Definition of done" referenced `mcp__tools-py__run_*` (missing the `mcp-` prefix) and `./tools/format_all.sh`, which do not match `.claude/CLAUDE.md`.
- No blockers; plan otherwise ready for approval.

**Decisions**:
- Accept the tool-reference NIT — wrong tool names would misdirect the implementing LLM. Applied via plan edit.

**User decisions**: none required.

**Changes**: `pr_info/steps/step_1.md` — corrected tool references to `mcp__mcp-tools-py__run_pylint_check` / `run_pytest_check` / `run_mypy_check`, and replaced `./tools/format_all.sh` with `mcp__mcp-tools-py__run_format_code` (in Verification, Definition of done, and LLM prompt).

**Status**: plan changed — committing; loop continues with round 3.
