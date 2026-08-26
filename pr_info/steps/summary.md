# Summary — Issue #1113: Headless runs get the wrong CLAUDE.md

## Problem

Claude Code discovers `CLAUDE.md` by walking up from **its own working directory**. There is
no flag for it — cwd is the only lever.

mcp-coder launches Claude with `cwd = execution_dir`
(`llm/providers/claude/claude_code_cli_streaming.py:154`), and `execution_dir` defaults to
`Path.cwd()` (`cli/utils.py:372-373`) — the *shell's* directory, never `project_dir`.

On Jenkins the shell sits in the tool env (`C:\Jenkins\environments\mcp-coder-dev`) while the
code lives elsewhere (`C:\Jenkins\workspace\...\repo`). Separate trees. So every headless run
obeys a stale predecessor project's `CLAUDE.md` — one that instructs the agent to call
`mcp__filesystem__*` / `mcp__code-checker__*`, servers renamed long ago — and the driven
project's own rules never arrive. Locally it works only by coincidence: developers stand in
the repo, so cwd happens to equal `project_dir`.

This is the third instance of one pattern: **#977** (`--mcp-config` resolved against cwd),
**#981** (Claude settings discovered via cwd), **#1113** (`CLAUDE.md` discovered via cwd).
Each time something that should be anchored to `project_dir` was anchored to the shell.

## Architectural / design changes

### 1. The anchor moves from the shell to the project

`resolve_execution_dir` gains an optional `project_dir` parameter and uses it as the default,
mirroring `resolve_mcp_config_path` and `resolve_claude_settings_path`, which took this same
fix in #977 and #981. After this change all three cwd-sensitive inputs — MCP config, Claude
settings, project instructions — are anchored to the same place.

```
before:  cwd(shell) ──> Claude subprocess cwd ──> CLAUDE.md discovery
after:   project_dir ─> Claude subprocess cwd ──> CLAUDE.md discovery
```

The design point is not "pick a better default" but **decide at all**. Today the Jenkins
templates' `cd %VENV_BASE_DIR%` (`command_templates.py:49` and five siblings), a step whose
only intent is activating a virtualenv, silently also selects whose coding rules the agent
obeys. Two unrelated concerns coupled through one inherited variable. This decouples them.

**`--execution-dir` survives as an explicit override** with a deprecation warning naming
#1132, which removes it entirely.

### 2. Deliberate non-validation of the default

The `project_dir` default is `.resolve()`d but **not** existence-checked. Two reasons:
`commit.py:80` builds `Path(args.project_dir)` without `.resolve()`, so a relative
`--project-dir sub` must not reach the subprocess as a relative cwd; and skipping the check
preserves `commit.py`'s error ordering, where `validate_git_repository` (`:83`) produces the
message for a bad `project_dir` rather than "Execution directory does not exist". The
existence check remains for a user-supplied `--execution-dir`, where a typo is likely.

### 3. Observability becomes a first-class concern

The durable half of this issue. Nothing ever reported which working directory Claude used or
which `CLAUDE.md` it loaded — a wrong memory file and a right one are indistinguishable from
outside the process, which is why this drifted silently since December.

Three new functions in `cli/utils.py` report, once per run at `OUTPUT` level, the Claude working
directory and the cwd-upward `CLAUDE.md` walk, **warning when none of the resolved files lies
inside `project_dir`**. That warning is the line that would have caught this in December; a bare
resolved path is too easy to skim past. The predicate is the absence of an inside hit rather than
the presence of an outside one: the walk reaches every ancestor, so individual outside files are
the norm and warning on each would cry wolf on almost every run.

`is_outside_project_dir` is the **single** definition of "outside", shared by the run-time report
(Step 3) and the verify report (Step 5) so the two cannot drift on the one rule the issue calls
load-bearing. `find_context_claude_md` takes an optional `stop_at` walk boundary used only by
tests — without it, "found nothing anywhere" is unassertable, because the walk runs to the
filesystem root and `tmp_path`'s real ancestors are outside any test's control.

