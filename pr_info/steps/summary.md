# Summary — Issue #1252: Approve skills set status directly via `set-status`

## Goal

`/issue_approve` and the `issue-approver` agent stop requesting a status change (comment
`/approve`, sleep 5 s, re-fetch) and instead **push** it synchronously:

```
mcp-coder gh-tool set-status <next> --from-status <current> --issue N --force
```

`set-status` replaces all labels in one `set_labels` call, so when it returns the label is in
place — no polling, no sleep, no window without a status label.

## Architectural / design changes

| Before | After |
|---|---|
| Skill comments `/approve`; `approve-command.yml` Action promotes asynchronously | Skill calls `set-status` synchronously from the local checkout |
| 5 s `mcp__mcp-tools-py__sleep` + one re-fetch to "confirm" | No sleep, no re-fetch; `set-status` output is the confirmation |
| Regression guard = prose ("do not regress") | Two guards: skill's promotable-status check (01/04/07, exactly one `status-*` label) + `--from-status` for races |
| `--repo` appended to every `gh` command | `--repo` on `gh` commands only, never on `set-status`; ignored when it matches `origin` |
| Cross-repo = same comment-and-poll flow | Cross-repo = comment `/approve`, report "approval requested, not confirmed" |

Design rules:

- **Single source of truth.** The outcome table lives only in `issue_approve/SKILL.md`. The
  agent reads the skill at runtime and points at its report step; the supervisor says only
  that approval is synchronous and the agent reports the outcome.
- **Promotion map duplicated** in the skill and `approve-command.yml` — accepted; a stale
  skill copy fails safe via `--from-status` (skip) or exit 1 (invalid label).
- **`approve-command.yml` stays** — it serves manual `/approve` and the cross-repo fallback.
- **`--force`** only bypasses the clean-tree check (irrelevant for a label change). This
  deliberately differs from `plan_approve`.
- **No `/approve` on the workspace path** — the Action would race `set-status` and post
  "⚠️ Cannot promote".

`set-status` facts relied on (`src/mcp_coder/cli/commands/set_status.py`, unchanged):

- success → exit 0, `Updated issue #N to <next>`
- `--from-status` mismatch → exit 0, `Skipped set-status to '<next>': current label is 'X', expected 'Y'`
- invalid label / API failure → exit 1; usage error → exit 2
- messages go to stderr — must not be redirected or dropped

## Files modified

No Python code, no new files, no new modules.

| File | Change |
|---|---|
| `.claude/skills/issue_approve/SKILL.md` | frontmatter tools; cross-repo section; steps 3–6 → promote + report |
| `.claude/agents/issue-approver.md` | `tools:`; intro sentence; drop wait/check clause; shell rule; report line |
| `.claude/skills/issue_analyse_supervisor/SKILL.md` | approver bullet (L51) |
| `docs/repository-setup/agent-permissions.md` | `issue-approver` paragraph — drop "sleep moved into the skill" |
| `docs/repository-setup/README.md` | `issue-approver.md` row (L58) requirements |
| `docs/processes-prompts/development-process.md` | Approve Issue "Additional capability" (L254) |

Left unchanged on purpose: manual `/approve` mentions (README ~L121, development-process
~L186/428/878, `docs/repository-setup/github.md`), `approve-command.yml`, `set_status.py`.

## Steps

One step / one commit: the agent reads the skill at runtime and the supervisor describes the
agent, so splitting would leave a commit where they disagree.

- [step_1.md](./step_1.md) — rewrite skill, agent, supervisor bullet and the three docs.

## Testing

Markdown-only; there is no unit to test (tests in `tests/icoder/` that parse skill
frontmatter use temp fixtures, not these files). Verification is by search assertions in
step 1 plus the mandatory pylint / pytest / mypy run.
