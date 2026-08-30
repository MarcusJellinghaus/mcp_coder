# Step 2 — Linked-branch state feeds `_exit_code`

**Read [summary.md](./summary.md) first** — in particular "Architectural / design changes"
(why two terms and not one, why ungated) and "Dependency — blocked on upstream merge".

One commit: tests + implementation + docs, all three checks passing.

## Precondition — verify before writing any code

**This step does not compile until mcp-workspace #268 is merged to `main`.**

1. Confirm `LinkedBranchStatus` and `linked_branch_blocks` exist on mcp-workspace `main`.
2. Reinstall mcp-workspace (unpinned git dep off the default branch — no `pyproject.toml`
   change).
3. Confirm the import resolves:
   ```python
   from mcp_workspace.checks.branch_status_rendering import (
       LinkedBranchStatus,
       linked_branch_blocks,
   )
   ```
4. Re-confirm `linked_branch_blocks` still returns
   `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`.

If any of these fail, **stop** and report that the upstream dependency has not landed. Do
not stub, vendor, or locally re-implement the upstream names.

> **Precondition re-checked 2026-08-30 — still blocked.** `origin/main` of mcp-workspace
> (head `b9106c4`, last `checks` commit `a1f0eac` / #244) contains no `LinkedBranchStatus`
> and no `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree returns 0
> matches, and the installed package exports neither name. Branch
> `origin/268-check-branch-status-verify-the-issue-s-linked-branch-matches-the-current-branch`
> still exists unmerged. Reinstalling would not help — the names are absent from `main`
> itself. No code written.
>
> **Re-checked again after `git fetch` (same day) — unchanged.** `origin/main` is still
> `b9106c4`; `origin/268-...` is still unmerged and has advanced `1ccb198` -> `7d5e348`.
> The upstream API on that branch is **unchanged in shape** at `7d5e348`: `LinkedBranchStatus`
> still has the same six members and `linked_branch_blocks` still returns
> `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`, so sections 2a-2d
> below remain accurate as written and need no revision. Still no code written.
>
> **Third re-check after `git fetch` — still blocked.** `origin/main` of mcp-workspace is
> *still* `b9106c4` ("chore(pyproject): drop unused config extra (#275)"); `git branch -r
> --merged origin/main` lists only `origin/main` and `origin/HEAD`, so
> `origin/268-...` is **not** merged. That branch has advanced again (`7d5e348` ->
> `eb9fe9f`, pr_info bookkeeping commits only). Checked this time against the **`origin/main`
> blob itself**, not the reference working tree (whose HEAD `1c181ea` is not `origin/main`):
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT`, `class CIStatus` and `pr_feedback_undeterminable`, but **zero**
> occurrences of `LinkedBranchStatus` or `linked_branch_blocks`. The installed
> `mcp_workspace.checks.branch_status_rendering` likewise exports neither name (it exports
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). Reinstalling
> remains pointless for *this* step — the names are absent from `main` itself, not merely
> stale locally. Sections 2a-2d still need no revision. No code written.
>
> **Side finding — the environment's mcp-workspace is badly stale and the pre-existing
> baseline is red.** This is **not** a regression from this branch (nothing here touches
> Python) and fixing it will **not** unblock step 2, but it must be cleared before step 2
> can be verified:
>
> - **pytest: mass collection failure.** ~20 collectors abort with
>   `ModuleNotFoundError: No module named 'mcp_workspace.checks.branch_status_rendering'`,
>   raised from the *existing* `src/mcp_coder/checks/branch_status.py:17` import of
>   `GITHUB_TOKEN_HINT, CIStatus`. Because `src/mcp_coder/__init__.py:37` imports
>   `collect_branch_status`, this poisons nearly every test module, not just the
>   branch-status ones. The venv's mcp-workspace predates the
>   `checks/branch_status_rendering` module altogether.
> - **mypy: 9 errors**, including `import-not-found` on the same module,
>   `"BranchStatusReport" has no attribute "pr_feedback_undeterminable"`
>   (`check_branch_status.py:154`, `workflows/review/core.py:139`) and two
>   `Unexpected keyword argument "fail_on_reviews"` for `format_for_llm`/`format_for_human`.
>   All three names **do** exist on `origin/main`.
> - **pylint: `E0401`** on the same import (alongside unrelated pre-existing `langchain`/
>   `httpx` import errors).
>
> Note the interpreters disagree: the MCP tooling process resolves
> `mcp_workspace.checks.branch_status_rendering` (its copy has `GITHUB_TOKEN_HINT`,
> `CIStatus`, `TaskTrackerStatus`, `WaitContext`, `format_report_for_human`,
> `format_report_for_llm`, `truncate_ci_details` — still no `LinkedBranchStatus`), while the
> project venv used by pytest/mypy/pylint has no such module at all. A reinstall off `main`
> should clear all three baselines. Not done here — it mutates the environment and is out of
> scope for a step whose instruction is stop-and-report.
>
> **Fourth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved.**
> `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop unused config
> extra (#275)") and `git branch -r --merged origin/main` still lists only `origin/main` and
> `origin/HEAD`, so `origin/268-...` remains **unmerged** (its head has advanced `eb9fe9f`,
> pr_info bookkeeping only). `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py`
> matches `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of
> `LinkedBranchStatus` or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree
> still returns 0 matches, and the module the MCP tooling process resolves still exports
> neither name. The side finding above is **unchanged**: a targeted pytest run on
> `tests/checks/test_branch_status.py` + `tests/cli/commands/test_check_branch_status_exit_code.py`
> still aborts at conftest import with `src/mcp_coder/checks/branch_status.py:17` failing to
> import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still stale.
> Sections 2a-2d need no revision. No code written.
>
> **Fifth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved.**
> `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop unused config
> extra (#275)") and `git branch -r --merged origin/main` still lists only `origin/main` and
> `origin/HEAD`, so `origin/268-...` remains **unmerged** (head unchanged at `eb9fe9f`).
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at conftest
> import, via `src/mcp_coder/__init__.py:37` -> `src/mcp_coder/checks/branch_status.py:17`
> failing to import from `mcp_workspace.checks.branch_status_rendering`. Sections 2a-2d need
> no revision. No code written.
>
> **Sixth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved since
> the fifth.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop
> unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `eb9fe9f` ("docs(pr_info): document CI isort fix in task tracker").
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at conftest
> import, via `src/mcp_coder/__init__.py:37` -> `src/mcp_coder/checks/branch_status.py:17`
> failing to import from `mcp_workspace.checks.branch_status_rendering`. Sections 2a-2d need
> no revision. No code written.
>
> **Seventh re-check after `git fetch` (2026-08-30) — still blocked.** `origin/main` of
> mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop unused config extra (#275)")
> and `git branch -r --merged origin/main` still lists only `origin/main` and `origin/HEAD`,
> so `origin/268-...` remains **unmerged**; its head has advanced `eb9fe9f` -> `1626fec`
> ("docs(pr_info): add round 2 implementation review log", docs only).
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The upstream
> API on branch `268-...` is **still unchanged in shape** at `1626fec`: `LinkedBranchStatus`
> has the same six members and `linked_branch_blocks` still returns
> `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`, so sections 2a-2d
> need no revision. No code written.
>
> **Eighth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved since
> the seventh.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop
> unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `1626fec` ("docs(pr_info): add round 2 implementation review log").
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The upstream
> API on branch `268-...` is **still unchanged in shape** at `1626fec`: `LinkedBranchStatus`
> has the same six members and `linked_branch_blocks` still returns
> `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`, so sections 2a-2d
> need no revision. The side finding above is **unchanged**: a targeted pytest run on
> `tests/checks/test_branch_status.py` +
> `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at
> `tests/cli/commands/conftest.py:10` -> `src/mcp_coder/__init__.py:37` ->
> `src/mcp_coder/checks/__init__.py:3` -> `src/mcp_coder/checks/branch_status.py:17` failing
> to import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still
> stale. No code written.
>
> **Ninth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved since
> the eighth.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop
> unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `1626fec` ("docs(pr_info): add round 2 implementation review log"). Since that
> commit is identical to the one inspected at the seventh/eighth re-checks, the upstream API
> shape is unchanged by construction and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus`
> or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0
> matches, and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Tenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved since
> the ninth.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop
> unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `1626fec` ("docs(pr_info): add round 2 implementation review log"). Since that
> commit is identical to the one inspected at the seventh/eighth/ninth re-checks, the
> upstream API shape is unchanged by construction and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Eleventh re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the tenth.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject):
> drop unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `1626fec` ("docs(pr_info): add round 2 implementation review log"). Since that
> commit is identical to the one inspected at the seventh through tenth re-checks, the
> upstream API shape is unchanged by construction and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Twelfth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved since
> the eleventh.** `origin/main` of mcp-workspace is *still* `b9106c4` ("chore(pyproject):
> drop unused config extra (#275)") and `git branch -r --merged origin/main` still lists only
> `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**; its head is also
> unchanged at `1626fec` ("docs(pr_info): add round 2 implementation review log"). Since that
> commit is identical to the one inspected at the seventh through eleventh re-checks, the
> upstream API shape is unchanged by construction and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus`
> or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0
> matches, and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Thirteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twelfth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through twelfth re-checks, the upstream API shape is unchanged by construction and
> sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Fourteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the thirteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through thirteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus`
> or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0
> matches, and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Fifteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the fourteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through fourteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`, and a repo-wide grep of the mcp-workspace tree still returns 0
> matches. This time the module the MCP tooling process resolves was read in **full** (all
> 301 lines), not just probed for its exports: it contains `GITHUB_TOKEN_HINT`, `CIStatus`,
> `WaitContext`, `format_report_for_human`, `format_report_for_llm`, `_review_gate_header`
> and `_format_wait_line`, and neither new name appears anywhere in the source. No code
> written.
>
> **Sixteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the fifteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through fifteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Seventeenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the sixteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through sixteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Eighteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the seventeenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through seventeenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus`
> or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0
> matches, and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). No code
> written.
>
> **Nineteenth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the eighteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through eighteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus`
> or `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0
> matches, and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at
> `tests/cli/commands/conftest.py:10` -> `src/mcp_coder/__init__.py:37` ->
> `src/mcp_coder/checks/__init__.py:3` -> `src/mcp_coder/checks/branch_status.py:17` failing
> to import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still
> stale. No code written.
>
> **Twentieth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the nineteenth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through nineteenth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at
> `tests/cli/commands/conftest.py:10` -> `src/mcp_coder/__init__.py:37` ->
> `src/mcp_coder/checks/__init__.py:3` -> `src/mcp_coder/checks/branch_status.py:17` failing
> to import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still
> stale. No code written.
>
> **Twenty-first re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twentieth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `1626fec` ("docs(pr_info): add round 2
> implementation review log"). Since that commit is identical to the one inspected at the
> seventh through twentieth re-checks, the upstream API shape is unchanged by construction
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at
> `tests/cli/commands/conftest.py:10` -> `src/mcp_coder/__init__.py:37` ->
> `src/mcp_coder/checks/__init__.py:3` -> `src/mcp_coder/checks/branch_status.py:17` failing
> to import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still
> stale. No code written.
>
> **Twenty-second re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-first.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)"); `git branch -r --merged origin/main`
> still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**,
> its head unchanged at `1626fec`. `git show
> origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches `class CIStatus`
> but **zero** occurrences of `LinkedBranchStatus` or `linked_branch_blocks`; a repo-wide
> grep of the mcp-workspace tree returns 0 matches, and the module the MCP tooling process
> resolves still exports neither name. Upstream API shape unchanged by construction (same
> commit as the seventh through twenty-first re-checks), so sections 2a-2d need no revision.
> No code written.

> **Twenty-third re-check after `git fetch` (2026-08-30) — still blocked.** `origin/main` of
> mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop unused config extra (#275)");
> `git branch -r --merged origin/main` still lists only `origin/main` and `origin/HEAD`, so
> `origin/268-...` remains **unmerged**. Its head has advanced `1626fec` -> `cdae676`
> ("docs(pr_info): add round 3 implementation review log entry", docs only). Because the head
> moved, the API shape was re-read on that branch rather than assumed: `LinkedBranchStatus`
> still has the same six members (`OK`, `MISMATCH`, `AMBIGUOUS`, `NOT_LINKED`, `UNKNOWN`,
> `NOT_CHECKED`) and `linked_branch_blocks` still returns
> `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`, so sections 2a-2d
> remain accurate as written and need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). Reinstalling
> would not help — the names are absent from `main` itself. No code written.

> **Twenty-fourth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-third.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `cdae676` ("docs(pr_info): add round 3
> implementation review log entry"). Since that commit is identical to the one inspected at
> the twenty-third re-check, the upstream API shape is unchanged by construction and sections
> 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). Reinstalling
> would not help — the names are absent from `main` itself. No code written.

> **Twenty-fifth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-fourth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `cdae676` ("docs(pr_info): add round 3
> implementation review log entry"). Since that commit is identical to the one inspected at
> the twenty-third and twenty-fourth re-checks, the upstream API shape is unchanged by
> construction and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). Reinstalling
> would not help — the names are absent from `main` itself. No code written.

---

## WHERE

| File | Role |
|---|---|
| `tests/cli/commands/test_check_branch_status_exit_code.py` | TDD — write first |
| `tests/checks/test_branch_status.py` | Shim-contract test — write first |
| `src/mcp_coder/checks/branch_status.py` | Re-export shim |
| `src/mcp_coder/cli/commands/check_branch_status.py` | `_exit_code` |
| `docs/cli-reference.md` | Exit-code table + limitation note |

No new files, no new modules.

---

## 2a. Tests first

**File:** `tests/cli/commands/test_check_branch_status_exit_code.py`

### Import

Extend the existing shim import — the test imports from `mcp_coder.checks.branch_status`,
not from `mcp_workspace`, which is what proves the shim re-export in 2b:

```python
from mcp_coder.checks.branch_status import (
    BranchStatusReport,
    CIStatus,
    LinkedBranchStatus,
)
```

### `_report()` gains one defaulted keyword

**WHAT:** extend the existing helper's signature; do not add a second helper.

```python
def _report(
    ci_status: CIStatus,
    *,
    undeterminable: bool = False,
    blocks_merge: bool = False,
    linked_branch_status: LinkedBranchStatus = LinkedBranchStatus.NOT_CHECKED,
) -> BranchStatusReport:
```

Pass `linked_branch_status=linked_branch_status` through to the `BranchStatusReport(...)`
construction. The default matches upstream's, so **every existing call site stays
untouched** and every existing assertion in the file keeps its current value.

### New test class — the ungated 6 x 2 mapping

**WHAT:** one parametrized test. Add after `TestExitCodeContract`.

```python
class TestLinkedBranchExitCode:
    """The linked-branch state feeds the ladder, ungated by --fail-on-reviews."""

    @pytest.mark.parametrize(
        ("linked_branch_status", "expected"),
        [
            (LinkedBranchStatus.OK, 0),
            (LinkedBranchStatus.NOT_CHECKED, 0),
            (LinkedBranchStatus.MISMATCH, 1),
            (LinkedBranchStatus.AMBIGUOUS, 1),
            (LinkedBranchStatus.NOT_LINKED, 1),
            (LinkedBranchStatus.UNKNOWN, 2),
        ],
    )
    @pytest.mark.parametrize("flag", [False, True])
    def test_linked_branch_mapping_is_ungated(
        self, linked_branch_status: LinkedBranchStatus, expected: int, flag: bool
    ) -> None:
        """Every state maps the same way with the review gate on and off.

        UNKNOWN is 2 rather than 1 even though linked_branch_blocks(UNKNOWN) is
        True: the tier-2 term is evaluated first. Reordering the two new terms
        in _exit_code turns this row red.
        """
        report = _report(CIStatus.PASSED, linked_branch_status=linked_branch_status)
        assert _exit_code(report, flag) == expected
