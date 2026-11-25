# Step 2 — Step-to-request table, grants, `verify` and formatting text

## LLM prompt

> Read `pr_info/steps/summary.md`, then this file. Implement Step 2 only:
> - add the step-to-request table to `docs/configuration/toolkits.md` and fix
>   that page's stale rules and the npm example;
> - fix `docs/architecture/toolkit-interface.md`;
> - fix the `### rebase` and `### verify` sections of `docs/cli-reference.md`;
> - fix `docs/architecture/architecture.md`.
>
> Docs only. Check each statement against the source files named below. Run the
> checks at the end, then make one commit.

## WHERE

- `docs/configuration/toolkits.md`
- `docs/architecture/toolkit-interface.md`
- `docs/cli-reference.md` (`### rebase` and `### verify` only)
- `docs/architecture/architecture.md`

Sources to check against:

- `utils/toolkit_runner.py::DEFAULT_BINDINGS`
- the `run_formatters` call sites:
  - `workflows/implement/core.py`
  - `workflows/implement/task_processing.py`
  - `workflows/implement/check_loop.py::rescue_commit`
  - `workflows/rebase.py`
  - `workflows/review/core.py`
  - `workflow_steps/ci.py`
- the `llm_permissions` call sites:
  - `implement/task_processing.py`
  - `implement/check_loop.py`
  - `implement/finalisation.py`
  - `workflow_steps/ci.py`
  - `workflows/rebase.py`
- `cli/commands/verify_toolkit_rows.py`
- `llm/providers/claude/claude_code_cli.py::build_cli_command`

## WHAT — `docs/configuration/toolkits.md`

1. **"Configure a toolkit".** "in `pyproject.toml` or, for repos without one, a
   root `mcp-coder.toml`" → "in `pyproject.toml` or a root `mcp-coder.toml`
   (any repo)". Keep the "Location" rule under `## [tool.mcp-coder.toolkit]`
   as it is.
2. **Bindings table, `commit` row, "Used by".** "formatting before commits:
   implement, rebase, review, CI fix, and the rescue commit after a check-stage
   abort".
3. **Bindings rule on `commit`.** "`commit` runs only when `format_code` is on
   (the default). `format_code` is read from `pyproject.toml` or
   `mcp-coder.toml` ([Project config](project-config.md))." Delete "read from
   `pyproject.toml` only … `commit = []`".
4. **Bindings rule on `mcp-coder verify`.** Rewrite:
   - It calls `verify()` for every action a non-empty binding requests
     (`format` only while `format_code` is on).
   - It shows an ok row for each declared depth a binding runs (fallback
     included), naming those bindings.
   - It adds a row per requested depth the toolkit doesn't declare: a warning
     naming the lower depth that runs, else an error.
   - Command toolkit only: it warns about a declared depth that is "not
     requested by any binding", that "no binding can request", or that is
     "unused while format_code is off".
   - Keep the grouping and severity rule that follows unchanged.
5. **New `### Step-to-request table`,** directly after the Bindings rules and
   before `## Required MCP servers`. Use the table from issue decision 4
   verbatim, with columns `Workflow step | Binding run | Default requests |
   Bash grant scope`. Below it, a short note:
   - No toolkit grants → Bash is off for the session (`build_cli_command` adds
     it only with grants), so the repo's own Bash rules don't apply either.
     This applies to mcp-coder's own Claude sessions; vscodeclaude's interactive
     session runs under the repo's Claude settings.
   - A request that falls back grants the lower depth's steps.
   - The Bash grant scope column applies to the command toolkit; mcp-tools-py
     passes no per-session `Bash(...)` grants.
   - Every other commit runs without formatting, e.g. finalisation,
     `mcp-coder commit`, create_plan, create-pr's cleanup commit, review's
     round-log commit, task-tracker prep, and the git-only rebase step's
     line-ending renormalize commit.