**Design decision (deviation from the issue, deliberate):** the issue specifies "a small
dedicated helper called next to each `resolve_execution_dir`" — nine wiring points. Instead
the helper is called *from inside* `resolve_execution_dir`. The issue supplies this reasoning
itself for the deprecation warning ("belongs in `resolve_execution_dir` itself — one edit
covers all nine commands"); the argument is identical for reporting, and it makes it
structurally impossible for a call site to forget. The helper stays a separate, unit-testable
function — only the wiring is centralised. Requirement 5's actual constraint (**not**
`log_command_startup`, which only 4 of 9 commands call and which logs at `info`) is honoured.
Cost, stated plainly: a function named "resolve" now emits `OUTPUT`-level output. It already
logged at `debug` and will now also warn, so it was never pure.

`verify.py` is the one genuine second call site — it bypasses the resolver entirely, passing
`str(project_dir)` straight to `prompt_llm` (`:575`, `:597`). That is also why verify could
never reproduce this bug: it always exercised the correct working directory while the
workflows did not.

### 4. Shared candidate knowledge, not a shared walk

**Design decision (deviation from the issue, deliberate — see "Open decision" below):** the
issue proposes extracting `_claude_md_candidates(start) -> Iterator[list[Path]]` (one group
per ancestor level) and rewriting `is_claude_md` over it. This plan extracts one level
smaller instead:

```python
def claude_md_paths(directory: Path) -> list[Path]:
    return [directory / "CLAUDE.md", directory / ".claude" / "CLAUDE.md"]
```

Both `is_claude_md` and the new finder use it, so the *location knowledge* lives in exactly
one place — which is what the issue's constraint protects against. But `is_claude_md` keeps
its `while` loop, its early-return-per-candidate structure and its `try/except OSError` guard
literally intact (a ~3-line diff), instead of being restructured around a generator. It has
three consumers (`llm/interface.py:63`, `verify.py:365`, the new finder), and the issue spends
a paragraph explaining how easily its membership semantics break. The smallest possible diff
is the safest way to honour that.

The finder writes its own six-line ancestor walk. Public name (no underscore) because two
modules import it.

### 5. What the report does and does not claim

Scope is the cwd-upward walk only: `<dir>/CLAUDE.md` and `<dir>/.claude/CLAUDE.md`, up to the
filesystem root. That **includes** user-level `~/.claude/CLAUDE.md` whenever the working
directory sits under the home directory, because Claude loads it and reporting what Claude
actually loads is the point. It does **not** expand `@import` directives, so the label must
still be worded so it does not claim to be a complete account of Claude's memory chain.

**Every** hit at **every** ancestor level is named — Claude loads the whole chain, not the
nearest file — and never one picked by precedence. The ordering inside `is_claude_md` is a
membership test and was never load-bearing; treating it as precedence would invent a fact.

### 6. Side effects that are intended, not regressions

- **Claude settings merge.** With `cwd == project_dir`, Claude also discovers
  `<project_dir>/.claude/settings.json` and `settings.local.json` and merges them with the one
  file passed via `--settings`. `resolve_claude_settings_path` passes only one of the two, so a
  project holding both newly activates the shared file. This is the intent of the issue, but it
  must be written down rather than discovered during rollout. **Carrier: Step 7**, in
  `docs/repository-setup/claude-code.md`'s "Pinning the settings file" section — not a release
  note, since this repo has no CHANGELOG and no step produces one.
- **Copilot settings discovery moves too.** `_read_settings_allow`
  (`llm/providers/copilot/copilot_cli.py:230-241`) reads
  `<execution_dir>/.claude/settings.local.json`, so it now reads the driven project's file.
- **Skills and agents stay inert.** `--tools ToolSearch` (`claude_code_cli.py:46`) exposes no
  `Skill` or `Task` tool.
- **Stream logs do not move.** `get_stream_log_path` prefers `logs_dir` over `cwd`, and
  `logs_dir` derives from `MCP_CODER_PROJECT_DIR`. Recorded so nobody hunts a log-location
  regression that cannot occur.
