# Step 1 — New `CIStatus.UNAVAILABLE` state + presentation (data layer)

> Read `pr_info/steps/summary.md` first. This step adds the new CI state and everything
> that *renders/recommends* it, with **no detection wiring yet** — so it is fully testable
> by constructing a report with `ci_status=CIStatus.UNAVAILABLE` directly.

## WHERE
- Source: `src/mcp_coder/checks/branch_status.py`
- Tests:  `tests/checks/test_branch_status.py`

## WHAT (changes in `branch_status.py`)

1. **Enum** — add a member to `CIStatus`:
   ```python
   class CIStatus(str, Enum):
       PASSED = "PASSED"
       FAILED = "FAILED"
       NOT_CONFIGURED = "NOT_CONFIGURED"
       PENDING = "PENDING"
       UNAVAILABLE = "UNAVAILABLE"  # auth/token missing — CI truth unknown
   ```

2. **Constant** — module-level, single source of truth for the actionable text
   (wording aligned with the `verify` GitHub-token message):
   ```python
   GITHUB_TOKEN_HINT = "no GitHub token; set GITHUB_TOKEN or add to config.toml"
   ```

3. **`format_for_human`** — add the icon and render the hint inline on the CI line:
   - Add to `ci_icon_map`: `CIStatus.UNAVAILABLE: "\U0001F512"  # 🔒`
   - Replace the single CI line append with:
     ```python
     ci_line = f"CI Status: {ci_icon} {self.ci_status.value}"
     if self.ci_status == CIStatus.UNAVAILABLE:
         ci_line += f" — {GITHUB_TOKEN_HINT}"
     lines.append(ci_line)
     ```

4. **`format_for_llm`** — append the same hint to `status_summary` when unavailable
   (right after `status_summary` is built, before the PR suffix logic is fine):
   ```python
   if self.ci_status == CIStatus.UNAVAILABLE:
       status_summary += f" ({GITHUB_TOKEN_HINT})"
   ```

5. **`_generate_recommendations`** — add one branch alongside the existing CI branches.
   Do **not** add it to the `NOT_CONFIGURED` ("Configure CI pipeline") branch:
   ```python
   elif ci_status == CIStatus.UNAVAILABLE:
       recommendations.append(f"Set a GitHub token ({GITHUB_TOKEN_HINT})")
   ```

## HOW (integration points)
- No new imports. `GITHUB_TOKEN_HINT` is a plain module constant referenced by both
  format methods and the recommendation branch.
- **Ready-to-merge needs no change.** The gate is
  `ci_status in [CIStatus.PASSED, CIStatus.NOT_CONFIGURED]` — `UNAVAILABLE` is absent, so
  "Ready to merge" is excluded automatically. Add a test that *locks in* this behavior.

## ALGORITHM (rendering, pseudocode)
```
icon = icon_map.get(ci_status, "❓")          # UNAVAILABLE → 🔒
line = f"CI Status: {icon} {ci_status.value}"
if ci_status is UNAVAILABLE: line += " — " + GITHUB_TOKEN_HINT
emit(line)
```

## DATA
- `CIStatus.UNAVAILABLE == "UNAVAILABLE"` (str-Enum equality holds).
- `format_for_human()` → string containing `CI Status: 🔒 UNAVAILABLE — no GitHub token; ...`.
- `format_for_llm()` → summary line containing `CI=UNAVAILABLE (no GitHub token; ...)`.
- `_generate_recommendations({"ci_status": CIStatus.UNAVAILABLE, ...})` → list that
  **contains** the "Set a GitHub token ..." item and **excludes** both
  "Configure CI pipeline" and "Ready to merge".

## TESTS (write first — TDD)
Add to `tests/checks/test_branch_status.py`:
1. `CIStatus.UNAVAILABLE == "UNAVAILABLE"` (mirror existing enum-value test at ~line 604).
2. `format_for_human` for an `UNAVAILABLE` report contains `🔒`, `UNAVAILABLE`, and the
   hint text on the CI line.
3. `format_for_llm` summary contains `CI=UNAVAILABLE` and the hint.
4. Recommendations for `UNAVAILABLE`: includes the token recommendation; excludes
   "Configure CI pipeline"; excludes "Ready to merge" even when tasks OK and no rebase.

## COMMIT
Single commit: tests + implementation, all three checks green.

## QUALITY GATES
```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check (extra_args=["-n","auto","-m","not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```
Run `./tools/format_all.sh` before committing.

## LLM PROMPT
> Implement Step 1 from `pr_info/steps/step_1.md` (see `pr_info/steps/summary.md` for
> context). In `src/mcp_coder/checks/branch_status.py`: add `CIStatus.UNAVAILABLE`, a
> module constant `GITHUB_TOKEN_HINT = "no GitHub token; set GITHUB_TOKEN or add to
> config.toml"`, the 🔒 icon-map entry, inline hint rendering in `format_for_human` and
> `format_for_llm`, and an `UNAVAILABLE` recommendation branch in
> `_generate_recommendations` (do NOT touch the ready-to-merge gate). Follow TDD: first add
> the tests described in Step 1 to `tests/checks/test_branch_status.py`, then implement.
> Do not add any token-detection logic in this step. Use only MCP tools per CLAUDE.md, run
> pylint/pytest/mypy, and produce exactly one commit.