```

**DATA:** 12 cases. `CIStatus.PASSED` isolates the linked-branch term — the CI verdict
contributes `0`, so the observed code is entirely the new behaviour.

Do **not** add a separate "UNKNOWN wins over blocking" test — the `UNKNOWN -> 2` row above
already is that assertion, with the same inputs.

### One tier-interaction case

**WHAT:** add a second method to `TestLinkedBranchExitCode`. The 6 x 2 table above fixes
`CIStatus.PASSED` with **no** review feedback, so it cannot see the one ordering that the
design rationale in summary.md actually rests on: the tier-1 `linked_branch_blocks` term
must stay *below* the gated tier-2 review term. Hoist it and every row above stays green
while the contract silently breaks.

```python
    def test_blocking_linked_branch_does_not_preempt_undeterminable_reviews(
        self,
    ) -> None:
        """MISMATCH + undeterminable reviews + gate on -> 2, not 1.

        linked_branch_blocks(MISMATCH) is True, but that is a tier-1 cause; the
        gated review term is tier 2 and is owed precedence. Moving the
        linked_branch_blocks term above it in _exit_code turns this red.
        """
        report = _report(
            CIStatus.PASSED,
            undeterminable=True,
            linked_branch_status=LinkedBranchStatus.MISMATCH,
        )
        assert _exit_code(report, True) == 2
        assert _exit_code(report, False) == 1
