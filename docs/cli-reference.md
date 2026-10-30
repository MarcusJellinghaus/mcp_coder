# CLI Reference

What each `mcp-coder` command is for, when to run it by hand, and what it does to your repository and issues.

For the complete option list of any command, run `mcp-coder <command> --help`. This page documents only what `--help` cannot say: purpose, prerequisites, behaviour, label effects and examples. A test (`tests/docs/test_cli_reference.py`) fails when a command is missing here, a table description drifts from the CLI, or a flag mentioned on this page does not exist.

`mcp-coder help` prints the same command overview grouped by category.

## Command List

### Setup

| Command | Description |
|---------|-------------|
| [`init`](#init) | Initialize project: create config and deploy Claude skills |
| [`install`](#install) | Install mcp-coder into a target environment |
| [`verify`](#verify) | Check config, git, GitHub, Jenkins, Claude CLI, LLM provider and MCP servers |

### Background development

Automated stages, normally dispatched by the coordinator. See the [Development Process](processes-prompts/development-process.md).

| Command | Description |
|---------|-------------|
| [`create-plan`](#create-plan) | Generate implementation plan for a GitHub issue |
| [`review-plan`](#review-plan) | Run automated review of an implementation plan |
| [`implement`](#implement) | Execute implementation workflow |
| [`rebase`](#rebase) | Automatically rebase the current branch onto its base branch |
| [`review-implementation`](#review-implementation) | Run automated review of an implementation |
| [`create-pr`](#create-pr) | Create pull request with AI-generated summary |
| [`fix-conflict`](#fix-conflict) | Rebase onto base branch to resolve a merge conflict |
| [`fix-ci`](#fix-ci) | Run the CI auto-fix loop to resolve a failing PR |
| [`coordinator`](#coordinator) | Monitor GitHub issues and dispatch automated workflows |

### Interactive development

| Command | Description |
|---------|-------------|
| [`icoder`](#icoder) | Interactive terminal chat for LLM-assisted coding |
| [`vscodeclaude launch`](#vscodeclaude-launch) | Launch VSCode/Claude session for issues |
| [`vscodeclaude status`](#vscodeclaude-status) | Show current VSCode/Claude sessions |

### Tools

| Command | Description |
|---------|-------------|
| [`prompt`](#prompt) | Send prompt to configured LLM |
| [`commit auto`](#commit-auto) | Auto-generate commit message using LLM |
| [`check branch-status`](#check-branch-status) | Check branch readiness status and optionally apply fixes |
| [`check file-size`](#check-file-size) | Check file sizes against maximum line count |
| [`gh-tool checkout-issue-branch`](#gh-tool-checkout-issue-branch) | Checkout or create a branch linked to a GitHub issue |
| [`gh-tool set-status`](#gh-tool-set-status) | Update GitHub issue workflow status label |
| [`gh-tool get-base-branch`](#gh-tool-get-base-branch) | Detect base branch for current feature branch |
| [`gh-tool define-labels`](#gh-tool-define-labels) | Sync workflow status labels to GitHub |
| [`gh-tool issue-stats`](#gh-tool-issue-stats) | Display issue statistics by workflow status |
| [`git-tool compact-diff`](#git-tool-compact-diff) | Generate compact git diff suppressing moved-code blocks |

## Global Options

```bash
mcp-coder --version                    # Show version information
mcp-coder --log-level LEVEL            # DEBUG, INFO, OUTPUT, WARNING, ERROR or CRITICAL; default OUTPUT, INFO for coordinator
mcp-coder help                         # Categorized command overview
```

## Common Options

Most commands share a few options. Their exact spelling is in each command's `--help`; this section explains how they behave.

- **`--project-dir PATH`**: the repository to act on (default: current directory). Always pass it when the shell is not inside the checkout, for example on a build server.
- **`--llm-method METHOD`**: `claude`, `copilot` or `langchain`. Without it, the `MCP_CODER_LLM_PROVIDER` environment variable, then `[llm] default_provider` in `config.toml`, then `claude` apply.
- **`--mcp-config PATH`** and **`--settings PATH`**: on the commands that run an agent session, such as `prompt`, `implement` and the reviews (check a command's `--help`). See below.

### Issue label and comment flags

The workflow commands `implement`, `create-plan`, `review-plan`, `review-implementation`, `create-pr` and `fix-ci` accept `--update-issue-labels` / `--no-update-issue-labels` (move the issue's status label on success or failure) and `--post-issue-comments` / `--no-post-issue-comments` (comment on the issue when the workflow fails).

Resolution order: the flag, then `update_issue_labels` / `post_issue_comments` in the matching `[coordinator.repos.*]` section of `config.toml` (matched by the checkout's git remote URL; both are `true` unless the section sets them to `false`), then `false` for a checkout with no matching section. The coordinator does not pass the flags; the executor reads them from its own `config.toml`. See [Configuration](configuration/config.md#coordinatorrepos).

### MCP Configuration

`--mcp-config` points to the MCP servers' config file. Platform-specific files by convention:

```bash
.mcp.linux.json    # Linux environments
.mcp.windows.json  # Windows environments
.mcp.macos.json    # macOS environments
```

The flag is optional when a default is configured via the `MCP_CODER_MCP_CONFIG` environment variable or `[mcp] default_config_path` in `config.toml`. See the [Configuration Guide](configuration/config.md).

### Claude Code Settings

`--settings` pins the Claude Code settings file (`.claude/settings.local.json` or `.claude/settings.json`). The path is forwarded to Claude via its native `--settings` flag and overrides cwd-based settings discovery. The file controls permissions, `enabledMcpjsonServers`, hooks, env, model and the rest of the Claude Code settings schema.

It is optional when a default is set via `MCP_CODER_CLAUDE_SETTINGS` or `[claude] default_settings_path` in `config.toml`. With no override, mcp-coder auto-detects `<project_dir>/.claude/settings.local.json`, then `<project_dir>/.claude/settings.json`. See the [Configuration Guide](configuration/config.md#claude).

### First Time Setup

```bash
# Create the user config and deploy skills, agents and the knowledge base into the project
mcp-coder init

# Coordinator commands also auto-create the config template
mcp-coder coordinator --dry-run --repo repo_name --branch-name main
# Output: Created default config file at ~/.mcp_coder/config.toml

# After editing config.toml and setting up the repository: check everything
mcp-coder verify
```

Full setup checklist: [Repository Setup](repository-setup/README.md).

---

## Commands

### init

Create the user config file (if missing), deploy the bundled Claude Code resources (skills, knowledge base and agents) into `.claude/` of the project, and add the VSCodeClaude entries to the project's `.gitignore`.

```bash
mcp-coder init [--project-dir PATH] [--just-skills]
```

`--just-skills` deploys only the bundled resources (all three sets, despite the name) and skips config creation. Use it to refresh them after upgrading mcp-coder. Existing files are never overwritten; delete a file first to refresh it.

The `.gitignore` step runs in both modes and is idempotent. If the file cannot be read or written it is logged as a warning, the remaining steps still run, and the command fails.

```bash
mcp-coder init                                   # config + bundled resources
mcp-coder init --just-skills                     # refresh deployed resources only
mcp-coder init --project-dir /path/to/project
```

---

### install

Install mcp-coder into a target environment: create `<target>/.venv`, install mcp-coder from git, PyPI or a local checkout, apply the sibling-package overrides and report the installed versions. Python packages only; staging `.mcp.json` or `.claude/` is the caller's job.

```bash
mcp-coder install TARGET [OPTIONS]
```

Options that need explaining:

- `--source {git,pypi,local}`: where to install mcp-coder from (default `git`; `--ref` picks the branch, tag or sha).
- `--local-path PATH`: local checkout; required for `--source local`. It also selects which `pyproject.toml` is read for the extras policy and the GitHub overrides (default: `<target>`).
- `--extras EXTRAS`: for example `dev` or `dev,mlflow`; `""` for none. Default: `[tool.mcp-coder.install] extras` from the pyproject.toml at `--local-path`, else `dev`.
- `--use-sync`: for `--source local`, use the `uv.lock`-honoring sequence. Requires `target == --local-path`.
- `--check`: dry run, prints every command without executing it.

After the version report, install runs the `[tool.mcp-coder.install] post_install_checks` declared in the pyproject.toml at `--local-path`. Any failing check fails the install; `--check` only prints them.

```bash
# GitHub HEAD, siblings pinned from a checkout
mcp-coder install ~/mcp-coder-env --source git --local-path ~/src/mcp_coder

# Editable install of a local checkout
mcp-coder install ~/src/mcp_coder --source local --local-path ~/src/mcp_coder
```

See the [Installation Guide](getting-started/installation.md) for which form to pick.

---

### verify

Check the whole local setup in one report. Run it after editing `config.toml` and after setting up a repository.

```bash
mcp-coder verify [OPTIONS]
```

The report has these sections: environment, `CONFIG` (the `config.toml` location, parse errors, missing required fields and unknown keys with a "did you mean" hint), `PROMPTS`, project configuration, `GIT` (including commit signing), `GITHUB` (token and security checks), `JENKINS` and `JENKINS JOBS` (only when `[jenkins]` is set), the Claude CLI, the active LLM provider and where it came from, LangChain (when it is the provider), the MCP servers (smoke test) and MLflow. Exits 1 when a check fails.

- `--llm-method METHOD` checks that provider instead of the configured one.
- `--check-models` lists the models available to the configured LangChain backend (needs network).
- `--list-mcp-tools` lists the MCP tools, grouped by server.

---

### create-plan

Generate an implementation plan for a GitHub issue: a summary and step files in `pr_info/`.

```bash
mcp-coder create-plan ISSUE_NUMBER [OPTIONS]
```

Normally dispatched by the coordinator for `status-02:awaiting-planning`. See [Plan creation](processes-prompts/processes/02-plan-creation.md).

```bash
mcp-coder create-plan 123
mcp-coder create-plan 456 --update-issue-labels --post-issue-comments
mcp-coder create-plan 789 --project-dir /path/to/project
```

---

### review-plan

Run an automated review of the implementation plan on the current branch. The issue number is derived from the branch (no positional argument).

```bash
mcp-coder review-plan [OPTIONS]
```

A multi-round loop pairs a fresh reviewer session each round with a persistent supervisor session (rounds cap: 5) and ends in a 3-way decision: **success** advances the issue to `status-05:plan-ready`; **needs-human** routes to `status-04:plan-review` for the interactive supervisor; **error** sets a `status-14f-*` failure label. Each round appends to `pr_info/plan_review_log_{n}.md`. The coordinator dispatches it only with `auto_review_plan = true`; otherwise run it manually.

```bash
mcp-coder review-plan
mcp-coder review-plan --update-issue-labels --post-issue-comments
```

---

### implement

Execute the implementation workflow: read the tasks from `pr_info/TASK_TRACKER.md` and implement them step by step, running the quality checks and committing after each step.

```bash
mcp-coder implement [OPTIONS]
```

Normally dispatched by the coordinator for `status-05:plan-ready`. See [Implementation](processes-prompts/processes/05-implementation.md).

```bash
mcp-coder implement
mcp-coder implement --update-issue-labels --post-issue-comments
mcp-coder implement --llm-method langchain --mcp-config .mcp.linux.json
mcp-coder implement --mcp-config .mcp.json --settings .claude/settings.local.json
```

---

### rebase

Rebase the current feature branch onto its base branch, resolving conflicts with LLM assistance where needed. This is the same rebase step the `review-implementation` workflow runs between rounds.

```bash
mcp-coder rebase [OPTIONS]
```

The base branch is auto-detected. A base named in the issue's `### Base Branch` section is used as-is, but only when the issue body is trusted (see [Trust and Validation](repository-setup/github.md#trust-and-validation)); otherwise detection falls back. A base found from an open PR, git merge-base or the default branch is accepted automatically only when it is `main` or `master`; otherwise pass `--base-branch`. The command fails if the base does not exist on origin.

```bash
mcp-coder rebase
mcp-coder rebase --base-branch develop
```

---

### review-implementation

Run an automated review of the implemented code on the current branch. The issue number is derived from the branch (no positional argument).

```bash
mcp-coder review-implementation [OPTIONS]
```

A multi-round loop pairs a fresh reviewer session each round with a persistent supervisor session (rounds cap: 5), applies fixes via MCP edit tools, and re-runs the shared rebase and CI steps between rounds. It ends in a 3-way decision: **success** advances the issue to `status-08:ready-pr`; **needs-human** routes to `status-07:code-review` for the interactive supervisor; **error** sets a `status-17f-*` failure label (`status-17f-ci:code-review-ci-fix-needed` when CI is still red at the rounds cap).

Two gates can also fail the run before it advances: `status-17f-tasks:code-review-open-tasks` when `## Tasks` in `pr_info/TASK_TRACKER.md` still has unchecked items (recover with `/implementation_finalise`), and `status-17f-ci-unknown:code-review-ci-unknown` when the final gate cannot prove CI green because the status is pending, not configured, unknown or unavailable (recover with `/check_branch_status`). Each round appends to `pr_info/implementation_review_log_{n}.md`. The coordinator dispatches it only with `auto_review_implementation = true`; otherwise run it manually.

```bash
mcp-coder review-implementation
mcp-coder review-implementation --update-issue-labels --post-issue-comments
```

---

### create-pr

Create a pull request with an AI-generated summary of the changes. Rebases first when the branch is behind its base.

```bash
mcp-coder create-pr [OPTIONS]
```

**Prerequisites:** clean working directory; all tasks complete in `pr_info/TASK_TRACKER.md`; on a feature branch (not main); GitHub credentials configured.

**Post-creation checks.** Once the PR exists, `create-pr` polls its `mergeable_state` (one rebase-and-push on `dirty`), then waits for the CI run of the pushed HEAD without fixing anything. The outcome sets the final label: `status-10:pr-created`, `status-74:pr-merge-conflict` (still conflicting) or `status-81:failing-ci`. The checks also run with `--no-update-issue-labels`; the outcome is then only logged. If the branch already has an open PR, `create-pr` resumes at these checks instead of creating a new one.

**Description refresh.** If the post-creation rebase pushed new commits, the PR title and body are regenerated from the full branch diff (closing references kept). This is best-effort and never changes the label or exit code. `fix-ci` refreshes the same way when its fixes pushed commits.

```bash
mcp-coder create-pr
mcp-coder create-pr --update-issue-labels --post-issue-comments
```

---

### fix-conflict

Rebase a PR onto its base branch to resolve a merge conflict. Jenkins-dispatched for `status-71:merge-conflict` (see [PR follow-up](processes-prompts/processes/71-pr-follow-up.md)); normally run by the coordinator, not by hand.

```bash
mcp-coder fix-conflict [--project-dir PATH]
```

Runs the mechanical rebase only, with no LLM. It then re-reads the PR's `mergeable_state` (polling every 5 s, up to 30 s, while GitHub reports `unknown`) and sets the label itself:

- settled and not `dirty`, or still `unknown` after a successful rebase → `status-10:pr-created`;
- still conflicting (`dirty`), no open PR found, or still `unknown` after a failed rebase or push → `status-74:pr-merge-conflict` with a "Fix Conflict Failed" comment (verdict, rebase reason, base, conflicting and uncommitted files).

Crashes are caught by `run_guarded()`, which comments and sets `status-73:merge-conflict-failed`.

---

### fix-ci

Run the CI auto-fix loop on a PR with failing CI. Jenkins-dispatched for `status-81:failing-ci` (see [PR follow-up](processes-prompts/processes/71-pr-follow-up.md)); normally run by the coordinator, not by hand.

```bash
mcp-coder fix-ci [OPTIONS]
```

Reuses the same `check_and_fix_ci` loop as `implement`. CI passing returns the issue to `status-10:pr-created`. Exhausted fix attempts, an LLM timeout or an unavailable MCP server post a comment (the Category line gives the reason) and set `status-84:pr-ci-failed`. Unexpected crashes are caught by `run_guarded()`, which comments and sets `status-83:ci-fix-failed`.

---

### coordinator

Monitor GitHub issues and dispatch workflows (create-plan, implement, create-pr, and the optional review-plan and review-implementation) as Jenkins jobs, based on each issue's status label. It also checks open PRs and routes merge conflicts, failing CI and review comments. Repositories come from `[coordinator.repos.*]` in `config.toml`; Jenkins access from `[jenkins]`.

```bash
mcp-coder coordinator (--all | --repo REPO_NAME) [OPTIONS]
```

- `--all` processes every configured repository; `--repo NAME` one (the section name under `[coordinator.repos.*]`). They are mutually exclusive.
- `--dry-run` runs a real Jenkins build of the executor job against `--branch-name`, without touching GitHub issues or labels. It needs `--repo` and `--branch-name`, and is the recommended first-run check for a newly configured repository. `--log-level-coordinator` sets the log level of the `mcp-coder` commands in that test script (default `DEBUG`).
- `--force-refresh` bypasses the GitHub cache. See `cache_refresh_minutes` in the [Configuration Guide](configuration/config.md).

See [Jenkins Setup](repository-setup/jenkins.md) for the required permissions and credentials, and [Coordinator and VSCodeClaude](coordinator-vscodeclaude.md).

```bash
mcp-coder coordinator --all
mcp-coder coordinator --repo mcp_coder
mcp-coder coordinator --dry-run --repo mcp_coder --branch-name main
mcp-coder coordinator --all --force-refresh
```

---

### icoder

Interactive terminal chat (a Textual TUI) for LLM-assisted coding, with streaming responses, slash commands and session persistence. **Prototype.** See the [iCoder User Guide](iCoder.md) and [TUI Reference](icoder/icoder.md).

```bash
mcp-coder icoder [OPTIONS]
```

- Session options `--continue-session-from FILE` (a `.jsonl` event log), `--continue-session` (a session picker over prior iCoder logs in the project) and `--session-id ID` are mutually exclusive.
- `--initial-color COLOR` sets the prompt border colour at startup (named colour or hex code).
- A structured event log is written to `logs/icoder_<timestamp>.jsonl`.
- Built-in commands: `/help`, `/clear`, `/quit`. Shift+Enter inserts a newline, Enter submits.

```bash
mcp-coder icoder
mcp-coder icoder --llm-method langchain
mcp-coder icoder --project-dir /path/to/project --mcp-config .mcp.linux.json
```

---

### vscodeclaude launch

Launch VS Code sessions with Claude Code for the issues that need you: `status-01:created`, `status-04:plan-review`, `status-07:code-review`, and the review-comment and failure labels. **Only issues assigned to you** (the GitHub user your token authenticates as) get a session.

```bash
mcp-coder vscodeclaude launch [OPTIONS]
```

**Prerequisites:** trust the workspace base folder once in VS Code (File → Open Folder, select it, "Yes, I trust the authors"); a `[vscodeclaude]` section in `~/.mcp_coder/config.toml`; a `.mcp.json` in each repository.

- `--repo NAME` limits it to one repository; `--max-sessions N` overrides the concurrent session limit (default from config, or 3).
- `--cleanup` deletes stale clean session folders; without it they are only listed.
- `--intervene --issue NUMBER` force-opens a `bot_busy` issue for debugging.
- `--no-install-from-github` skips installing packages from GitHub even when configured in `pyproject.toml`.

Details, session states and troubleshooting: [Coordinator and VSCodeClaude](coordinator-vscodeclaude.md).

```bash
mcp-coder vscodeclaude launch
mcp-coder vscodeclaude launch --repo mcp_coder
mcp-coder vscodeclaude launch --cleanup
mcp-coder --log-level debug vscodeclaude launch
```

---

### vscodeclaude status

Show a table of all tracked VS Code Claude sessions with their state (active, closed, stale, dirty, orphaned).

```bash
mcp-coder vscodeclaude status [OPTIONS]
```

`--repo NAME` filters to one repository. `--explain` dumps the detection signals and the decision per session (read-only).

---

### prompt

Send a prompt to the configured LLM.

```bash
mcp-coder prompt "Your prompt here" [OPTIONS]
```

- `--output-format FORMAT`: `rendered` (default, human-friendly streaming), `text` (plain streaming), `ndjson` (streaming NDJSON events), `json-raw` (streaming raw events), `json` (blocking, complete response including `session_id`) or `session-id` (blocking, only the session ID). Under `--llm-method langchain` in agent mode, a turn whose history was not recorded reports `"session_id": null`; that id is not resumable, so do not chain it into a later `--session-id`.
- `--store-response` saves the session to `.mcp-coder/responses/` for later continuation.
- `--continue-session-from FILE` resumes from a specific stored session file, `--continue-session` from the most recent one (the two are mutually exclusive), and `--session-id ID` from a direct session ID (overrides the file-based options). With `--llm-method langchain` the session ID is taken from the file *name*, so `--continue-session-from` works only for a langchain history file (`~/.mcp_coder/sessions/langchain/<id>.json`). A `--store-response` file (`response_<timestamp>.json`) has no matching history and the command exits 1; use `--continue-session` or `--session-id` instead. With langchain, an unknown session ID is an error, not a new conversation.
- `--add-system-prompts` injects the system and project prompts from `[tool.mcp-coder.prompts]` in `pyproject.toml` (or the shipped defaults). See [Prompt Configuration](repository-setup/python.md#prompt-configuration).

```bash
mcp-coder prompt "Analyze this code structure"
mcp-coder prompt "Start project planning" --store-response
mcp-coder prompt "What's next?" --continue-session
mcp-coder prompt "Review my implementation" --output-format json --mcp-config .mcp.linux.json
mcp-coder prompt "Analyze code" --add-system-prompts --llm-method langchain
```

---

### commit auto

Generate a commit message with the LLM and commit.

```bash
mcp-coder commit auto [OPTIONS]
```

`--preview` shows the generated message and asks for confirmation before committing. `--push` pushes to origin after a successful commit.

```bash
mcp-coder commit auto
mcp-coder commit auto --preview
mcp-coder commit auto --push
```

---

### check branch-status

Check comprehensive branch readiness: CI status, rebase requirements, task completion and GitHub labels.

```bash
mcp-coder check branch-status [OPTIONS]
```

- `--ci-timeout SECONDS` polls CI every 15 seconds until it completes or the timeout passes (default 0: a single snapshot). It exits early when CI completes and returns the current status on timeout. Progress dots show in human mode; `--llm-truncate` makes the output LLM-friendly and the polling silent.
- `--fix [N]` attempts to fix CI failures up to N times (`--fix` alone = 1; default 0 = read-only). With N above 1 it waits for CI after each attempt and stops early when CI passes. `--llm-method`, `--mcp-config` and `--settings` apply to the fixes.
- `--wait-for-pr` waits for PR creation (up to `--pr-timeout` seconds, default 600), then runs the normal check.
- `--fail-on-reviews` exits non-zero unless PR reviews are proven clean and renders the Review Gate header (default: informational).

**Failure conditions.** The command exits non-zero when CI failed, `--wait-for-pr` expired without a PR, fix attempts failed, or (with `--fail-on-reviews`) PR reviews block merge or cannot be determined. API errors and a repository with no CI configured are treated as a graceful exit so they do not block workflows.

> **Note:** the linked-branch check is **not** gated on `--fail-on-reviews`: it applies whenever the branch name yields an issue number, so a default run can fail on a stale linked branch. GitHub's linked-branches list (the Development panel's "Create a branch" link) always wins. Only when it is empty are open PRs that close the issue (`Closes #N`) considered: one whose head is the current branch counts as `LINKED_VIA_PR` and does not block; if closing PRs exist but none matches, the state is `MISMATCH` and blocks; with no closing PR either, it is `NOT_LINKED` and blocks.

> **Known limitation:** neither `--fail-on-reviews` nor the linked-branch check is evaluated when `--fix` resolves CI. The `--fix` success path returns before that gate.

```bash
mcp-coder check branch-status
mcp-coder check branch-status --ci-timeout 300 --llm-truncate
mcp-coder check branch-status --ci-timeout 180 --fix 3

# In a script
if mcp-coder check branch-status --ci-timeout 300; then echo "ready"; else echo "not ready"; fi
```

---

### check file-size

Scan a project and report files that exceed the maximum line count. Binary files are skipped. Files listed in an allowlist are excluded.

```bash
mcp-coder check file-size [OPTIONS]
```

`--max-lines` sets the limit (default 600). `--allowlist-file` names the allowlist (default `.large-files-allowlist`): one path per line relative to the project directory, `#` starts a comment. `--generate-allowlist` prints the violating paths for piping into the allowlist, which makes gradual adoption easy: allow today's large files, enforce the limit on new ones.

```bash
mcp-coder check file-size --max-lines 400
mcp-coder check file-size --generate-allowlist > .large-files-allowlist
```

---

### gh-tool checkout-issue-branch

Check out the branch for a GitHub issue, creating a linked branch only when none exists. Used by the automated workflows to land on the right branch before running.

```bash
mcp-coder gh-tool checkout-issue-branch ISSUE_NUMBER [--project-dir PATH]
```

Resolution order: linked branch, open PR referencing the issue, closed PR whose branch still exists, then branch-name pattern (`N-...` / `.../N_...`). Otherwise it collects linked branches, open closing-PR heads and matching remote branches and checks out the single candidate; only when none exist is a new linked branch created. An existing PR's head branch is checked out rather than a duplicate branch created.

If two or more candidate branches are found, the command stops and lists them in the log instead of choosing.

```bash
mcp-coder gh-tool checkout-issue-branch 123
```

---

### gh-tool set-status

Set the workflow status label on a GitHub issue. Removes any existing status labels before applying the new one.

```bash
mcp-coder gh-tool set-status [LABEL] [OPTIONS]
```

Without `--issue NUMBER`, the issue number is extracted from the branch name, which must follow `{issue_number}-title` (for example `123-feature-name`). `--from-status LABEL` is a precondition guard: it only updates when the issue's current status matches. `--force` bypasses the clean working directory check. `mcp-coder gh-tool set-status --help` lists the available labels.

Used by the slash commands (`/plan_approve`, `/implementation_approve`, `/implementation_needs_rework`) and for failure recovery (see [Failure Handling](processes-prompts/processes/failure-handling.md)).

```bash
mcp-coder gh-tool set-status status-05:plan-ready
mcp-coder gh-tool set-status status-05:plan-ready --force
mcp-coder gh-tool set-status status-05:plan-ready --issue 123 --from-status status-04:plan-review
```

---

### gh-tool get-base-branch

Detect the base branch for the current feature branch, for diffs and rebases.

```bash
mcp-coder gh-tool get-base-branch [--project-dir PATH]
```

Priority order:

1. **Linked issue's base branch**: the issue number is taken from the branch name and the `### Base Branch` section of the issue body is used, if the body is trusted (see [Trust and Validation](repository-setup/github.md#trust-and-validation)).
2. **GitHub PR base branch**: if an open PR exists for the current branch.
3. **Git merge-base**: the branch point found via `git merge-base`.
4. **Default branch**: the repository's default branch (main or master).

```bash
BASE_BRANCH=$(mcp-coder gh-tool get-base-branch)
git diff ${BASE_BRANCH}...HEAD
```

Also available as an MCP tool in mcp-workspace.

---

### gh-tool define-labels

Sync the workflow status labels to the GitHub repository: validate the label config, then create, update and delete `status-*` label definitions. The optional operations are opt-in.

```bash
mcp-coder gh-tool define-labels [OPTIONS]
```

- `--dry-run` previews the changes without applying them.
- `--init` assigns the default label to open issues without a status label.
- `--validate` checks all open issues for errors (multiple status labels) and warnings (stale bot processes).
- `--generate-github-actions` writes `label-new-issues.yml` and `approve-command.yml` to `.github/workflows/`.
- `--all` enables all three optional operations.
- `--config PATH` selects the labels config. Resolution order: `--config`, then `[tool.mcp-coder] labels-config` in `pyproject.toml`, then the bundled defaults.

See [Label Setup](getting-started/label-setup.md).

```bash
mcp-coder gh-tool define-labels --dry-run
mcp-coder gh-tool define-labels
mcp-coder gh-tool define-labels --init --validate
mcp-coder gh-tool define-labels --all
```

---

### gh-tool issue-stats

Display issue statistics grouped by workflow status category.

```bash
mcp-coder gh-tool issue-stats [OPTIONS]
```

`--filter` limits the output to `all` (default), `human` or `bot` issues; `--details` lists the individual issues with links.

```text
=== Human Action Required ===
  status-01:created           5 issues
  status-04:plan-review       2 issues

=== Validation Errors ===
  No status label: 2 issues
  Multiple status labels: 1 issue

Total: 16 open issues (13 valid, 3 errors)
```

---

### git-tool compact-diff

Generate a diff between the current branch and its base branch, then apply a two-pass pipeline that replaces moved code blocks with concise summary comments. This reduces token usage when an LLM reviews large refactorings.

```bash
mcp-coder git-tool compact-diff [OPTIONS]
```

- `--base-branch BRANCH` overrides the auto-detected base.
- `--exclude PATTERN` excludes matching paths from both committed and uncommitted changes (repeatable).
- `--committed-only` shows only committed changes. By default, uncommitted changes (staged, unstaged, untracked) follow in full diff format, not subject to compact suppression, under `=== STAGED CHANGES ===`, `=== UNSTAGED CHANGES ===` and `=== UNTRACKED FILES ===`. The section is skipped when the working directory is clean; with no committed changes, "No committed changes" is shown first.

```bash
mcp-coder git-tool compact-diff
mcp-coder git-tool compact-diff --committed-only --project-dir /path/to/project
mcp-coder git-tool compact-diff --exclude "*.log" --exclude "*.lock"
```

---

## Common Patterns

**Run the stages by hand:**

```bash
mcp-coder create-plan 123
mcp-coder implement --update-issue-labels --post-issue-comments
mcp-coder create-pr --update-issue-labels --post-issue-comments
```

**Continue a prompt session:**

```bash
mcp-coder prompt "Let's plan feature X" --store-response
mcp-coder prompt "What's the next step?" --continue-session
```
