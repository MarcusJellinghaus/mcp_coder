# Agent permissions and the `disable-model-invocation` trap

Rationale for how `.claude/agents/*.md` are wired. Deliberately kept out of the agent files
themselves: an agent's markdown body *is* its system prompt, loaded on every launch, so
maintainer-facing notes there cost context on each run — and a section explaining that a
constraint is unenforced reads, from inside the prompt, as permission to ignore it.

**Scope: Claude Code only.** `disable-model-invocation`, `allowed-tools`, `skills:`, hooks
and subagents are Claude Code mechanisms — nothing here describes another client. Worth
stating because Copilot CLI reads `.claude/skills/*/SKILL.md` natively ([copilot.md](copilot.md))
but has no `.claude/agents/` and no permission modes: under Copilot the skills are plain
instructions and none of the gating below applies. Baseline: Claude Code 2.1.317; hook and
`skills:` behaviour tested ([How Claude permissions work §6](claude-permissions/how-it-works.md#6-subagents)).

## Agents in this repo

| Agent | Launched by | Extra tools | Hook | Write limit | `skills:` |
|---|---|---|---|---|---|
| `issue-analyst` | `issue_analyse_supervisor` | `save_file`, `delete_this_file`, `delete_directory` | none (all allow-listed) | none — `.scratch/` by instruction | `issue_analyse` |
| `plan-engineer` | `plan_review_supervisor` | file write tools | none | none — `pr_info/`, `.scratch/`, named requirement files by instruction | `plan_review`, `plan_update` |
| `code-engineer` | `implementation_review_supervisor` | file write tools, `check_branch_status` | none | none — `.mcp-file-access` guards settings | `implementation_review`, `check_branch_status` |
| `commit-pusher` | plan / implementation review supervisors | `git_commit`, `git_push` | inline allow | none | – (reads `commit_push/SKILL.md`) |
| `issue-updater` | `issue_analyse_supervisor` | `github_issue_edit`, file tools | inline allow | none — `.scratch/` by instruction | – (reads `issue_update/SKILL.md`) |
| `issue-approver` | `issue_analyse_supervisor` | `github_issue_set_status` | inline allow | none | – (reads `issue_approve/SKILL.md`) |

Extra tools = beyond the MCP read tools and mcp-tools-py. Inline allow = the one-line
frontmatter `PreToolUse` hook below, matcher = the agent's GitHub / git write tools. Enforcing
a write limit would need a hook with path parsing; the paths are instructions.

None has `Bash`, `Skill` or `permissionMode`, and none has GitHub or git write tools beyond
those listed; committing stays with `commit-pusher`. `tools:` lists every tool the preloaded
skills call (see below). `/rebase` has no agent: it stays a
self-contained skill until mcp-workspace offers rebase tools (mcp-workspace #263).

## Agents cannot invoke `disable-model-invocation` skills

Several skills carry `disable-model-invocation: true`, reserving them for the user typing
`/<name>`. That flag gates the **Skill tool from every model context, subagents included**.
It is independent of permissions — allow-listing `Skill(commit_push)` does not lift it. It
also blocks preloading: `skills:` silently skips a user-only skill (tested).

So an agent whose procedure is a user-only skill cannot invoke or preload it. Instead each of
the three privileged agents reads its skill's `SKILL.md` with
`mcp__mcp-workspace__read_file` and follows the process. Reading the file is not invoking the
skill, so the flag does not apply, the skill stays the single source of truth, and the skills
remain user-only.

Consequence to be aware of: the path is load-bearing at runtime. Renaming or moving a
`SKILL.md` breaks the agent loudly at launch rather than letting a duplicated copy drift
silently — the better failure mode, but a real coupling. The coupling runs the other way too:
editing a `SKILL.md` for the user-typed path changes unattended agent behaviour, which is why
each agent names its deltas explicitly ("ignore its frontmatter", "ignore its opening step")
instead of assuming the skill reads well unattended.

For `issue-approver` (against `.claude/skills/issue_approve/SKILL.md`) the cross-repo handling
lives in the skill, so both paths do the same thing; the agent states only the two inputs
that genuinely differ unattended — where the issue number comes from, and what counts as
validation.

## Engineer agents preload model-invocable skills

`issue-analyst`, `plan-engineer` and `code-engineer` are the supervisors' workers — dedicated
agents rather than general-purpose subagents, which would have every tool, incl. `Bash` and
GitHub writes. Their skills are model-invocable, so `skills:` injects the skill text at
launch — no `Skill` tool and no file read needed. Two rules follow (tested):

- **`skills:` injects text, not tools.** `tools:` must list every tool the preloaded skills
  call (their `allowed-tools` and their bodies).
- **Deltas, as above.** Each body says which skill applies to which launch prompt, that the
  issue number comes from the launch prompt (not `$ARGUMENTS`), which skill instructions to
  ignore (e.g. `implementation_review`'s "do not perform any action" when asked to fix,
  `check_branch_status`'s Follow-Up table), the untrusted-issue stop, and the report format
  the supervisor consumes.

They need no hook: every tool they have is in `.claude/settings.local.json` `allow`, which
custom agents inherit (tested). Custom agents also load CLAUDE.md themselves.

`tests/icoder/test_repo_agents.py` checks these rules against the frontmatter.

## The allow hook

`.claude/settings.local.json` deliberately omits `Bash(git add|commit|push)`, the git-write
MCP tools (`mcp__mcp-workspace__git_commit`, `_push`, `_push_force`, `_branch`,
`_branch_delete`) and the issue write tools (`mcp__mcp-workspace__github_issue_create`,
`_edit`, `_comment`, `_set_status`), so those prompt in the main session. Each privileged
agent carries one frontmatter `PreToolUse` hook whose `matcher` names exactly its extra tools
and whose `command` prints the `allow` decision:

```yaml
hooks:
  PreToolUse:
    - matcher: "mcp__mcp-workspace__git_commit|mcp__mcp-workspace__git_push"
      hooks:
        - type: command
          command: "echo '{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\"}}'"
```

No script, nothing extra to deploy; the command runs in Git Bash on Windows (no `shell:`
key needed). A frontmatter hook fires only for its own agent, so the global allow list stays
narrow.

**Why not `permissionMode: bypassPermissions`:** under the user default `acceptEdits` an
agent's `permissionMode` is ignored ([details](claude-permissions/how-it-works.md#6-subagents)),
so bypass would have no effect. Real bypass would also allow writes to `.git` and
`.claude`. A settings `allow` rule would reach every session and every headless run.

## What the hook does not do

Do not treat any of the following as enforced:

- **It is not access control.** Agent frontmatter has no caller restriction — any session
  can launch these agents, not just the supervisor skills. Note also that "the supervisor"
  is a *skill*, so it runs in the main session; there is no privileged caller tier.
- **It does not run everywhere** — not in untrusted folders or under `-p`
  ([details](claude-permissions/how-it-works.md#6-subagents)). A fresh vscodeclaude clone
  prompts until its folder is trusted (pre-trust: [#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434)).
- **It cannot beat `deny` or `ask`.** A hook `allow` loses to both, so no `ask` or `deny`
  rule may ever match these tools.
- **It does not limit paths.** No agent has a write limit: `.scratch/`-only or
  `pr_info/`-only are instructions in the agent body. Agent files are MCP-writable, so an
  agent with file write tools could edit another agent's hook. Write limits would need a
  hook with path parsing ([#1434](https://github.com/MarcusJellinghaus/mcp_coder/issues/1434)).
- **Edits take a restart.** Changes to an agent file apply only after a session restart.
- **`Bash` would be all-or-nothing.** Agent `tools:` takes bare tool names, so any shell
  limit stated in an agent body would be prose. None of the agents has `Bash`.
- **A "refuse unless launched by a supervisor" instruction would not help either.** The
  agent sees only its launch prompt, which the caller writes, so the claim is
  unverifiable self-attestation.

## The alternative this does not rule out

On a *skill*, `allowed-tools` grants the listed tools for the turn that invokes the skill, so
they run without prompting; the grant clears at the user's next message. Combined with
`disable-model-invocation`, that is a genuinely user-gated privileged tier: only a typed
`/<name>` opens it, the scope is the specific MCP git write tools (`git_commit`, `git_push`),
and it expires on its own. Putting `mcp__mcp-workspace__git_commit` and
`mcp__mcp-workspace__git_push` on the supervisor skills would retire `commit-pusher`.

Two things stand in the way:

- **The grant does not reach subagents.** A spawned agent's permission layers are built fresh
  — a `model` layer plus an optional `effort` layer — with no copy of the parent's. The grant
  is an `allowed_tools` layer, so it is simply absent. (`context: fork` skills are the
  exception: that path merges the parent's layers explicitly.) Read out of the shipped bundle
  of **Claude Code 2.1.227** (older than the 2.1.317 baseline), not from the docs — re-check
  it against the current build before relying on it. The grant therefore only helps
  if a supervisor runs `git` itself instead of delegating to `commit-pusher` — not a large
  step, since `implementation_review_supervisor` already runs `run_vulture_check` and
  `run_lint_imports_check` itself.
- **The grant dies at every escalation.** It covers one turn, and the supervisors stop to ask
  the user about major refactorings and import-contract violations. The user's reply starts a
  new turn, and the rest of the run prompts again.

Net trade: the agents survive escalations, but their write tools run unprompted for any
caller; a supervisor-level grant is tightly scoped and self-expiring but breaks whenever the
user is consulted.

## What actually constrains these agents

- **`tools:`** — an agent cannot call a tool it does not list. The engineer agents list no
  git or GitHub write tools and no `Bash`.
- **The launch-prompt scope check** — `commit-pusher` compares `git status` against the file
  list in its prompt and refuses if anything else changed. A check against observable state,
  not an assertion, and it bounds what a bad launch can do.
- **The git-write tools' own guardrails** — `git_commit` never amends or bypasses hooks
  (`--no-verify`); `git_push` and `git_push_force` refuse the default branch and a detached
  HEAD, and `git_push_force` uses only `--force-with-lease --force-if-includes`, never plain
  `--force`. These guardrails, plus `commit-pusher` having no `Bash`, are why allowing its
  two write tools unprompted is safe.
- **The status tool's own guard** — `issue-approver` passes `from_status`, so
  `github_issue_set_status` changes nothing unless the issue's sole status label is the
  expected one. Followed by instruction, not enforced: a call without `from_status` changes
  the status from any status.
- **`deny` rules** abort a call in every mode, hook `allow` included. This repository
  sets none.

## Deployment

`mcp-coder init` deploys `skills/`, `knowledge_base/` and `agents/` — not `docs/`. An
adopting repo gets the agents and the skills they use, but not this file. `init` never
overwrites: to pick up new agent versions, delete the old agent **and** skill files together
before re-running it — the supervisors name agents that must exist.