6. **"LLM access → Which sessions".** Replace the four session sub-bullets and
   the fallback sentence with one sentence: the sessions and their scopes are
   in the [Step-to-request table](#step-to-request-table). Keep:
   - the re-run list in the prompt names exactly the granted commands;
   - other sessions keep Bash off;
   - Copilot and Langchain get no grants and log a warning once.
7. **Defaults rule on `format.apply`.** "…which fails formatting: implement
   fails; rebase, review, CI fix and the rescue commit carry on."
8. **Errors bullet on `mcp-coder verify`.** Same content as item 4, in short:
   the declared-depth ok rows, the undeclared-depth rows, and the three
   command-toolkit warnings. Link [Bindings](#bindings) for the details.
9. **npm example:**
   - `test.quick` → `argv = ["npm", "run", "test"]`;
   - in the grant sentence, `Bash(npm test)` → `Bash(npm run test)`;
   - add bullets after the example:
     - Every `parser = "junit"` step (`test` and `test:ci`) must run a reporter
       that writes `reports/junit.xml`. The toolkit deletes the report before
       each step and reports a missing one as `error`, so failing tests would
       show as `error`, not `findings`.
     - Gitignore `reports/`: mcp-coder stages all changes when it commits, and
       its clean-tree checks ignore only `uv.lock`.
10. **"Formatting off".** Either `[tool.mcp-coder] format_code = false` (either
    file) or `commit = []`. In both cases leave out the `format` table:
    otherwise, with the command toolkit, `verify` warns about the declared
    `format.apply` ("unused while format_code is off" or "not requested by any
    binding"). Show both snippets.

## WHAT — `docs/architecture/toolkit-interface.md`

- **`### LLM permissions`.** Replace the whole three-row table with one line:
  "Which session gets which grants:
  [Step-to-request table](../configuration/toolkits.md#step-to-request-table)."
  Keep the bullets below it.
- **`### Verify`, the `mcp-coder verify` bullet.** "calls
  `verify(project_dir, action)` once per action a non-empty binding requests
  and the toolkit declares (`commit` counts only with `format_code` on), then
  adds the depth rows. Rows, grouping and severities:
  [Bindings](../configuration/toolkits.md#bindings)."
- **Formatting table, "Any other status" row.** "implement fails; rebase,
  review, CI fix and the rescue commit carry on".

## WHAT — `docs/cli-reference.md` (no `--flag` names in new text)

- **`### rebase`, first paragraph.** Replace "…passing the detected base
  explicitly and a pytest marker filter that skips…" with: "…passing the
  detected base explicitly; that automated rebase runs the `rebase_automated`
  binding, `mcp-coder rebase` the `rebase` binding."
- **`### rebase`, the "regression check … 1800 s … `sys.executable`"
  paragraph.** Replace it with: "The checks before and after the rebase are the
  binding's requests (by default, an automated rebase tests at
  `test@unattended`); see
  [Bindings](configuration/toolkits.md#bindings). Their timeouts, and the
  interpreter tests run in, come from the toolkit:
  [mcp-tools-py](configuration/toolkits.md#mcp-tools-py),
  [command toolkit](configuration/toolkits.md#defaults)."
- **`### verify`.** It also reports `[tool.mcp-coder]` keys: unknown keys,
  retired keys and keys in the wrong file. Most appear in the project section;
  unknown `prompts` keys and `prompts` defined in both files appear in
  `PROMPTS`. Link `configuration/project-config.md#checked-by-verify`.

## WHAT — `docs/architecture/architecture.md`

In the "Target repos" bullet: "declares its setup steps in `pyproject.toml` or
`mcp-coder.toml` (and, for Python, install extras and sibling pins in
`pyproject.toml`)".

## ALGORITHM (checks before commit)

```
search docs/ for "Union of all `Bash(...)` grants"  -> must be 0 hits
search docs/ for "pytest marker filter", "1800 s timeout" in cli-reference  -> 0
search docs/ for "toolkits.md#step-to-request-table" -> heading exists in toolkits.md
search docs/ for "#bindings", "#npm", "#defaults", "#mcp-tools-py" -> headings unchanged
run tests/docs (cli-reference flag test)
```

## DATA

None (docs only).

## Checks, then commit

- `mcp__mcp-tools-py__run_pytest_check(extra_args=["-n", "auto", "tests/docs"])`
- `run_pylint_check`, `run_mypy_check`
- `run_format_code`, then `git_commit` with `paths` listing the four files.
  Message:
  `docs: add step-to-request table, fix grant/verify/formatting statements (#1453)`.
