# Summary — check-branch-status: extend `_exit_code` with the linked-branch block

Issue [#1146](https://github.com/MarcusJellinghaus/mcp-coder/issues/1146).

## Goal

`mcp-coder check branch-status` prints a report that already refuses `Ready to merge`
when the issue's linked branch does not match the current branch (delivered upstream by
[mcp-workspace #268](https://github.com/MarcusJellinghaus/mcp-workspace/issues/268), which
reaches us for free through the re-export shim). The **exit code** does not see that block,
so the command still exits `0` while the report it just printed says the branch is not
ready. Automation gating on the exit code proceeds on a superseded branch.

This change adds the linked-branch state to `_exit_code`, and repairs the three pieces of
prose that describe the gate.

## Architectural / design changes

**No new abstractions.** The change is two boolean terms inserted into an existing ladder,
plus two names added to an existing re-export list. No new module, class, function, or
config.

1. **The exit-code ladder gains a third input.** `_exit_code` previously derived from two
   sources: the CI verdict (`assess_ci`) and PR-review feedback. It now derives from three,
   the linked-branch state being the new one. The `2 -> 1 -> 0` precedence contract is
   unchanged — each new term is placed inside its existing tier:

   | Tier | Existing terms | New term |
   |---|---|---|
   | 2 (undeterminable) | CI undeterminable; (gated) reviews undeterminable | `linked_branch_status is UNKNOWN` |
   | 1 (blocking) | CI failed; (gated) reviews block merge | `linked_branch_blocks(linked_branch_status)` |
   | 0 | — | — |

   Order *within* a tier does not affect the result. Order *between* the two new terms does:
   `UNKNOWN` satisfies `linked_branch_blocks` too, so the tier-2 term must precede the tier-1
   term or `UNKNOWN` collapses to `1`. This is the reason the two terms are not merged into
   a single `return 2 if ... else 1` branch — such a merge would also make a `MISMATCH`
   short-circuit past the tier-2 review term and return `1` where `2` is owed.

2. **The new terms are ungated.** Unlike the review terms, they participate regardless of
   `--fail-on-reviews`. This mirrors upstream, where the `and not linked_branch_blocking`
   term suppresses `Ready to merge` unconditionally and only the `Review Gate:` *header* is
   flag-suppressed. Gating the exit code would leave a default run printing
   `Linked Branch: MISMATCH ...` with no `Ready to merge` and still exiting `0` — the exact
   disagreement this issue removes. **Consequence, stated plainly:** `--fail-on-reviews` is
   no longer the only thing that can turn a `0` into a `1`.

3. **Blocking is asked, not enumerated.** `_exit_code` calls upstream's
   `linked_branch_blocks(status)` predicate rather than listing the blocking states locally.
   A state added upstream later then inherits the right behaviour instead of falling through
   a stale local list. Only the `UNKNOWN` term names a member directly, because upstream has
   no "undeterminable" predicate.

4. **Both new names arrive via the shim.** `src/mcp_coder/checks/branch_status.py` already
   re-exports `CIStatus` and `GITHUB_TOKEN_HINT` from `mcp_workspace.checks.branch_status_rendering`;
   `LinkedBranchStatus` and `linked_branch_blocks` sit on that exact precedent, and the shim's
   docstring rule ("only names actually consumed by mcp-coder callers") is satisfied once
   `_exit_code` uses them. Note this is convention, not a checked contract — import-linter
   cannot enforce shim-only access to external subpackages (`.importlinter:73-84`).

5. **Layering unchanged.** `cli.commands` -> `checks` -> `mcp_workspace` is the existing
   direction (`docs/architecture/architecture.md:341`). Nothing moves between layers.

### Deliberately not changed

- **The `--fix` success path stays open.** `execute_check_branch_status` returns a bare `0`
  after successful fixes (`check_branch_status.py:352`) and never reaches `_exit_code`.
  Routing it through does not work: the stale report still carries `CIStatus.FAILED`, so it
  would return `1` and destroy the fix-success semantics. Closing it needs a separate guard.
  Deferred; documented alongside the existing `--fail-on-reviews` limitation.
- **Everything on the mcp-workspace side** — the check, the states, the rendering, and
  repairing a stale link (`createLinkedBranch` / `deleteLinkedBranch` are writes;
  `check_branch_status` is read-only).
- **`_review_gate_header`.** Upstream renders `Review Gate: BLOCKED (linked branch)`, but
  that header is display-only and does not feed `_exit_code`. Independent change.

## Upstream API — verified

Re-confirmed against mcp-workspace branch
`268-check-branch-status-verify-the-issue-s-linked-branch-matches-the-current-branch`
at commit `1ccb198`.

`mcp_workspace/checks/branch_status_rendering.py`:

```python
class LinkedBranchStatus(str, Enum):
    OK = "OK"                    # exactly one linked branch, equals current
    MISMATCH = "MISMATCH"        # exactly one linked branch, differs
    AMBIGUOUS = "AMBIGUOUS"      # more than one linked branch
    NOT_LINKED = "NOT_LINKED"    # queried fine, no linked branch
    UNKNOWN = "UNKNOWN"          # lookup could not be completed
    NOT_CHECKED = "NOT_CHECKED"  # branch name yields no issue number


def linked_branch_blocks(status: LinkedBranchStatus) -> bool:
    return status not in (LinkedBranchStatus.OK, LinkedBranchStatus.NOT_CHECKED)
```

There is **no blocking flag on the report** — blocking is the free function above. The
`linked_branch_blocks` *dict key* is internal to `collect_branch_status`.

**Two drifts from the issue text, neither affecting this plan:**

1. `BranchStatusReport` gains **three** trailing defaulted fields, not two:
   `linked_branch_status: LinkedBranchStatus = NOT_CHECKED`, `linked_branches: tuple[str, ...] = ()`,
   and `linked_branch_issue_number: Optional[int] = None` (renderer-only — this
   implementation never touches it). All defaulted, so every existing
   `BranchStatusReport(...)` construction in this repo stays valid untouched.
2. Upstream separates `UNKNOWN` from `NOT_LINKED` via a new
   `IssueBranchManager.get_linked_branches_or_none` returning `None` on failure. The issue's
   "four in-body paths return `[]`" is the pre-fix rationale, not the shipped shape.

## Dependency — blocked on upstream merge

`origin/main` of mcp-workspace has **no** `LinkedBranchStatus`, and the mcp-workspace
installed in this environment does not either. Branch `268-...` exists on the remote at
`1ccb198` but is unmerged.

`pyproject.toml:24,347` take mcp-workspace as an **unpinned git dependency off the default
branch**, so no version bump is needed — but **step 1 fails with `ImportError` until #268
lands on `main`**. The blocker is merge, not release. Re-verify the API names above before
implementing; reinstall mcp-workspace after the merge.

**Step 2 is not blocked** and can land independently (see below).

## Known risk, recorded not reopened

**Exit 2 gets easier to trigger.** `UNKNOWN` covers upstream failure paths including a
GraphQL blip or a token lacking permission to read `linkedBranches`. A token that works fine
for REST/CI can therefore turn a run that used to exit `0` into a `2`, and `2` conventionally
reads as "technical error" to callers. This is downstream of #268's settled "all non-OK
states block" decision.

**No no-token regression.** Without a token `IssueBranchManager.__init__` raises -> `UNKNOWN`
-> `2`, but CI is already `UNAVAILABLE` -> `2` via `assess_ci`. Same exit code, no new path.

**No in-repo exit-code consumer.** Nothing in `workflows/`, `workflow_steps/` or the
coordinator shells out to `check branch-status`; the consumers are shell scripts and CI. That
is why the printed-report/exit-code disagreement went unnoticed.

## Files created / modified

No folders or modules are created. No files are created.

### Modified — step 1

| File | Change |
|---|---|
| `src/mcp_coder/checks/branch_status.py` | Re-export `LinkedBranchStatus` and `linked_branch_blocks` (import list + `__all__`) |
| `src/mcp_coder/cli/commands/check_branch_status.py` | Import both from the shim; two new terms in `_exit_code`; `_exit_code` docstring |
| `docs/cli-reference.md` (`:688-696`) | Exit-code table rows 1 and 2 gain the linked-branch cause; ungated note; `--fix` known limitation |
| `tests/cli/commands/test_check_branch_status_exit_code.py` | `_report()` gains a defaulted `linked_branch_status`; one 6x2 parametrized mapping test; one end-to-end case |

### Modified — step 2

| File | Change |
|---|---|
| `.claude/skills/implementation_approve/SKILL.md` (`:19`) | "passes (exit code 0)" -> report's `Recommendations` contains `Ready to merge` |

## Steps

| Step | Scope | Blocked on #268? |
|---|---|---|
| [step_1.md](./step_1.md) | Shim re-export + `_exit_code` terms + tests + `docs/cli-reference.md` | **Yes** |
| [step_2.md](./step_2.md) | `implementation_approve` skill wording | No |

### Why two steps and not three

The shim export, the `_exit_code` terms and the `cli-reference.md` rows are **one behaviour
change**: the shim export exists only to serve `_exit_code`, and the doc rows describe
exactly the codes that step introduces. Splitting them would produce a commit adding an
unconsumed re-export, and a window where the documented exit codes contradict the shipped
ones. They are one commit.

The skill wording is genuinely independent — it is wrong **today**, before any of this
lands: step 1 of that skill calls the `mcp__mcp-workspace__check_branch_status` MCP tool,
which returns text and no exit code at all, so "passes (exit code 0)" already describes
nothing. It is also the only part not blocked on the upstream merge, so keeping it separate
lets it land while #268 is in flight.

## Test strategy

`tests/cli/commands/test_check_branch_status_exit_code.py` is the exit-code contract's home
and is **extended, not replaced**. The file's existing two-layer pattern is preserved: a
pure layer that builds small `BranchStatusReport`s and calls `_exit_code` directly, and a
thin end-to-end layer that drives `execute_check_branch_status` with only
`collect_branch_status` faked.

The upstream default `NOT_CHECKED` keeps every existing test in that file green untouched,
including the full `test_ci_mapping_unchanged_after_assess_ci` table. The sibling
`test_check_branch_status*.py` files all build real `BranchStatusReport` instances (no `Mock`
reports), so they stay green too — a `Mock` report would make `linked_branch_blocks` return
`True` and silently flip a `0` into a `1`, so that property is worth keeping in mind, but no
such report exists today. **No test migration to budget for.**
