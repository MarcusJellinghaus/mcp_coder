# review-plan review log 1

## Round 1 — 2026-10-25
**Findings**:
Review done; here is the report.

pr_info/steps/step_2.md:37 — medium — The plan hardcodes "A ruleset-protected branch shows OK even without `Administration: Read`", but it doesn't yet know which permission the effective-rules endpoint needs (precondition 2 exists to find that out). If upstream finds `/rules/branches/{branch}` also needs `Administration: Read`, this sentence would be wrong. Make the sentence depend on the recorded finding.
pr_info/steps/step_2.md:16 — medium — Precondition 2 blocks the whole docs step until upstream records the token-permission findings. But edits 2 (strictest-wins, `not verifiable` only when both sources lack protection) and 3 (bypass-actors sentence) don't depend on those findings. Either block only edit 1 and the permission sentence, or state why the full block is intended.
pr_info/steps/step_1.md:29 — low — The step says the new tests must fail first, but test cases 3–5 (suppressed when parent fails, suppressed when parent is unverifiable, key absent) already pass before the change: the unregistered key prints raw as `require_pull_request`, so `"Require pull request" not in output` holds. Only cases 1–2 go red. Either mark cases 3–5 as regression guards or drop the "must fail" wording for them.
pr_info/steps/summary.md:11 — low — Nothing in the plan says when or by whom the environment gets reinstalled with the new mcp-workspace. Step 2 only detects that it is missing (precondition 1) and stops. Add one line naming the reinstall as an outside prerequisite, e.g. on the `blocked` label, so a run doesn't stall on it.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_2.md:37, remove the hardcoded claim that a ruleset-protected branch shows OK without `Administration: Read`. Make the sentence depend on the token-permission finding recorded under precondition 2: if `/rules/branches/{branch}` needs no extra permission, say so; if it also needs `Administration: Read`, say that instead.', 'In pr_info/steps/step_2.md:16, narrow precondition 2 so that it blocks only edit 1 and the permission sentence. Edits 2 (strictest-wins; `not verifiable` only when both sources lack protection) and 3 (the bypass-actors sentence) do not depend on the permission findings, so they should go ahead without waiting.', "In pr_info/steps/step_1.md:29, limit the 'must fail first' requirement to test cases 1–2. Mark cases 3–5 (suppressed when the parent fails, suppressed when the parent is unverifiable, key absent) as regression guards that already pass before the change."], escalate_reason=None)
**Changes**:
applied
