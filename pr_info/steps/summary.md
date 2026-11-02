# #1311 — Coordinator and vscodeclaude: handle issues with an untrusted body

## Goal

An issue body written by an untrusted user is LLM input with tool access (prompt injection).
Before mcp-coder feeds an issue body to an LLM it must know whether the body is **trusted**:

- author is trusted (`OWNER`, `MEMBER`, `COLLABORATOR`, or `[github] trusted_commenters`), **or**
- the last body editor is the token user or in `trusted_commenters`.

The rule is implemented upstream (mcp-workspace #369). mcp_coder only consumes it.

| Consumer | Untrusted / lookup failed |
|---|---|
| `coordinator run` | Skip the issue, per-repo INFO summary, no comment, no label change |
| `vscodeclaude` launch / restart | Launch a **review-only** session: fixed prompt, no title, no `Branch:` line |
| `vscodeclaude status` | Mark the "Create and start" row |
| `create-plan` | Warn, keep running |

## Upstream names (verified)

mcp-workspace #369, merged as commit 359eea5. Verified against the source and the project `.venv`:

- `IssueManager.check_body_trust(issue: IssueData) -> BodyTrustResult`
- `BodyTrust` enum: `TRUSTED`, `UNTRUSTED`, `LOOKUP_FAILED`
- `BodyTrustResult` (NamedTuple) with `.status: BodyTrust` and `.reason: str`; constructible as
  `BodyTrustResult(status=..., reason=...)`
- All three are re-exported from `mcp_workspace.github_operations.issues`.

## Architectural / design changes

1. **One shared helper, no own types.** `workflow_utils/issue_trust.py::evaluate_body_trust(issue_manager, issue)`
   calls the upstream method and returns the upstream `BodyTrustResult` unchanged. It raises
   only `GitHubRateLimitError` (via `raise_if_rate_limited`). Any other exception becomes
   `LOOKUP_FAILED` with the exception **type name** as reason (no raw text in logs).
   It lives in `workflow_utils` because `cli` and `workflows` both use it, and `workflows` must not import `cli`.
2. **Fail closed, compare by identity.** Callers test `result.status is BodyTrust.TRUSTED`.
   A `MagicMock` result counts as not trusted, so a test that forgets the mock fails loudly.
3. **No caching** of trust results anywhere. Every launch, restart and dispatch does a fresh lookup.
4. **Coordinator gate**: one check per issue inside the dispatch loop of `execute_coordinator_run`,
   after the workflow-label check and before the dispatch `try`. It covers every workflow and both fallback paths.
   Skipped issues are collected and logged once per repo in a `finally` around the loop.
5. **vscodeclaude untrusted mode** is one new spec flag, `SessionSpec.untrusted_body` (last field, default `False`):
   - the launch side computes trust and blanks the title (`display_title = ""`), passing it through the existing `issue_title` parameters;
   - the run side (`session_setup`) picks untrusted banner text and, in `orchestrate`, a single `claude` call with a fixed prompt.
     Order: intervention → no commands → untrusted → normal.
6. **Trust computed before side effects**: before `create_working_folder` in `prepare_and_launch_session`,
   and before the first write in `regenerate_session_files`. A rate limit leaves no folder and no half-written files.
   `prepare_and_launch_session` takes a **required** `issue_manager`.
7. **Status table stays GitHub-free**: the command computes `untrusted_keys` with
   `issues.find_untrusted_launch_keys(...)` (after the `--explain` return) and passes the set to
   `display_status_table`, the same way `issues_without_branch` is passed.
8. **Docs, one source of truth**: a new "Issue body trust" section in `docs/repository-setup/github.md`
   holds every limitation. Other docs get short behaviour lines plus a link.

## KISS choices

- No mcp_coder result type or enum; the upstream ones are used directly.
- Existing `issue_title` parameters are kept; callers pass the blanked title. The only new parameter on the writers is `untrusted_body`.
- Untrusted templates are separate constants, so the trusted templates stay byte-identical.
- The untrusted `orchestrate` branch reuses `build_claude_argv(spec, prompt=...)`.
- The intervention rate-limit handling wraps the single call site, using the existing `_rate_limit_or_raise` pattern.
- Existing tests are kept green with autouse "trusted" fixtures in `conftest.py`, not by editing every test.
- New tests go in new files (file-size gate).

## Files

### Created
- `src/mcp_coder/workflow_utils/issue_trust.py`
- `tests/workflow_utils/test_issue_trust.py`
- `tests/cli/commands/coordinator/conftest.py`
- `tests/cli/commands/coordinator/test_commands_trust_gate.py`
- `tests/cli/commands/coordinator/test_vscodeclaude_trust.py`
- `tests/workflows/vscodeclaude/test_session_setup_untrusted.py`
- `tests/workflows/vscodeclaude/test_workspace_untrusted.py`
- `tests/workflows/vscodeclaude/test_session_launch_trust.py`
- `tests/workflows/vscodeclaude/test_status_untrusted.py`
- `tests/workflows/create_plan/test_prerequisites_trust.py`

### Modified
- `pyproject.toml` (minimum `mcp-workspace` version)
- `src/mcp_coder/mcp_workspace_github.py`, `tests/test_mcp_workspace_github_exports.py`, `vulture_whitelist.py`
- `src/mcp_coder/cli/commands/coordinator/commands.py`
- `src/mcp_coder/cli/commands/coordinator/commands_vscodeclaude.py`
- `src/mcp_coder/workflows/vscodeclaude/types.py` (`SessionSpec`)
- `src/mcp_coder/workflows/vscodeclaude/templates.py`
- `src/mcp_coder/workflows/vscodeclaude/session_setup.py` (`render_banner`, `orchestrate`)
- `src/mcp_coder/workflows/vscodeclaude/workspace.py` (`create_startup_script`, `create_status_file`)
- `src/mcp_coder/workflows/vscodeclaude/session_launch.py` (`prepare_and_launch_session`, `process_eligible_issues`, `regenerate_session_files`)
- `src/mcp_coder/workflows/vscodeclaude/issues.py` (`find_untrusted_launch_keys`)
- `src/mcp_coder/workflows/vscodeclaude/status.py` (`display_status_table`)
- `src/mcp_coder/workflows/create_plan/prerequisites.py` (`check_prerequisites`)
- `tests/workflows/vscodeclaude/conftest.py` (autouse trusted fixture)
- existing tests calling `prepare_and_launch_session` (new `issue_manager=` argument)
- `docs/repository-setup/github.md`, `docs/coordinator-vscodeclaude.md`, `docs/cli-reference.md`,
  `docs/configuration/config.md`, `SECURITY.md`

## Steps

1. Upstream integration + shared helper
2. Coordinator gate
3. Session spec, templates, run-time (`session_setup`)
4. Launch-time writers (`workspace.py`)
5. Launch / restart / intervention wiring
6. Status table marker
7. `create-plan` warning
8. Documentation