```

**DATA:** the `False` assertion is the same report with the gate off — the review term drops
out, leaving the tier-1 linked-branch term to return `1`. Both halves are needed: the first
pins the ordering, the second pins that the linked-branch term is ungated.

### Shim-contract test

**File:** `tests/checks/test_branch_status.py`

**WHAT:** extend the existing `test_shim_reexports_expected_names` — do not add a new test
function. `LinkedBranchStatus` is proven by the exit-code file's import, but
`linked_branch_blocks` is otherwise never reached through the shim, so 2b's `__all__`
addition would go unverified.

Add `linked_branch_blocks` and `LinkedBranchStatus` to that module's `from
mcp_coder.checks.branch_status import (...)` list and assert them alongside the existing
names:

```python
    assert callable(linked_branch_blocks)
    assert isinstance(LinkedBranchStatus.OK, LinkedBranchStatus)
```

Also assert both names are on the declared surface, which is what 2b edits:

```python
    assert {"LinkedBranchStatus", "linked_branch_blocks"} <= set(branch_status.__all__)
```

Leave the other three tests in that file (`test_ci_status_has_degradation_members`,
`test_report_has_pr_feedback_fields`, `test_collect_pr_feedback_not_reexported`) untouched.

### One end-to-end case

**WHAT:** add a method to the **existing** `TestFailOnReviewsEndToEnd` class, reusing its
`_run` helper. Do not create a second class duplicating the patching.

```python
    def test_linked_branch_mismatch_exit_1_ungated(self) -> None:
        report = _report(
            CIStatus.PASSED, linked_branch_status=LinkedBranchStatus.MISMATCH
        )
        assert self._run(report, fail_on_reviews=False) == 1
