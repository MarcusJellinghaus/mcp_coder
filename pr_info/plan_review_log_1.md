# review-plan review log 1

## Round 1 — 2026-10-26
**Findings**:
Checking the test fixtures in `test_checks.py` against step 2's plan.`pr_info/steps/step_2.md:105` — low — The test "untrusted thread with watermark → `OUTPUT` line" can't exercise a watermark as written. When the PR has only untrusted threads, `get_issue_events` is never called (line 93), so no watermark is ever computed. The fixture also needs an old review or comment so that events are fetched and a watermark exists. Only then does it cover the issue's case "untrusted thread → `OUTPUT` line regardless of watermark".
`pr_info/steps/step_1.md:84` — low — No test checks that `_fetch_marked_comment` passes the result of `get_trusted_commenters()` into `_find_marked_comment`. Add one case: the patched allowlist contains `{"friend"}`, and a ❌ comment from `friend` with association `NONE` is found through `create_status_file`. Without it, the allowlist path through the status note is never exercised.
`pr_info/steps/step_2.md:54` — low — `PullRequestData.user` is `Optional[str]`, so for a ghost or missing PR author the untrusted-author `OUTPUT` line prints `@None`. Specify a fallback such as `@?`, or state that `@None` is acceptable.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_2.md (~line 105), fix the test 'untrusted thread with watermark → OUTPUT line'. Add an old review or comment to the fixture so that get_issue_events is called and a watermark is computed. Then assert the untrusted thread still produces the OUTPUT line, which covers the issue's case 'untrusted thread → OUTPUT line regardless of watermark'.", 'In pr_info/steps/step_1.md (~line 84), add a test case for create_status_file. Patch get_trusted_commenters() to return {"friend"}, then assert that a ❌ comment from author \'friend\' with association NONE is found. This checks that _fetch_marked_comment passes the allowlist into _find_marked_comment.'], escalate_reason=None)
**Changes**:
applied
