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
silently — the better failure mode, but a real coupling.

`issue-approver` needs none of this: it targets no skill and inlines its own procedure.

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
- **Scoped skill grants would not help.** `allowed-tools` entries such as
  `Bash(git add *)` are a **pre-approval list, not a restriction** — non-matching commands
  still go through the normal permission flow rather than being refused — and the whole
  mechanism is moot under `bypassPermissions`.
- **A "refuse unless launched by a supervisor" instruction would not help either.** The
  agent sees only its launch prompt, which the caller writes, so the claim is
  unverifiable self-attestation.
- **The allow-list itself is bypassed by a permissive session permission mode**, which is
  how direct commits from a main session can succeed despite the omitted entries.

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