```

Widen that class's docstring to cover both causes, e.g. `"""The review gate and the
linked-branch state reach the process exit code via the real entry point."""`

**Run the tests now.** Expect the 12 mapping cases for `MISMATCH`/`AMBIGUOUS`/`NOT_LINKED`/
`UNKNOWN`, the tier-interaction case's `_exit_code(report, False) == 1` half and the
end-to-end case to fail (all returning `0`); the `OK` and `NOT_CHECKED` rows already pass,
as does the tier-interaction case's gated half (`== 2`, from the review term alone). The
shim-contract additions fail at import until 2b lands.

---

## 2b. Shim re-export

**File:** `src/mcp_coder/checks/branch_status.py`

**HOW:** extend the existing `branch_status_rendering` import and `__all__`. The name order
below is isort's (`profile = "black"`, `order_by_type` — constants, classes, functions) and
matches upstream's own import of the same module.

```python
from mcp_workspace.checks.branch_status_rendering import (
    GITHUB_TOKEN_HINT,
    CIStatus,
    LinkedBranchStatus,
    linked_branch_blocks,
)
```

`__all__` gains `"LinkedBranchStatus"` and `"linked_branch_blocks"`.

No docstring change: the module rule is "only names actually consumed by mcp-coder
callers/tests", which 2c satisfies.

---

## 2c. The two terms

**File:** `src/mcp_coder/cli/commands/check_branch_status.py`

### Import

```python
from ...checks.branch_status import (
    GITHUB_TOKEN_HINT,
    BranchStatusReport,
    CIStatus,
    LinkedBranchStatus,
    collect_branch_status,
    linked_branch_blocks,
)
```

### `_exit_code` — signature unchanged

```python
def _exit_code(report: BranchStatusReport, fail_on_reviews: bool) -> int:
```

**ALGORITHM** (the two `# NEW` lines are the whole change):

