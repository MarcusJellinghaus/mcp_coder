# Step 8 — Documentation

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_8.md`.
> Docs only. Keep the writing style from `.claude/CLAUDE.md` (short, no filler). Check every new
> anchor link resolves. Make exactly one commit.

## WHERE

- `docs/repository-setup/github.md`
- `docs/coordinator-vscodeclaude.md`
- `docs/cli-reference.md`
- `docs/configuration/config.md`
- `SECURITY.md`

## WHAT / HOW

### `docs/repository-setup/github.md` — single source of truth

- Keep `### Trust and Validation` (anchor `#trust-and-validation`, linked from `cli-reference.md` and
  `SECURITY.md`) unchanged apart from one added line linking to the new section.
- Add a new top-level section with a **distinct** heading, e.g. `## Issue body trust` (anchor
  `#issue-body-trust`). Never name it "Trust and Validation".
- Content:
  - Rule (author or last body editor; editor has no role check) → link to mcp-workspace Commenter trust.
  - Behaviour: coordinator skips (per-repo INFO summary, no comment, no label change, all workflows incl.
    `fix-conflict` / `fix-ci`); vscodeclaude review-only session (fixed prompt, banner/status without title
    and `Branch:`, table marker); `create-plan` warns and runs. `lookup_failed` is handled like untrusted.
  - **Accepting an external issue**: the maintainer edits the body. Works only if the maintainer is the token
    user the coordinator runs with, or is in `trusted_commenters`. A machine/Jenkins token user that differs
    from the maintainer breaks the flow; collaborator status of the editor does not help.
  - **Jenkins token user**: the `create-plan` job runs with its own credentials, so its trust verdict can differ.
  - **Bots / machine authors** (`github-actions[bot]`, dependabot) at a `bot_pickup` status stop being
    dispatched unless they are listed in `trusted_commenters`. This is a behaviour change.
  - **Limitations**:
    - Title not vetted (nor the branch name derived from it); a stranger can change the title after acceptance.
    - Time-of-check vs time-of-use: the Jenkins job re-reads the issue live.
    - Re-edit by the untrusted author makes the body untrusted again.
    - Restart: if regenerating files fails with a non-rate-limit error, the old spec is reused, and `tasks.json`
      (`runOn: folderOpen`) re-runs the stored spec on manual reopen; trust is recomputed only on
      coordinator-driven launch/restart.
    - `github_issue_view` fences by *author* trust only, so an accepted body may still be fenced (fails safe).
    - Review-only protection ends once the user asks the agent to read the issue (e.g. `/issue_analyse`).
  - **Cost**: untrusted issues keep their label, so every coordinator run repeats one lookup and one summary
    entry per such issue; a `/approve`d untrusted issue is explained only in the coordinator log;
    `vscodeclaude status` makes one lookup per launchable untrusted-author row. No caching of trust results.
  - **Stale cache**: a cache entry without `author_association` on a maintainer's never-edited issue stays skipped
    until the next full refresh (`cache_refresh_minutes`) or `--force-refresh`; a maintainer edit fixes it at once.

### `docs/coordinator-vscodeclaude.md`

- Issue selection: one line on the gate / review-only sessions + link.
- Generated files: the untrusted banner / status-file variant and the blank `title` in `.vscodeclaude_session.json`.
- Adapt the machine-user note next to the ❌ / `status-91` caveat: it covers *authors* of PRs and notes; for
  *body editors* the token user or `trusted_commenters` is what counts (link).
- "GitHub rate limits and caches": trust lookups are never cached; one lookup per gated issue per run.

### `docs/cli-reference.md`

- `coordinator run`: skips untrusted bodies (link).
- `create-plan`: warns on an untrusted body, still runs (link).

### `docs/configuration/config.md`

- `trusted_commenters` row: also covers issue-body author and editor trust, bots and machine users (link).

### `SECURITY.md`

- Reword the Threat Model sentence "mcp-coder only acts on issues … from trusted authors": issue bodies must be
  trusted (author or last editor) before automated workflows run them; untrusted bodies are skipped or opened
  review-only. Link to `docs/repository-setup/github.md#issue-body-trust`.

## ALGORITHM / DATA

None (docs only).

## Checks

- `#trust-and-validation` still exists exactly once in `github.md`.
- All new relative links point to existing files and anchors (search for each heading).
