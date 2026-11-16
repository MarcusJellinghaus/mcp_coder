# Agent permissions and the `disable-model-invocation` trap

Rationale for how `.claude/agents/*.md` are wired. Deliberately kept out of the agent files
themselves: an agent's markdown body *is* its system prompt, loaded on every launch, so
maintainer-facing notes there cost context on each run — and a section explaining that a
constraint is unenforced reads, from inside the prompt, as permission to ignore it.

**Scope: Claude Code only.** `disable-model-invocation`, `allowed-tools`, `skills:`, hooks
and subagents are Claude Code mechanisms — nothing here describes another client. Worth
stating because Copilot CLI reads `.claude/skills/*/SKILL.md` natively ([copilot.md](copilot.md))
but has no `.claude/agents/` and no permission modes: under Copilot the skills are plain
instructions and none of the gating below applies. Verified against **Claude Code 2.1.227**;
hook and `skills:` behaviour tested 2026-11-16 (T23, T26 in
[claude-permissions/implementation.md](claude-permissions/implementation.md)).

## The agents

| Agent | Launched by | Process | Extra tools (allow hook) |
|---|---|---|---|
| `commit-pusher` | plan / implementation review supervisors | reads `commit_push/SKILL.md` | `git_commit`, `git_push` |
| `issue-updater` | `issue_analyse_supervisor` | reads `issue_update/SKILL.md` | `github_issue_edit` |
| `issue-approver` | `issue_analyse_supervisor` | reads `issue_approve/SKILL.md` | `github_issue_set_status` |
| `issue-analyst` | `issue_analyse_supervisor` | preloads `issue_analyse` | none |
| `plan-engineer` | `plan_review_supervisor` | preloads `plan_review`, `plan_update` | none |
| `code-engineer` | `implementation_review_supervisor` | preloads `implementation_review`, `check_branch_status` | none |

None has `Bash`, `Skill` or `permissionMode`. The three engineer agents have no git or
GitHub write tools; committing stays with `commit-pusher`.

## Agents cannot invoke `disable-model-invocation` skills

Several skills carry `disable-model-invocation: true`, reserving them for the user typing
`/<name>`. That flag gates the **Skill tool from every model context, subagents included**.
It is independent of permissions — allow-listing `Skill(commit_push)` does not lift it. It
also blocks preloading: `skills:` silently skips a user-only skill (T23).

`commit-pusher` and `issue-updater` were each defined with a single instruction ("invoke the
`/commit_push` skill" / "invoke the `/issue_update` skill") against exactly such a skill, so
neither had a reachable procedure and both failed on every launch.

**Resolution:** each of the three privileged agents reads its skill's `SKILL.md` with
`mcp__mcp-workspace__read_file` and follows the process. Reading the file is not invoking the
skill, so the flag does not apply, the skill stays the single source of truth, and the skills
remain user-only.

Consequence to be aware of: the path is load-bearing at runtime. Renaming or moving a
`SKILL.md` breaks the agent loudly at launch rather than letting a duplicated copy drift
silently — the better failure mode, but a real coupling. The coupling runs the other way too:
editing a `SKILL.md` for the user-typed path changes unattended agent behaviour, which is why
each agent names its deltas explicitly ("ignore its frontmatter", "ignore its opening step")
instead of assuming the skill reads well unattended.

`issue-approver` follows the same pattern against `.claude/skills/issue_approve/SKILL.md`. It
stayed inlined longer than the other two and had drifted in both directions: the agent had
grown cross-repo handling, while the skill held the issue-number
resolution the agent lacked. The `--repo` handling moved into the skill,
so both paths now do the same thing; what remains in the agent is only the two inputs that
genuinely differ unattended — where the issue number comes from, and what counts as
validation.

## Engineer agents preload model-invocable skills

`issue-analyst`, `plan-engineer` and `code-engineer` replace the general-purpose engineer
subagents the supervisors used to launch (those had every tool, incl. `Bash` and GitHub
writes). Their skills are model-invocable, so `skills:` injects the skill text at launch — no
`Skill` tool and no file read needed. Two rules follow from T23:

- **`skills:` injects text, not tools.** `tools:` must list every tool the preloaded skills
  call (their `allowed-tools` and their bodies).
- **Deltas, as above.** Each body says which skill applies to which launch prompt, that the
  issue number comes from the launch prompt (not `$ARGUMENTS`), which skill instructions to
  ignore (e.g. `implementation_review`'s "do not perform any action" when asked to fix,
  `check_branch_status`'s Follow-Up table), the untrusted-issue stop, and the report format
  the supervisor consumes.

They need no hook: every tool they have is in `.claude/settings.local.json` `allow`, which
custom agents inherit (T23). Custom agents also load CLAUDE.md themselves.

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

**Why not `permissionMode: bypassPermissions`** (used before): per the docs, an agent's
`permissionMode` is ignored when the parent runs `acceptEdits`, `auto` or
`bypassPermissions` — the user default here is `acceptEdits`, so per the docs bypass had no
effect (F9 — documented, not tested). Real bypass would also have allowed writes to `.git`
and `.claude`. A settings `allow` rule would reach every session and every headless run.

## What the hook does not do

Do not treat any of the following as enforced:

- **It is not access control.** Agent frontmatter has no caller restriction — any session
  can launch these agents, not just the supervisor skills. Note also that "the supervisor"
  is a *skill*, so it runs in the main session; there is no privileged caller tier.
- **It does not run everywhere.** Frontmatter hooks are skipped in untrusted folders and
  under `-p` (docs). There the extra tools prompt (interactive) or are denied (headless). A
  fresh vscodeclaude clone prompts until its folder is trusted (FU8).
- **It cannot beat `deny` or `ask`.** A hook `allow` loses to both, so no `ask` or `deny`
  rule may ever match these tools.
- **It does not limit paths.** No agent has a write limit yet: `.scratch/`-only or
  `pr_info/`-only are instructions in the agent body. Agent files are MCP-writable, so an
  agent with file write tools could edit another agent's hook. Write limits need a hook
  runtime with path parsing — later.
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

Two things stand in the way today:

- **The grant does not reach subagents.** A spawned agent's permission layers are built fresh
  — a `model` layer plus an optional `effort` layer — with no copy of the parent's. The grant
  is an `allowed_tools` layer, so it is simply absent. (`context: fork` skills are the
  exception: that path merges the parent's layers explicitly.) Read out of the shipped bundle
  of **Claude Code 2.1.227**, not from the docs — re-check it against the current build before
  relying on it. The grant therefore only helps
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