```python
verdict = assess_ci(report.ci_status, require_proven=False)
if verdict == "undeterminable":                                 return 2
if report.linked_branch_status is LinkedBranchStatus.UNKNOWN:   return 2   # NEW
if fail_on_reviews and report.pr_feedback_undeterminable:       return 2
if verdict == "failed":                                         return 1
if linked_branch_blocks(report.linked_branch_status):           return 1   # NEW
if fail_on_reviews and report.pr_feedback_blocks_merge:         return 1
return 0
```

Written out as real one-statement-per-line `if`/`return` pairs, matching the current body.

**Constraints:**

- The tier-2 `UNKNOWN` term **must** precede the tier-1 `linked_branch_blocks` term —
  `UNKNOWN` satisfies both. Order within each tier is free.
- Use the predicate, not a local tuple of blocking states, so a state added upstream later
  inherits the right behaviour.
- Eight `return`s is fine: pylint's `R` category (including `too-many-return-statements`) is
  disabled project-wide at `pyproject.toml:198-204`.

**DATA:** returns `int` in `{0, 1, 2}`. Unchanged contract, three inputs instead of two.

### Docstring

The current one attributes every non-CI cause to the review gate, and its
`fail_on_reviews` arg line says "when False, only CI status drives the code" — now false.
Rewrite along these lines:

