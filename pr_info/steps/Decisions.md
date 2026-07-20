# Plan Decisions

Decisions applied to the `pr_info/steps/` plan after the plan review of issue #1041,
triaged and accepted by the technical lead (2026-07-20). Skipped findings are recorded
for traceability.

## Applied

- **C1 — parse-only `matches()` invariant (Step 2).** Added a test asserting a `Matcher`
  carrying an `ArgPredicate` still matches the bare `mcp__server__tool` name; `matches()`
  never evaluates args in M2.
- **C2 — `matched_rule is None` on frame-sourced decisions (Step 4).** Added explicit
  `matched_rule is None` assertions to the frame tests (models A/B/C declared, frame
  `deny`, frame `allow` elevation) to lock the biconditional
  (`matched_rule is None` iff `source in {default, frame, degraded}`).
- **S1 — primary-key ranking test (Step 2).** Added a test asserting an exact-tool matcher
  on server A outranks a server-wildcard matcher on the same server A (the §8.3 manager
  case).
- **S2 — keep `model.py` pure-data (Steps 1 & 3).** Moved the `default_policy None -> ALWAYS`
  semantic note out of the model comment; the mapping is documented as resolver-only
  (Step 3).
- **S3 — canonical marker set (all steps).** Updated each step's pytest CHECKS / LLM-PROMPT
  to cite the full canonical fast-unit marker-exclusion set from `.claude/CLAUDE.md`
  (git_integration, claude_cli_integration, claude_api_integration, copilot_cli_integration,
  formatter_integration, github_integration, jenkins_integration, langchain_integration,
  llm_integration, textual_integration) with `-n auto`.
- **S4 — deterministic `__init__` exports (Step 2).** Removed the "(optional)" hedge:
  `parse_matcher` is exported from the package `__init__` (needed by I2.2/I2.4);
  `specificity`/`matches` stay module-internal.
- **S5 — vulture green at Step-3 commit (Step 3).** Noted the Step-3 commit must leave
  `run_vulture_check` green; the unread `frame` param is whitelisted in
  `vulture_whitelist.py` alongside `args` if vulture flags it.
- **S6 — `Degraded.layer` stays None in I2.1 (Step 1).** Documented that the field is
  unfillable by the pure resolver and is populated later by I2.2, so it is not mistaken
  for a bug.
- **Q3 — degrade masks base for `lifted_never` (Step 4).** Added a test row plus a code
  comment: under a degraded config a frame `allow` over a would-be-`never` tool reports
  `lifted_never is None`.

## Skipped (recorded for awareness; not applied)

- **S7** — keep the explicit `permissions_leaf_isolation` import-linter contract as-is
  (redundant third-party entries retained).
- **Q1** — `Decision.lifted_never` stays `Policy | None`.
- **Q2** — no ask->always frame-elevation signal added here (out of scope; I4.3).
- **Q4** — no dependency / `pyproject.toml` / config changes (confirmed correct).
