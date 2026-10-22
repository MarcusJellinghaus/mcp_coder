# Step 3 — Triage skill and docs

## LLM prompt

Read `pr_info/steps/summary.md`, then implement this step (`pr_info/steps/step_3.md`) only.
Steps 1–2 (code changes) are already done. Documentation only — no tests. Keep edits short;
`development-process.md` carries the full explanation, the other files one clause each.
Produce exactly one commit.

## WHERE / WHAT

### `.claude/skills/pr_comment_triage/SKILL.md`

- After the intro paragraph, one or two sentences on the trigger: `status-91` fires on
  unresolved threads, changes-requested reviews submitted after the last return to `status-10`,
  and new PR comments; a comment whose first line contains ❌ (mcp-coder's automated notes)
  is ignored; a review already triaged does not re-trigger.
- Replace "When done" with:
  - CI green, no rebase needed, every item fixed, replied to or declined. A changes-requested
    review that has been replied to or fixed does not block — it stays listed by
    `/check_branch_status` until the reviewer re-reviews.
  - Re-run `/check_branch_status` right before `set-status` and handle anything new.
  - Post all replies before `mcp-coder gh-tool set-status status-10:pr-created` (the relabel
    sets the watermark).

### `docs/processes-prompts/development-process.md` (section 10)

- Line ~1212: rewrite the trigger and live-state sentences. Unresolved threads use GitHub's
  live state. Changes-requested reviews and conversation comments count only if newer than the
  last return to `status-10` after a `status-91` (reviews by `submitted_at`, comments by
  `created_at`), so a review already triaged does not re-trigger. Comments whose first line
  contains ❌ are skipped — that is mcp-coder's marker for its own notes, so a human comment
  starting that way is ignored too. Keep "Code-scanning alerts are excluded" and "nothing is
  stored locally".
- Line ~1214 ("Triage session"): an answered or fixed changes-requested review does not block
  `status-10`; `/check_branch_status` is re-run before `set-status`.

### `docs/coordinator-vscodeclaude.md` (~line 114)

`**New review feedback** (unresolved thread, or a changes-requested review / PR comment newer
than the last triage; comments whose first line contains ❌ are ignored) → status-91`.

### `docs/getting-started/label-setup.md` (~line 304)

`status-91` row: "Outstanding review feedback (unresolved thread, untriaged changes-requested
review, new PR comment; ❌-first-line comments ignored) — human triage via `/pr_comment_triage`".

## Checks

Re-read each edited section for consistency with `summary.md`. Run `run_format_code` before
committing (no Python changed, should be a no-op).
