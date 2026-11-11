# review-plan review log 1

## Round 1 — 2026-11-11
**Findings**:
Plan read; now spot-checking the symbols and doc anchors the plan cites against the repo.Symbols and anchors check out so far; confirming the file-size limit and the existing `#prompt-configuration` anchor target.`pr_info/steps/step_1.md:153` — medium — Step 1 moves the npm `mcp-coder.toml` example out of `## Command toolkit` into `## Examples` → `### npm`. Two links still treat `#command-toolkit` as where the template lives: the new `mcp-coder.toml` row in `docs/repository-setup/README.md` (`step_3.md:91`, "Template: …#command-toolkit") and #1198's npm template. Either keep the npm example (or a full copy) under `## Command toolkit`, or point the step_3 row at `toolkits.md#npm`.
`pr_info/steps/step_3.md:48` — medium — The architecture.md §1 edit doesn't cover the phrase "the installer and architecture enforcement assume a Python target repo" (architecture.md:9). README edit 4 (`step_3.md:36-39`) drops "the architecture checks" from the same claim because they run only through `PythonToolkit`'s `check@full`. If §1 keeps the phrase, the two pages contradict each other. Add a line telling the implementer to drop or rescope "architecture enforcement" in §1 the same way.
`pr_info/steps/step_3.md:59` — low — architecture.md §4 (line 60) and 05-implementation.md (line 40) both repeat "`check_type_hints = false` drops the `check@*` requests", which is a transitional fact `toolkits.md` now owns. Step 3 edits both sentences but doesn't link this clause to `#until-the-next-breaking-release`, so the fact is still stated in three places. That goes against the issue's "Other pages link here instead of repeating these facts."
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_3.md (~line 91), change the new `mcp-coder.toml` row's template link in docs/repository-setup/README.md from `toolkits.md#command-toolkit` to `toolkits.md#npm`, because step 1 moves the npm example under `## Examples` → `### npm`. Also note in step_1.md (~line 153) that #1198's npm template link must target `#npm`.", "In pr_info/steps/step_3.md (~line 48), add an instruction for the architecture.md §1 edit: drop or rescope the phrase 'the installer and architecture enforcement assume a Python target repo' (architecture.md:9) the same way README edit 4 (step_3.md:36-39) does. Architecture checks run only through PythonToolkit's `check@full`, and the two pages must not contradict each other.", "In pr_info/steps/step_3.md (~line 59), replace the restated '`check_type_hints = false` drops the `check@*` requests' clause in both architecture.md §4 (line 60) and 05-implementation.md (line 40) with a link to `toolkits.md#until-the-next-breaking-release`, so that toolkits.md is the only place this fact is stated."], escalate_reason=None)
**Changes**:
applied

## Round 2 — 2026-11-11
**Findings**:
Reviewing the plan files against the issue; checking a few cited code facts before writing up the findings.`pr_info/steps/step_3.md:24` — medium — README edit 1 would have README say "mcp-coder runs the configured toolkit's checks and tests after each step". That is wrong: `DEFAULT_BINDINGS["implement_task"]` is `("check@quick",)`, so no tests run after each step by default. Tests run only in the `implement_final` gate (`test@quick`). Use the issue's own wording instead: "mcp-coder runs the configured bindings (after each task and as a final gate)", with no claim about checks and tests per step.

`pr_info/steps/step_1.md:48` — medium — The "Configure a toolkit" section (the anchor #1199's error message points to) is framed as "Shortest path: add the table with one `toolkit` line" and shows `toolkit = "command"` as a one-liner. For `command` this is not enough: with no `[tool.mcp-coder.toolkit.command]` steps, `verify` fails on the missing `format` table and other actions return `error` at run time. State that `command` also needs its step tables, and link `#command-toolkit` / `#npm` from that sentence.

`pr_info/steps/step_1.md:154` — medium — The plan moves the npm template's anchor to `toolkits.md#npm`, but the issue says the template is at `toolkits.md#command-toolkit` in two places: the Scope 3 `repository-setup/README.md` row and the Out-of-scope #1198 follow-up. This deviation is written only in a `pr_info` step file, which gets deleted. Add an instruction to record it in the commit body / PR description so the #1198 follow-up uses `#npm`.

`pr_info/steps/step_1.md:203` — low — The verification pattern `(?i)proposed|will be|until ` expects "only the heading". The same step tells the implementer to link the transitional section from Bindings and from Configure a toolkit, and link text such as "[Until the next breaking release](…)" also matches, so the check fails falsely. Allow link text in the expected result, or require link text that doesn't contain "until ". The same applies to `pr_info/steps/step_2.md:163`.
**Decisions**:
Verdict(decision='tasks', tasks=["In pr_info/steps/step_3.md (~line 24), change README edit 1 so it no longer says checks and tests run after each step. By default `implement_task` binds only `check@quick`, and tests run only in the `implement_final` gate. Use the issue's wording instead: 'mcp-coder runs the configured bindings (after each task and as a final gate)'.", 'In pr_info/steps/step_1.md (~line 48), have the \'Configure a toolkit\' section say that `toolkit = "command"` alone is not enough: it also needs its `[tool.mcp-coder.toolkit.command]` step tables, at least `format`, or `verify` fails and actions return `error`. Link that sentence to `#command-toolkit` and `#npm`.', 'In pr_info/steps/step_1.md (~line 154), add an instruction to record in the commit body and PR description that the npm template anchor is `toolkits.md#npm`, not `#command-toolkit` as the issue states, so the #1198 follow-up links to `#npm`.', "In pr_info/steps/step_1.md (~line 203) and pr_info/steps/step_2.md (~line 163), update the expected result of the `(?i)proposed|will be|until ` verification so it allows matches in links to the transitional section (e.g. link text 'Until the next breaking release') as well as the heading. Otherwise the check fails falsely."], escalate_reason=None)
**Changes**:
applied

## Round 3 — 2026-11-11
**Findings**:
Checking the README and architecture.md passages Step 3 edits against the plan's verification patterns.NO FINDINGS
**Decisions**:
Verdict(decision='dismiss', tasks=[], escalate_reason=None)
**Changes**:
dismiss
