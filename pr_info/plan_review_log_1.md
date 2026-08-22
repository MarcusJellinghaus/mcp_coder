# review-plan review log 1

## Round 1 — 2026-08-23
**Findings**:
I'll gather context systematically. Starting with the knowledge base, the issue, and the plan files.`pr_info/steps/step_1.md:97` — medium — `open("a", encoding="utf-8")` keeps default newline translation, so on Windows the appended block is written CRLF into an otherwise-LF `.gitignore`, and in the no-trailing-newline case the last *existing* line gains a CRLF terminator; this is the artifact the issue's "line endings elsewhere in the file must not change" requirement targets, and `newline=""` is a one-token fix the plan does not consider (summary.md declares only *dominant-ending matching* out of scope, not this).

`pr_info/steps/step_1.md:106` — medium — no test covers the issue's headline "content already in the file is never rewritten / line endings must not change" requirement; both new tests read via `read_text`, whose universal-newline translation hides exactly the line-ending behaviour being claimed. A `read_bytes()` assertion that a pre-existing `b"*.pyc\n"` prefix survives unchanged would cover it.

`pr_info/steps/step_2.md:116` — medium — the issue requirement "Init reports what it did — how many entries were added, or that the file was already up to date" is implemented (`Gitignore: %d entries added`) but no test asserts that line; tests A/B/C only cover file content, exit code and the `.git` warning.

`pr_info/steps/step_2.md:159` — medium — the prescribed `caplog.at_level(logging.WARNING, ...)` is above the custom `OUTPUT` level, so any assertion on the `Gitignore:` report line silently cannot match; reporting assertions need `at_level(OUTPUT)` (or INFO) on `mcp_coder.cli.commands.init`.

`pr_info/steps/step_2.md:99` — low — `.git` is probed only directly under `project_dir`, so `--project-dir <subdir-of-a-repo>` (a supported flag combination) emits a misleading "has no .git/ directory" warning.

`pr_info/steps/step_3.md:10` — low — docs step updates only `docs/`; `COMMAND_DESCRIPTIONS["init"]` and the `--just-skills` help string ("Deploy skills only, skip config creation") stay silent about the gitignore step even though it now runs in that mode, against the knowledge-base rule that CLI commands are documented via help text *and* `docs/`.
**Decisions**:
Verdict(decision='tasks', tasks=['In step_1.md:97, open the .gitignore for appending with newline="" (e.g. open(path, "a", encoding="utf-8", newline="")) so Python does not translate the written \\n to \\r\\n on Windows, and make the missing-trailing-newline path append the same literal \\n; this preserves the issue requirement that line endings elsewhere in the file must not change.', 'In step_1.md:106, add a test that writes a .gitignore with pre-existing content (e.g. b"*.pyc\\n") and asserts via read_bytes() that the pre-existing byte prefix is unchanged after the append and that the newly appended block uses \\n terminators — do not use read_text(), whose universal-newline translation masks the behaviour under test.', "In step_2.md:116, add a test asserting the init command's reporting output for the gitignore step: both the 'Gitignore: <n> entries added' line for the added-entries case and the already-up-to-date variant, so the issue's 'Init reports what it did' requirement is covered.", 'In step_2.md:159, change the prescribed caplog.at_level(logging.WARNING, ...) to caplog.at_level(OUTPUT, logger="mcp_coder.cli.commands.init") (or INFO) for any test asserting the \'Gitignore:\' report line, since the custom OUTPUT level is below WARNING and those records would otherwise never be captured.'], escalate_reason=None)
**Changes**:
applied