```python
    """Map a report to a process exit code. Evaluated 2 -> 1 -> 0.

    Precedence: undeterminable (2) wins over blocking (1) wins over clean (0).

    Three causes feed the ladder: the CI verdict, the issue's linked-branch
    state, and PR-review feedback. Only the review terms are gated on
    fail_on_reviews; the linked-branch terms participate whenever the check ran,
    mirroring upstream, which suppresses "Ready to merge" on a blocking linked
    branch regardless of the flag.

    Args:
        report: Collected branch status report.
        fail_on_reviews: When True, PR-review feedback participates in the gate;
            when False, it is informational only.

    Returns:
        2 if CI truth, the linked-branch lookup, or the (gated) review state is
        undeterminable; 1 if determined and blocking; 0 if proven clean.
    """
```

### Do not touch

- The `--fix` success path at `:352` (`return 0`) — out of scope, documented in 2d.
- The early return at `:317` — it already routes through `_exit_code`.
- `execute_check_branch_status`'s own docstring `Returns:` block is generic enough to stand.

---

## 2d. Docs

**File:** `docs/cli-reference.md`, the `#### Exit Codes` block at `:688-696`.

Row 1 (`Failure`) gains the linked-branch cause — mismatched, ambiguous, or absent:

> CI failed, `--wait-for-pr` expired without a PR appearing, or fix operations failed; the
> issue's linked branch is missing, ambiguous, or is not the current branch; or (with
> `--fail-on-reviews`) PR reviews block merge

Row 2 (`Technical Error or Undeterminable`) gains the failed lookup:

