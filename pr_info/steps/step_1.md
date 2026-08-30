# Step 1 — Linked-branch state feeds `_exit_code`

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

---

## WHERE

| File | Role |
|---|---|
| `tests/cli/commands/test_check_branch_status_exit_code.py` | TDD — write first |
| `src/mcp_coder/checks/branch_status.py` | Re-export shim |
| `src/mcp_coder/cli/commands/check_branch_status.py` | `_exit_code` |
| `docs/cli-reference.md` | Exit-code table + limitation note |

No new files, no new modules.

---

## 1a. Tests first

**File:** `tests/cli/commands/test_check_branch_status_exit_code.py`

### Import

Extend the existing shim import — the test imports from `mcp_coder.checks.branch_status`,
not from `mcp_workspace`, which is what proves the shim re-export in 1b:

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
`UNKNOWN` and the end-to-end case to fail (all returning `0`); the `OK` and `NOT_CHECKED`
rows already pass.

---

## 1b. Shim re-export

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
callers/tests", which 1c satisfies.

---

## 1c. The two terms

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

- The `--fix` success path at `:352` (`return 0`) — out of scope, documented in 1d.
- The early return at `:317` — it already routes through `_exit_code`.
- `execute_check_branch_status`'s own docstring `Returns:` block is generic enough to stand.

---

## 1d. Docs

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

All 12 new mapping cases plus the end-to-end case pass; every pre-existing test in
`test_check_branch_status_exit_code.py` and its sibling `test_check_branch_status*.py` files
stays green **without edits**. If a sibling test turns red, check whether it passes a `Mock`
rather than a real `BranchStatusReport` — `linked_branch_blocks(Mock())` is `True` and would
flip a `0` to a `1`. None do today.

---

## LLM prompt

> Implement **step 1** of `pr_info/steps/step_1.md`. Read `pr_info/steps/summary.md` first
> for the design rationale — especially why the two new terms sit in separate tiers rather
> than being merged into one branch, and why they are ungated by `--fail-on-reviews`.
>
> **Before writing code, run the precondition check at the top of step_1.md.** This step
> depends on mcp-workspace #268 being merged to `main`. If `LinkedBranchStatus` and
> `linked_branch_blocks` do not import from
> `mcp_workspace.checks.branch_status_rendering`, stop and report that the upstream
> dependency has not landed — do not stub or vendor the upstream names.
>
> Work test-first: extend `tests/cli/commands/test_check_branch_status_exit_code.py`
> (section 1a) and watch the new cases fail, then make them pass via 1b (shim re-export),
> 1c (the two `_exit_code` terms plus its docstring) and 1d (`docs/cli-reference.md`).
>
> Extend the existing test file and its existing `_report()` helper and
> `TestFailOnReviewsEndToEnd._run` helper — do not add a new test file, a second report
> helper, or a duplicate end-to-end class. Existing tests must stay green without edits.
>
> Use MCP tools for all file operations. Run `./tools/format_all.sh`, then pylint, pytest
> (with the fast-unit-test marker exclusions) and mypy, and fix everything they report.
> Commit once, with tests, implementation and docs together.
