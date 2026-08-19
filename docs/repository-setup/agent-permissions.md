# Agent permissions and the `disable-model-invocation` trap

Rationale for how `.claude/agents/*.md` are wired. Deliberately kept out of the agent files
themselves: an agent's markdown body *is* its system prompt, loaded on every launch, so
maintainer-facing notes there cost context on each run — and a section explaining that a
constraint is unenforced reads, from inside the prompt, as permission to ignore it.

## Agents cannot invoke `disable-model-invocation` skills

Several skills carry `disable-model-invocation: true`, reserving them for the user typing
`/<name>`. That flag gates the **Skill tool from every model context, subagents included**.
It is independent of permissions — allow-listing `Skill(commit_push)` does not lift it.

`commit-pusher` and `issue-updater` were each defined with a single instruction ("invoke the
`/commit_push` skill" / "invoke the `/issue_update` skill") against exactly such a skill, so
neither had a reachable procedure and both failed on every launch.

**Resolution:** each agent reads its skill's `SKILL.md` with `mcp__mcp-workspace__read_file`
and follows the process. Reading the file is not invoking the skill, so the flag does not
apply, the skill stays the single source of truth, and the skills remain user-only.

Consequence to be aware of: the path is load-bearing at runtime. Renaming or moving a
`SKILL.md` breaks the agent loudly at launch rather than letting a duplicated copy drift
silently — the better failure mode, but a real coupling. The coupling runs the other way too:
editing a `SKILL.md` for the user-typed path changes unattended agent behaviour, which is why
each agent names its deltas explicitly ("ignore its frontmatter", "ignore its opening step")
instead of assuming the skill reads well unattended.

`issue-approver` follows the same pattern against `.claude/skills/issue_approve/SKILL.md`. It
stayed inlined longer than the other two and had already drifted: the agent had grown the
post-approval sleep and assignee steps, while the skill held the issue-number resolution the
agent lacked. The procedure now lives in the skill, the unattended deltas in the agent.

`mcp-coder init` deploys `skills/`, `knowledge_base/` and `agents/` — not `docs/`. An
adopting repo gets the agents and the skills they read, but not this file, so the agents name
this document by path rather than linking to it; a relative link would be dead in every
downstream repo.

## What `permissionMode: bypassPermissions` does

`.claude/settings.local.json` deliberately omits `Bash(git add|commit|push)` and
`Bash(gh issue edit *)`, so those prompt in the main session. The agents carry
`bypassPermissions` so the commands run unprompted there, without widening the global allow
list.

## What it does not do

Do not treat any of the following as enforced:

- **It is not access control.** Agent frontmatter has no caller restriction — any session
  can launch these agents, not just the supervisor skills. Note also that "the supervisor"
  is a *skill*, so it runs in the main session; there is no privileged caller tier.
- **`Bash` is all-or-nothing.** Agent `tools:` takes bare tool names, so the git/gh-only
  limits stated in the agent bodies are prose. Under `bypassPermissions`, *every* shell
  command is auto-approved.
- **Scoped `allowed-tools` would not constrain *these agents*.** Entries such as
  `Bash(git add *)` are a **pre-approval list, not a restriction** — non-matching commands
  still go through the normal permission flow rather than being refused — and the whole
  mechanism is moot under `bypassPermissions`. This is a statement about the agents only; on
  the supervisor skills the same field is a real alternative, covered below.
- **A "refuse unless launched by a supervisor" instruction would not help either.** The
  agent sees only its launch prompt, which the caller writes, so the claim is
  unverifiable self-attestation.
- **The allow-list itself is bypassed by a permissive session permission mode**, which is
  how direct commits from a main session can succeed despite the omitted entries.

## The alternative this does not rule out

On a *skill*, `allowed-tools` grants the listed tools for the turn that invokes the skill, so
they run without prompting; the grant clears at the user's next message. Combined with
`disable-model-invocation`, that is a genuinely user-gated privileged tier: only a typed
`/<name>` opens it, the scope is a command pattern rather than all of `Bash`, and it expires
on its own. Putting `Bash(git add *) Bash(git commit *) Bash(git push *)` on the three
supervisor skills would retire these agents.

Two things stand in the way today:

- **The grant does not reach subagents.** A spawned agent's permission layers are built fresh
  — a `model` layer plus an optional `effort` layer — with no copy of the parent's. The grant
  is an `allowed_tools` layer, so it is simply absent. (`context: fork` skills are the
  exception: that path merges the parent's layers explicitly.) The grant therefore only helps
  if a supervisor runs `git` itself instead of delegating to `commit-pusher` — not a large
  step, since `implementation_review_supervisor` already runs `run_vulture_check` and
  `run_lint_imports_check` itself.
- **The grant dies at every escalation.** It covers one turn, and the supervisors stop to ask
  the user about major refactorings and import-contract violations. The user's reply starts a
  new turn, and the rest of the run prompts again.

Net trade: the agents survive escalations but carry an unrestricted `Bash`; a supervisor-level
grant is tightly scoped and self-expiring but breaks whenever the user is consulted.

## What actually constrains these agents

- **The launch-prompt scope check** — `commit-pusher` compares `git status` against the file
  list in its prompt and refuses if anything else changed. A check against observable state,
  not an assertion, and it bounds what a bad launch can do.
- **A `PreToolUse` hook** would be the only real enforcement of the git/gh limit: hooks fire
  regardless of permission mode, and their input carries `agent_id` / `agent_type`, so one
  can be scoped to a single agent. **None is configured today** — a deliberate deferral, not
  an oversight.
- **`deny` rules** abort a call regardless of `allowed-tools`. Whether they also override
  `bypassPermissions` has not been verified here.