> Invalid arguments, Git errors, API errors, unexpected exceptions, missing GitHub token (CI
> unavailable); the linked-branch lookup could not be completed; or (with
> `--fail-on-reviews`) PR review state is undeterminable

Add one short note below the table making the ungating explicit, e.g.:

> **Note:** the linked-branch causes are **not** gated on `--fail-on-reviews` — they apply
> whenever the branch name yields an issue number, so a default run can exit non-zero on a
> stale linked branch.

Extend the existing known-limitation note at `:696` to cover both:

> **Known limitation:** neither `--fail-on-reviews` nor the linked-branch check is evaluated
> when `--fix` resolves CI — the `--fix` success path returns before the exit-code gate.

Wording is a guide, not a transcript; keep the table's existing style and column widths.
Leave the `--fail-on-reviews` option bullet at `:686` alone — the flag's own behaviour has
not changed.

---

## Verification

1. `./tools/format_all.sh` (isort will settle the import blocks).
2. `mcp__tools-py__run_pylint_check`
3. `mcp__tools-py__run_pytest_check` with
   `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"]`
4. `mcp__tools-py__run_mypy_check`

All 12 new mapping cases, the tier-interaction case, the extended shim-contract test and the
end-to-end case pass; every pre-existing test in
`test_check_branch_status_exit_code.py` and its sibling `test_check_branch_status*.py` files
stays green **without edits**. If a sibling test turns red, check whether it passes a `Mock`
rather than a real `BranchStatusReport` — `linked_branch_blocks(Mock())` is `True` and would
flip a `0` to a `1`. None do today.

---

## LLM prompt

> Implement **step 2** of `pr_info/steps/step_2.md`. Read `pr_info/steps/summary.md` first
> for the design rationale — especially why the two new terms sit in separate tiers rather
> than being merged into one branch, and why they are ungated by `--fail-on-reviews`.
>
> **Before writing code, run the precondition check at the top of step_2.md.** This step
> depends on mcp-workspace #268 being merged to `main`. If `LinkedBranchStatus` and
> `linked_branch_blocks` do not import from
> `mcp_workspace.checks.branch_status_rendering`, stop and report that the upstream
> dependency has not landed — do not stub or vendor the upstream names.
>
> Work test-first: extend `tests/cli/commands/test_check_branch_status_exit_code.py` and
> `tests/checks/test_branch_status.py` (section 2a) and watch the new cases fail, then make
> them pass via 2b (shim re-export), 2c (the two `_exit_code` terms plus its docstring) and
> 2d (`docs/cli-reference.md`).
>
> Extend the existing test files and their existing `_report()` helper,
> `TestFailOnReviewsEndToEnd._run` helper and `test_shim_reexports_expected_names` — do not
> add a new test file, a second report helper, a duplicate end-to-end class or a new shim
> test function. Existing tests must stay green without edits.
>
> Use MCP tools for all file operations. Run `./tools/format_all.sh`, then pylint, pytest
> (with the fast-unit-test marker exclusions) and mypy, and fix everything they report.
> Commit once, with tests, implementation and docs together.

> **Twenty-sixth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-fifth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `cdae676` ("docs(pr_info): add round 3
> implementation review log entry"). Same commit as the twenty-third through twenty-fifth
> re-checks, so the upstream API shape is unchanged by construction and sections 2a-2d need
> no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). The side
> finding above is **unchanged**: a targeted pytest run on `tests/checks/test_branch_status.py`
> + `tests/cli/commands/test_check_branch_status_exit_code.py` still aborts at
> `tests/cli/commands/conftest.py:10` -> `src/mcp_coder/__init__.py:37` ->
> `src/mcp_coder/checks/__init__.py:3` -> `src/mcp_coder/checks/branch_status.py:17` failing
> to import from `mcp_workspace.checks...`, i.e. the project venv's mcp-workspace is still
> stale. Reinstalling would not help *this* step — the names are absent from `main` itself.
> No code written.

