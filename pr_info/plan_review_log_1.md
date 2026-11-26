# review-plan review log 1

## Round 1 — 2026-11-27
**Findings**:
Checking existing `test_init_file_access.py` assertions that the new hint condition could break.`pr_info/steps/step_1.md:103` — medium — Test 5 checks the "Commit .gitignore and .mcp-file-access" hint on an empty project, where `rules.changed` and `scratch_added` are also True, so it can't show that `logs_added` triggers the hint. The issue requires the hint "also fires when only this block was added". Add a test that pre-creates the template `.mcp-file-access`, plus a `.gitignore` that already has the VSCodeClaude block and `.scratch/` but no session-log lines. It then asserts the hint and `Gitignore: /.mcp-coder/*, /logs/ added`.
`pr_info/steps/step_1.md:101` — low — No test covers the issue's rule that the block is written "regardless of `.mcp-file-access` skip reasons". Add an assertion that `/logs/` and `/.mcp-coder/*` are written to an existing skip-reason test, such as an invalid rules file, or to a new `execute_init` case.
`pr_info/steps/step_1.md:106` — low — No test covers the `utf-8-sig` read with a BOM or a CRLF `.gitignore` that has no trailing newline. That is the constraint "Read `.gitignore` with `utf-8-sig` and write LF line endings". Add one case, like test 6, asserting the spelling is detected with a BOM present, that no `\r\n` is added, and that the new block isn't glued onto the last line.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_1.md (near line 103), add a test that isolates the logs_added hint trigger: pre-create the template `.mcp-file-access` and a `.gitignore` that already contains the VSCodeClaude block and `.scratch/` but no session-log lines; run init and assert the 'Commit .gitignore and .mcp-file-access' hint appears and the output reports `Gitignore: /.mcp-coder/*, /logs/ added`.", 'In pr_info/steps/step_1.md (near line 101), extend an existing `.mcp-file-access` skip-reason test (e.g. the invalid rules file case) or add a new `execute_init` case to assert that `/logs/` and `/.mcp-coder/*` are still written to `.gitignore` when `.mcp-file-access` handling is skipped.', 'In pr_info/steps/step_1.md (near line 106), add a test similar to test 6 using a `.gitignore` with a UTF-8 BOM, CRLF line endings and no trailing newline; assert the existing spelling is detected despite the BOM, no new `\\r\\n` is introduced by the appended block, and the new block starts on its own line rather than being joined to the last existing line.'], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-27
**Findings**:
Checking whether existing init tests assert exact `.gitignore` contents that the new block would break.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