- **One behaviour is genuinely lost:** a project with no `.mcp.json` of its own picking one up
  from the workspace via Claude's cwd discovery. It only fires when mcp-coder resolves no
  config from any of its four sources. Since #977 made every other path project-anchored, this
  is a leftover rather than a feature. If it must be preserved, add the directory as a fifth
  fallback inside `resolve_mcp_config_path` — do not retain cwd plumbing for it.
- **One-time resume break, accepted.** Claude keys native sessions by cwd
  (`~/.claude/projects/<slug>`), so session ids stored before the change will not resume. No
  headless workflow resumes across invocations; `.mcp-coder/*_sessions` files are written at
  ten sites and read back by nothing. Only interactive `prompt --continue-session*` and
  `icoder --continue-session` are exposed, and only when run from outside the repo with
  `--project-dir`. A developer standing in the repo sees no break. The risk that a failed
  `--resume` is *silent* is pre-existing and tracked as **#1134**.

### 7. Explicitly out of scope

- Removing `--execution-dir` → **#1132** (blocked on this).
- Injecting `CLAUDE.md` or prompts into headless workflows — reverses a documented decision
  (`docs/repository-setup/python.md`), touches ~10 call sites, its own issue.
- `--add-dir` — built-in file tools are disabled, so its only possible effect here is an
  undocumented memory-loading behaviour that could change silently. Rejected.
- Detecting a session-id mismatch on resume → **#1134**.
- Normalising the ten `execution_dir=... if ... else None` fallbacks in the workflows — they
  become unreachable from the CLI once the default changes, and #1132 deletes the parameter.
- The `is_claude_md` skip at `llm/interface.py:60-63` — reached only when `prompt_llm` receives
  a `project_dir`, which only `prompt --add-system-prompts` and icoder do. Once the default is
  `project_dir`, `cwd == project_dir` holds unless `--execution-dir` is passed, which nothing
  does.

## Manual actions (no commits — schedule around the code steps)

**BEFORE Step 1 — pre-flight probe. This gates the whole implementation.**
Requirement 1 of the issue. Cannot be automated; it validates the load-at-session-start claim
the entire fix rests on, and produces the "before" half of the acceptance evidence.

1. Create a scratch directory outside the repo with a `CLAUDE.md` containing a unique marker
   sentence (e.g. an instruction to call a made-up tool `mcp__marker_probe__ping`).
2. `cd` into that scratch directory.
3. Run `mcp-coder prompt --project-dir <repo> "Quote verbatim any instruction you received
   about which tools to use."`
4. **Confirm the marker comes back.** If it does not, stop — the premise is wrong and the fix
   route needs rethinking before any code is written.

**AFTER Step 7 — repeat the probe.** The marker must now be *absent* and the repo's own rules
present. This is the acceptance evidence; no automated check can observe Claude's internal
memory loading.