> **Twenty-seventh re-check after `git fetch` (2026-08-30) — still blocked, nothing has
> moved since the twenty-sixth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged
> origin/main` still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains
> **unmerged**; its head is also unchanged at `cdae676` ("docs(pr_info): add round 3
> implementation review log entry"). Same commit as the twenty-third through twenty-sixth
> re-checks, so the upstream API shape is unchanged by construction and sections 2a-2d need
> no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`,
> `format_report_for_human`, `format_report_for_llm`, `truncate_ci_details`). Reinstalling
> would not help — the names are absent from `main` itself. No code written.

> **Twenty-eighth re-check after `git fetch` (2026-08-30) — still blocked.** `origin/main` of
> mcp-workspace is *still* `b9106c4` ("chore(pyproject): drop unused config extra (#275)") and
> `git branch -r --merged origin/main` still lists only `origin/main` and `origin/HEAD`, so
> `origin/268-...` remains **unmerged**. Its head *has* advanced this time (`cdae676` ->
> `dbf3a81`, "docs(pr_info): update commit message for isort fix"), so the API shape was
> re-verified against that blob rather than assumed: `class LinkedBranchStatus(str, Enum)` still
> has exactly the six members `OK`/`MISMATCH`/`AMBIGUOUS`/`NOT_LINKED`/`UNKNOWN`/`NOT_CHECKED`
> and `linked_branch_blocks(status)` still returns
> `status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)`. Sections 2a-2d need
> no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `GITHUB_TOKEN_HINT` and `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or
> `linked_branch_blocks`; a repo-wide grep of the mcp-workspace tree still returns 0 matches,
> and the module the MCP tooling process resolves still exports neither name (only
> `GITHUB_TOKEN_HINT`, `CIStatus`, `TaskTrackerStatus`, `WaitContext`, `format_report_for_human`,
> `format_report_for_llm`, `truncate_ci_details`). Reinstalling would not help — the names are
> absent from `main` itself. No code written.

> **Twenty-ninth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-eighth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged origin/main`
> still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**;
> its head is also unchanged at `dbf3a81` ("docs(pr_info): update commit message for isort
> fix"), so the API shape re-verified at that same blob during the twenty-eighth re-check
> still stands and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or `linked_branch_blocks`;
> a repo-wide grep of the mcp-workspace tree still returns 0 matches, and the module the MCP
> tooling process resolves still exports neither name (only `GITHUB_TOKEN_HINT`, `CIStatus`,
> `TaskTrackerStatus`, `WaitContext`, `format_report_for_human`, `format_report_for_llm`,
> `truncate_ci_details`). Reinstalling would not help — the names are absent from `main`
> itself. No code written.

> **Thirtieth re-check after `git fetch` (2026-08-30) — still blocked, nothing has moved
> since the twenty-ninth.** `origin/main` of mcp-workspace is *still* `b9106c4`
> ("chore(pyproject): drop unused config extra (#275)") and `git branch -r --merged origin/main`
> still lists only `origin/main` and `origin/HEAD`, so `origin/268-...` remains **unmerged**;
> its head is also unchanged at `dbf3a81` ("docs(pr_info): update commit message for isort
> fix"), so the API shape verified at that blob during the twenty-eighth re-check still stands
> and sections 2a-2d need no revision.
> `git show origin/main:src/mcp_workspace/checks/branch_status_rendering.py` matches
> `class CIStatus` but **zero** occurrences of `LinkedBranchStatus` or `linked_branch_blocks`;
> a repo-wide grep of the mcp-workspace tree still returns 0 matches, and the module the MCP
> tooling process resolves still exports neither name (only `GITHUB_TOKEN_HINT`, `CIStatus`,
> `TaskTrackerStatus`, `WaitContext`, `format_report_for_human`, `format_report_for_llm`,
> `truncate_ci_details`). Reinstalling would not help — the names are absent from `main`
> itself. No code written.
>
> **Note on these records.** Thirty re-checks have now produced thirty near-identical
> paragraphs and no progress. Nothing changes on this side until #268 is merged upstream;
> further re-checks add bookkeeping, not information. Suggest pausing this step until the
> upstream merge is observed rather than re-running it.
