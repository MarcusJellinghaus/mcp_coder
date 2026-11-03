# review-plan review log 1

## Round 1 — 2026-11-03
**Findings**:
Now verify key code facts.Checking the remaining code facts (CI status shape, fix-ci and fix-conflict bodies) against the plan.Verifying the remaining plan targets: CLI helpers, the CI poll signature, and the create-pr command.`pr_info/steps/step_3.md:103` — low — The `("HTTP status", str(status) or None)` field turns `status=None` (a possible `MergeResult.status` for `error`) into the literal string "None", so `build_failure_comment` will not drop it. Use `str(status) if status is not None else None`.
`pr_info/steps/summary.md:125` — low — The summary names `tests/cli/test_resolver_utils.py`, but `resolve_issue_interaction_flags` is tested in `tests/cli/test_utils.py`. `resolve_auto_merge` tests belong there.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_3.md:103, change the HTTP status field from `("HTTP status", str(status) or None)` to `("HTTP status", str(status) if status is not None else None)`. That way `build_failure_comment` drops the field when `MergeResult.status` is None, instead of showing the literal string "None".', 'In pr_info/steps/summary.md:125 (and in any step file that names the same path), replace `tests/cli/test_resolver_utils.py` with `tests/cli/test_utils.py`, where `resolve_issue_interaction_flags` is already tested. The `resolve_auto_merge` tests should go there too.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-03
**Findings**:
Checking the plan against the code: rebase helpers, CI poll, label functions.Verifying `find_pull_request_by_head` and the `_handle_github_errors` decorator behaviour (raises on 401/403 for find too?).Checking `labels.json` structure and label-related tests for step 1.Checking file sizes of the files the plan touches.Last check: the fix-conflict command entry point, then the report.`pr_info/steps/step_5.md:51` — low — With `auto_merge` on, a create-pr soft pass (`verified_sha` is None) drops straight to `apply_post_creation_label` without logging anything. The issue's Step 1 table requires "keep `pr-created`, log a warning" for a soft pass. Add a `logger.warning` when `auto_merge and label == "pr_created" and not verified_sha`, plus a test.
`pr_info/steps/step_3.md:77` — low — On the retry pass (`attempt == 2`), a `refused` result goes to `_failed(result)` without reading `mergeable_state`. The issue's `99f` comment should include `mergeable_state` "when it is known". Either call `_poll_mergeable_state` before `_failed` on a second-pass refusal, or state in the plan that the field is left out there on purpose.
**Decisions**:
Verdict(decision='tasks', tasks=['In pr_info/steps/step_5.md around line 51, handle the create-pr soft pass when `auto_merge` is on: if `auto_merge and label == "pr_created" and not verified_sha`, emit a `logger.warning` stating that auto-merge was skipped because CI was not verified and the `pr-created` label is kept. Do this before `apply_post_creation_label`, as the issue\'s Step 1 table requires. Add a matching test that asserts the warning is logged and the `pr-created` label is applied.', "In pr_info/steps/step_3.md around line 77, add a note that a `refused` result on the second attempt goes to `_failed(result)` without polling, so `mergeable_state` is left out of the 99f comment there on purpose. This is allowed because the issue includes the field only 'when it is known'."], escalate_reason=None)
**Changes**:
applied
