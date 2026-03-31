# Plan Review Log — Issue #647 (implement_direct)

## Review Summary

**Overall assessment**: The plan is well-structured and follows codebase conventions closely. Three findings below, two of which are actionable.

---

## Findings

### 1. Steps 1 and 2 should be merged (Severity: MEDIUM)

**Problem**: Step 1 creates `execute_checkout_issue_branch()` in `gh_tool.py` with tests, and Step 2 wires it into the parser and dispatcher. These are tightly coupled — the handler function cannot be exercised through the CLI until Step 2 is done. Splitting them creates a commit where the function exists but is unreachable. Per planning principles: "Merge tiny or intertwined steps."

Additionally, Step 2 is small (one subparser block in `parsers.py`, one `elif` + import in `main.py`, three parser tests). Combined with Step 1, the total is still a manageable single commit — one new function in `gh_tool.py`, one parser block, one dispatch route, and ~13 tests.

**Recommendation**: Merge Steps 1 and 2 into a single step: "Add `checkout-issue-branch` subcommand (handler + parser + tests)." This matches how `get-base-branch` was originally added (handler + wiring together).

---

### 2. Missing edge case: `get_issue` returns empty issue with `base_branch` absent (Severity: LOW)

**Problem**: The algorithm in Step 1 calls `IssueManager.get_issue(issue_number)` and then uses `issue_data["base_branch"]`. However, `IssueData` has `base_branch` as `NotRequired[Optional[str]]`. When `get_issue` fails (e.g., API error), it returns `create_empty_issue_data()` which does NOT include `base_branch` at all. The plan's test `test_checkout_issue_not_found` checks for `number == 0`, which is correct, but the algorithm description in Step 1 doesn't show checking for `number == 0` before accessing `base_branch`.

The plan's algorithm should be explicit:
```
3. issue_data = IssueManager(project_dir).get_issue(issue_number)
4. if issue_data["number"] == 0: return 1  # issue not found
5. branches = ...
```

This is already implied by the test cases but should be stated in the algorithm section for clarity.

**Recommendation**: Update the ALGORITHM section in Step 1 to check `issue_data["number"] == 0` immediately after `get_issue`, before accessing `base_branch`. The implementing LLM will likely figure this out from the test cases, so this is low severity.

---

### 3. Settings permission entry may need a Bash wildcard (Severity: LOW)

**Problem**: Step 3 adds `"Skill(implement_direct)"` to settings. But the existing settings already have an entry `"Bash(mcp-coder gh-tool get-base-branch)"` (specific, no wildcard). The new `checkout-issue-branch` command will also need a Bash permission for direct CLI invocation. The skill's `allowed-tools` has `Bash(mcp-coder gh-tool *)` but `settings.local.json` only allows the specific `get-base-branch` command.

Looking more carefully: `"Bash(mcp-coder git-tool:*)"` already exists with a wildcard for `git-tool`. The `gh-tool` entry is inconsistent — it only allows `get-base-branch` specifically. This is a pre-existing inconsistency, but the new command will need permission too.

**Recommendation**: Step 3 should also update the Bash permission from `"Bash(mcp-coder gh-tool get-base-branch)"` to `"Bash(mcp-coder gh-tool:*)"` (wildcard, matching the `git-tool` pattern). This covers both existing and new subcommands. Alternatively, add a second specific entry `"Bash(mcp-coder gh-tool checkout-issue-branch:*)"`. The wildcard approach is cleaner.

---

## Step Granularity Assessment

| Original Step | Verdict | Reasoning |
|---------------|---------|-----------|
| Step 1 (handler + tests) | Merge with Step 2 | Tightly coupled, unreachable code without parser wiring |
| Step 2 (parser + dispatch) | Merge with Step 1 | Too small standalone, depends on Step 1 |
| Step 3 (skill + settings) | Keep as-is | Independent, no Python code, distinct concern |

**Proposed revised steps:**
- **Step 1**: Add `checkout-issue-branch` subcommand — handler in `gh_tool.py`, parser in `parsers.py`, dispatch in `main.py`, all tests
- **Step 2**: Skill file + settings update (current Step 3)

---

## Items That Look Good

- Handler follows the existing `execute_get_base_branch()` pattern exactly (exit codes 0/1/2, ValueError handling, broad-exception-caught)
- Test structure mirrors src structure (`tests/cli/commands/test_gh_tool.py`)
- Correct use of `IssueManager` and `IssueBranchManager` APIs — the TypedDict fields and method signatures match the actual code
- `subprocess.run` for git operations is consistent with how other CLI commands work
- Skill frontmatter uses the newer skills format correctly
- No unnecessary abstractions — direct calls to existing managers
- Test coverage is thorough with both exit-code tests and behavioral tests

---

## Questions

None — the plan is clear and the design decisions are sound.
