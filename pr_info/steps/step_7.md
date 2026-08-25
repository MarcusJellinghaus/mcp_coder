# Step 7 — Documentation

**Depends on:** Step 4 (the default must actually be `project_dir` before docs say so).
Independent of Steps 5 and 6.

Requirement 7 of the issue. Docs only — no source changes, no new tests.

**After this step, run the two remaining manual actions in
[summary.md](summary.md#manual-actions-no-commits--schedule-around-the-code-steps): repeat the
marker probe, and clean the Jenkins tool env.**

---

## WHERE

### 1. `docs/architecture/architecture.md`

**`:124-144` — "Execution Context Management".** The section documents the default as "Uses
shell's current working directory" (`:136`) and builds the whole "Context Separation Pattern"
(`:124`) on it. The worked example at `:139-144` is now actively wrong:

```bash
cd /home/user/workspace  # Has .mcp.json
mcp-coder implement --project-dir /path/to/project
# Claude runs in workspace, modifies project files
```

Claude no longer runs in the workspace. Rewrite so that:
- Default is stated as `project_dir`.
- The reason is stated: **Claude Code discovers `CLAUDE.md` by walking up from its own working
  directory and has no flag for it — cwd is the only lever.** This is the fact whose absence
  caused #1113 and it belongs in the architecture doc, not just in a changelog.
- `--execution-dir` is described as a deprecated override (removal tracked in #1132).
- The "Benefits" list at `:146-149` is revised — "Share MCP configurations across multiple
  projects" via cwd discovery is the one behaviour genuinely lost (see summary.md §6). Say so
  rather than deleting it silently; note that `--mcp-config`, `--settings` and `--project-dir`
  cover the CI/CD case.
- Record the family: #977 (`--mcp-config`), #981 (settings), #1113 (`CLAUDE.md`) — three
  instances of the same anchoring bug, all now project-anchored.

**`:325` — Scenario 4.** Builds a worked example on
`mcp-coder implement --project-dir /project --execution-dir /workspace`, which is now the
deprecated path. Either rewrite it around the default (cwd == project_dir) or keep it as an
explicit-override illustration that is clearly labelled deprecated. Steps `:326-331` still hold
mechanically; only the flag and the framing change.

### 2. `docs/cli-reference.md`

**`:175`** currently reads:
```
- `--execution-dir PATH` - Working directory for Claude subprocess (default: current directory)
```
This is the same stale statement being corrected in `architecture.md:136`.

**Nine further bullets** at lines **219, 264, 293, 332, 365, 395, 426, 462, 690** describe
`--execution-dir` as "Working directory for Claude subprocess" with no default and no
deprecation note.

**Make all ten identical** — one canonical sentence, reused verbatim, e.g.:
```
- `--execution-dir PATH` - **Deprecated** (removal tracked in #1132). Working directory for Claude subprocess. Default: `--project-dir`. See [Execution Context Management](architecture/architecture.md#execution-context-management).
```
The full explanation lives once in `architecture.md`; the bullets link to it rather than each
carrying bespoke wording. Verify the anchor resolves.

### 3. `docs/environments/environments.md`

The doc covers the two-environment split thoroughly — tool env vs project env, every
`MCP_CODER_*` variable, who sets what — but **never mentions that the working directory selects
the agent's coding rules.** That omission is the source of this whole class of surprise and is
the single most valuable line in this step.

Add a short section (a good home is after "Who Sets the Environments?" / the Entry Point
Matrix). It should state:

- Claude Code discovers `CLAUDE.md`, and project-level `.claude/settings*.json`, by walking up
  from its own working directory.
- mcp-coder therefore launches Claude with `cwd = project_dir` — the driven project's rules,
  not the tool env's.
- **The concrete trap:** the Jenkins templates run `cd %VENV_BASE_DIR%`
  (`command_templates.py:49`, `:242`, `:280`, `:318`, `:356`, `:394`) purely to activate a
  virtualenv. Before #1113 that shell-plumbing step silently also selected whose coding rules
  the agent obeyed — two unrelated concerns coupled through one inherited variable.
- A `.claude/CLAUDE.md` staged in the **tool env** is not read by driven projects and should not
  exist. Keep `.mcp.json` there: the coordinator smoke test
  (`command_templates.py:88-89`) runs `claude --mcp-config .mcp.json` from that directory.
  `tools/install.py:17` leaves both to the caller — no code in this repo creates them.

Cross-link to `architecture.md`'s Execution Context Management section.

### 4. `docs/repository-setup/claude-code.md` — "Pinning the settings file with `--settings`"

`:193-208` explains why `--settings` exists, and gives two causes for Claude discovering the
wrong settings file: *"because `--execution-dir` differs from `--project-dir`, or the workflow
was invoked from a parent directory"*. **The second cause no longer exists** — that was #1113,
and the default is now `project_dir`. Left as-is, this paragraph documents the bug as if it were
still current behaviour.

- Rewrite the two causes: the remaining one is an explicitly passed (deprecated)
  `--execution-dir`. Keep the section — `--settings` still earns its place, because it pins the
  file rather than relying on discovery, and because the symptom list at `:200-202` is still
  accurate for the `--execution-dir` case.
- **This is also the carrier for the settings-merge side effect** (summary.md §6). State it here,
  in the docs, rather than deferring it to a release note — this repo has no CHANGELOG and no
  step produces one, so an unwritten release note is not a place anything lands. Wording to
  cover: with `cwd == project_dir`, Claude Code now *also* discovers
  `<project_dir>/.claude/settings.json` and `settings.local.json` by its own cwd walk and merges
  them with the single file passed via `--settings`. `resolve_claude_settings_path` passes only
  one of the two (`cli/utils.py:330-341` prefers `settings.local.json`), so **a project holding
  both files newly activates the shared `settings.json`** that was previously inert. Intended,
  not a regression — but a rollout surprise if undocumented.
- Same note applies to the copilot provider, whose `_read_settings_allow`
  (`llm/providers/copilot/copilot_cli.py:230-241`) reads
  `<execution_dir>/.claude/settings.local.json` and therefore now reads the driven project's
  file. One sentence.

### 5. `docs/configuration/claude-code.md:123-128`

The `--settings` pinning callout says it is "Useful when `--execution-dir` differs from
`--project-dir`". Update to name the deprecation (#1132) and the new default, and keep the
cross-link to the rewritten section 4 above. One paragraph, no new content — the explanation
stays single-sourced in `repository-setup/claude-code.md` and `architecture.md`.

## WHAT / HOW / ALGORITHM / DATA

Not applicable — prose only. No code, no signatures, no data structures.

## TESTS

None. Verify by reading: every `--execution-dir` mention across `docs/` states the new default
and the deprecation, and no doc still claims the default is the current directory.

```
search_files(pattern="execution-dir|execution_dir", glob="docs/**/*.md")
search_files(pattern="current working directory|current directory", glob="docs/**/*.md")
```

The first search returns exactly 14 hits today, in five files:
`docs/cli-reference.md` (10), `docs/architecture/architecture.md` (2),
`docs/configuration/claude-code.md:126` (1), `docs/repository-setup/claude-code.md:198` (1).
All five files are in the WHERE scope above — if the search turns up a sixth, treat it as in
scope rather than deferring it.

Confirm the ten `cli-reference.md` bullets are byte-identical to each other.

## CHECKS

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Docs-only commits still run the gates — some tests assert on documented CLI help strings.

Then `./tools/format_all.sh`, review the diff, commit.

## Commit message

```
Document that Claude's working directory selects the project's rules (#1113)

architecture.md and cli-reference.md stated the execution-dir default as the
shell's current directory; it is now project_dir. environments.md documented
the two-environment split without ever mentioning that cwd selects which
CLAUDE.md the agent obeys - the omission behind this whole class of surprise.

repository-setup/claude-code.md still named "invoked from a parent directory"
as a cause of wrong settings discovery - that cause is gone - and now carries
the intended side effect: with cwd == project_dir, Claude also cwd-discovers
<project_dir>/.claude/settings.json and merges it with the --settings file.
```

---

## LLM PROMPT

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_7.md`, then implement Step 7. Docs
> only — do not change any source file.
>
> Five files:
>
> 1. `docs/architecture/architecture.md` — rewrite "Execution Context Management" (`:124-144`)
>    so the default is `project_dir`, `--execution-dir` is a deprecated override (#1132), and
>    the reason is stated explicitly: **Claude Code discovers `CLAUDE.md` by walking up from its
>    own working directory and has no flag for it, so cwd is the only lever.** The worked
>    example at `:139-144` currently says "Claude runs in workspace" and is now wrong. Revise
>    the Benefits list at `:146-149` — note that workspace `.mcp.json` discovery via cwd is the
>    one behaviour genuinely lost. Record the family: #977, #981, #1113. Also update Scenario 4
>    at `:325`, which is built on `--execution-dir /workspace`.
>
> 2. `docs/cli-reference.md` — replace `:175` and the nine bullets at 219, 264, 293, 332, 365,
>    395, 426, 462, 690 with **one identical canonical sentence** stating the deprecation, the
>    new default, and a link to the architecture section. Confirm the anchor resolves and the
>    ten bullets are byte-identical.
>
> 3. `docs/environments/environments.md` — add a short section stating that Claude's working
>    directory selects the agent's rules, that mcp-coder therefore launches it at
>    `project_dir`, and that the Jenkins `cd %VENV_BASE_DIR%` step (`command_templates.py:49`
>    and five siblings) silently coupled virtualenv activation to rule selection before this
>    fix. Note that a `.claude/CLAUDE.md` staged in the tool env should not exist, while
>    `.mcp.json` there must stay for the coordinator smoke test
>    (`command_templates.py:88-89`).
>
> 4. `docs/repository-setup/claude-code.md:193-208` ("Pinning the settings file with
>    `--settings`") — it currently gives two causes for wrong settings discovery, and the second
>    ("the workflow was invoked from a parent directory") is exactly the bug this issue fixes.
>    Rewrite so the only remaining cause is an explicitly passed, deprecated `--execution-dir`.
>    **In the same section, document the settings-merge side effect**: with `cwd == project_dir`,
>    Claude now also cwd-discovers `<project_dir>/.claude/settings.json` and
>    `settings.local.json` and merges them with the single file passed via `--settings`, so a
>    project holding both newly activates the shared `settings.json`. Intended, not a regression.
>    Add one sentence that the copilot provider's `_read_settings_allow`
>    (`llm/providers/copilot/copilot_cli.py:230-241`) likewise now reads the driven project's
>    `settings.local.json`. This section is the user-facing carrier for that side effect — there
>    is no CHANGELOG in this repo, so do not defer it to a release note.
>
> 5. `docs/configuration/claude-code.md:123-128` — the `--settings` callout says it is "Useful
>    when `--execution-dir` differs from `--project-dir`". State the deprecation (#1132) and the
>    new default, and keep the cross-link to file 4. One paragraph; do not duplicate the
>    explanation.
>
> Verify with `search_files` that no doc still documents the default as the current directory,
> and that all 14 `--execution-dir` mentions across `docs/` (10 in `cli-reference.md`, 2 in
> `architecture.md`, 1 each in the two files above) carry the new default and the deprecation.
>
> Use MCP tools for all file operations. Run `run_pylint_check`, `run_pytest_check` (with
> `-n auto` and the integration-marker exclusions from summary.md) and `run_mypy_check` — some
> tests assert on documented CLI help strings. One commit.
>
> **After committing, tell the user the two manual actions from summary.md are now due: repeat
> the marker probe (the marker must be gone and the repo's own rules present), and delete
> `C:\Jenkins\environments\mcp-coder-dev\.claude\` while keeping `.mcp.json` there.**