**AFTER Step 7 — clean the Jenkins tool env.** Delete
`C:\Jenkins\environments\mcp-coder-dev\.claude\`. **Keep `.mcp.json` there** — the coordinator
smoke test (`command_templates.py:88-89`) runs `claude --mcp-config .mcp.json` from that
directory. No code in this repo creates the `.claude/` staging (`tools/install.py:17` leaves it
to the caller). The code fix makes the stale file harmless either way; removing it stops it
misleading anyone reading the machine.

## Steps

| # | Step | Commit contains |
|---|---|---|
| 1 | [`claude_md_paths()` + `is_claude_md` refactor](step_1.md) | shared candidate knowledge, no behaviour change |
| 2 | [`resolve_execution_dir` signature + deprecation](step_2.md) | new optional param, warning; backwards compatible |
| 3 | [Context-root finder + reporter](step_3.md) | `find_context_claude_md`, `is_outside_project_dir`, `report_context_root`, wired into the resolver; `tach.toml` |
| 4 | [Nine call sites default to `project_dir`](step_4.md) | **the behaviour change** + help text + 14 test updates + two `cwd == project_dir` tests (one CLI-free, one at the subprocess) |
| 5 | [`verify` reports the same](step_5.md) | PROMPTS section rows, new test module |
| 6 | [Branch-name call sites](step_6.md) | `task_processing.py` two lines |
| 7 | [Docs](step_7.md) | architecture, cli-reference, environments, both claude-code docs |

Ordering: Step 3 depends on Steps 1 and 2; Step 4 depends on Steps 2 and 3. **Steps 1 and 2 are
independent of each other** — either may be committed first; the numbering is presentational.
Steps 5, 6 and 7 depend on Step 3, Step 4 and Step 4 respectively, but are independent of each
other. Every step is gated on the pre-flight marker probe below.

## Folders / modules / files

### Created

- `pr_info/steps/summary.md`, `pr_info/steps/step_1.md` … `step_7.md` (this plan)

**No new source modules.** Every source change lands in an existing file — a deliberate KISS
outcome of the two design decisions above. One new *test* module
(`tests/cli/commands/test_verify_prompts_context.py`, Step 5) and one `tach.toml` line
(Step 3) are the only additions.

### Modified — source (14 files)

| File | Step | Change |
|---|---|---|
| `src/mcp_coder/prompts/prompt_loader.py` | 1 | `claude_md_paths()`; `is_claude_md` uses it |
| `src/mcp_coder/cli/utils.py` | 2, 3 | `resolve_execution_dir` signature + deprecation; `find_context_claude_md`, `is_outside_project_dir`, `report_context_root` |
| `tach.toml` | 3 | allow `mcp_coder.cli` → `mcp_coder.prompts` |
| `src/mcp_coder/cli/shared_args.py` | 4 | `_EXECUTION_DIR_HELP` |
| `src/mcp_coder/cli/commands/check_branch_status.py` | 4 | **hoist out of the `--fix` block** + pass `project_dir` (`:189`, `:331`) |
| `src/mcp_coder/cli/commands/commit.py` | 4 | **reorder** + pass `project_dir` (`:74`, `:80`) |
| `src/mcp_coder/cli/commands/create_plan.py` | 4 | pass `project_dir` (`:46`) |
| `src/mcp_coder/cli/commands/create_pr.py` | 4 | pass `project_dir` (`:46`) |
| `src/mcp_coder/cli/commands/icoder.py` | 4 | **reorder** + pass `project_dir` (`:51`) |
| `src/mcp_coder/cli/commands/implement.py` | 4 | pass `project_dir` (`:46`) |
| `src/mcp_coder/cli/commands/prompt.py` | 4 | **reorder** + pass `project_dir` (`:48`) |
| `src/mcp_coder/cli/commands/rebase.py` | 4 | pass `project_dir` (`:81`) |
| `src/mcp_coder/cli/commands/review.py` | 4 | pass `project_dir` (`:84`) |
| `src/mcp_coder/cli/commands/verify.py` | 5 | PROMPTS section rows (`:338-374`) |
| `src/mcp_coder/workflows/implement/task_processing.py` | 6 | branch name from `project_dir` (`:214-216`, `:434`) |

### Modified — tests (12 files)

| File | Step |
|---|---|
| `tests/prompts/test_prompt_loader.py` | 1 |
| `tests/cli/test_utils.py` | 2, 3 |
| `tests/cli/test_shared_args.py` | 4 |
| `tests/cli/commands/test_create_pr.py` | 4 |
| `tests/cli/commands/test_implement.py` | 4 |
| `tests/cli/commands/test_create_plan.py` | 4 |
| `tests/cli/commands/test_review.py` | 4 |
| `tests/cli/commands/test_check_branch_status.py` | 4 (assertions + the `--fix 0` hoist test) |
| `tests/cli/commands/test_commit.py` | 4 (comments + one resolver test) |
| `tests/cli/commands/test_prompt.py` | 4 (**the CLI-free `cwd == project_dir` test**, `:706`; plus rename the now-misleading `test_default_execution_dir_uses_cwd`, `:712`) |
| `tests/integration/test_execution_dir_integration.py` | 2, 4 (**incl. the subprocess-level `cwd == project_dir` test**) |
| `tests/workflows/implement/test_task_processing.py` | 6 |

**Created — tests (1 file)**

- `tests/cli/commands/test_verify_prompts_context.py` (Step 5). A new module rather than
  extending `test_verify.py`, which is already 727 lines and would cross the repo's 750-line
  guidance.

`tests/cli/commands/test_check_branch_status.py` and `test_rebase.py` also patch
`resolve_execution_dir` — they are not in the issue's list of 14, but **grep for
`assert_called_once_with` on those mocks in Step 4** rather than trusting the list.

### Modified — docs (5 files)

- `docs/architecture/architecture.md` (`:124-144` default + Context Separation Pattern example;
  `:325` Scenario 4)
- `docs/cli-reference.md` (`:175` plus bullets at 219, 264, 293, 332, 365, 395, 426, 462, 690)
- `docs/environments/environments.md` (new section: cwd selects the agent's rules)
- `docs/repository-setup/claude-code.md` (`:193-208` — drops "invoked from a parent directory"
  as a cause of wrong settings discovery, and carries the settings-merge side effect)
- `docs/configuration/claude-code.md` (`:123-128` — the `--settings` callout that justifies
  itself by `--execution-dir` differing from `--project-dir`)

Together these are all five files in `docs/` that mention `--execution-dir` (14 hits).

## Acceptance

- `mcp-coder implement --project-dir <repo>` launches Claude with `cwd == <repo>` from any
  shell working directory. Covered automatically by two Step 4 tests, both of which `chdir`
  outside the project directory first: `test_default_execution_dir_uses_project_dir`
  (`tests/cli/commands/test_prompt.py`, patches `prompt_llm_stream`, needs no Claude CLI, runs
  under the standard marker exclusions) and `test_prompt_command_defaults_cwd_to_project_dir`
  (`tests/integration/test_execution_dir_integration.py`, asserts the `cwd` handed to the
  subprocess, behind `require_claude_cli`).
- The subprocess `cwd` equals `project_dir`, and every reported project instructions file lies
  inside `project_dir`. That is the checkable proxy — whether the repo's `.claude/CLAUDE.md` is
  *actually* in effect is a claim about Claude Code's internal memory loading that nothing in
  this repo can observe. Evidenced by the marker probe, not by an automated check.
- `--execution-dir <dir>` still sets cwd to `<dir>` and emits a deprecation warning naming
  #1132.
- Run output names the Claude working directory and every project instructions file in effect
  at the nearest ancestor level that has any (resolved paths, or "none found"), and warns when
  any lies outside `project_dir`.
- `mcp-coder verify` reports the same.
- LLM log filenames carry the branch name when the command is run from outside the repo.
- `architecture.md` and `docs/environments/environments.md` state the new default and the cwd /
  `CLAUDE.md` relationship.

## Open decision for the reviewer

**Section 4 above departs from the issue's stated mechanism** (`claude_md_paths` returning one
directory's candidates, versus `_claude_md_candidates` yielding per-level groups). It preserves
the constraint's purpose — single source of location knowledge, untouched `is_claude_md`
semantics — with a materially smaller diff. If you prefer to match the issue literally, only
Step 1 changes; Steps 2-7 are unaffected either way.

## Quality gates (every step)

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

Steps 1 and 3 add cross-module imports (`cli/utils.py` → `prompts.prompt_loader`); also run
`mcp__tools-py__run_lint_imports_check` and `mcp__tools-py__run_tach_check` there.
`cli/commands/verify.py` already imports `prompt_loader`, so the *direction* is established
(`presentation` → `domain`) — but `mcp_coder.prompts` is **not** on the `mcp_coder.cli`
`depends_on` allowlist in `tach.toml`, so Step 3 adds it in the same commit as the import.

Run `./tools/format_all.sh` before every commit.
