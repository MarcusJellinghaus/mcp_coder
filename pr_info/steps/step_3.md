# Step 3 — Per-process docs: PR follow-up, automated review

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_3.md`).
> Create `pr-follow-up.md` and `automated-review.md` in `docs/processes-prompts/processes/`. Use the fixed layout from the summary.
> Verify every transition against `src/mcp_coder/workflows/fix_conflict/core.py`, `src/mcp_coder/workflows/fix_ci/core.py`, `src/mcp_coder/workflows/review/config.py` and `.claude/skills/pr_comment_triage/SKILL.md`. Document the code's current behaviour; where it differs from the summary, the code wins.
> Then add the one-line back-links listed under HOW to the step 1–2 docs.
> Run the file-size check, then format, then commit as one commit.

## WHERE

```
docs/processes-prompts/processes/pr-follow-up.md       (new)
docs/processes-prompts/processes/automated-review.md   (new)
docs/processes-prompts/processes/plan-creation.md      (add link)
docs/processes-prompts/processes/plan-review.md        (add link)
docs/processes-prompts/processes/implementation.md     (add link)
docs/processes-prompts/processes/code-review.md        (add link)
docs/processes-prompts/processes/pr-merge.md           (add link)
```

## WHAT

### `pr-follow-up.md`

Source: current `development-process.md` section "10. PR-Health" (lines 1188–1215) plus the code.

- **Labels:**
  - 71 / 72 / 73 / 74, 81 / 82 / 83 / 84, 91, plus 10 as the start and end state.
  - Arrow chain: the ASCII tree from lines 1192–1205, extended with the formatter-config cause on the `fix-ci` → 84 branch.
  - Detection order at 10 (conflict → CI → review comments; at most one acts per poll) and why the order matters.
- **Actor:**
  - 71 / 81: fully automated (coordinator → Jenkins `fix-conflict` / `fix-ci`; no Jenkins → issue waits).
  - 91 and 73 / 74 / 83 / 84: human or supervisor skill (vscodeclaude session).
- **Slash commands:**
  - `/pr_comment_triage` (auto-launched at 91; ends with `set-status status-10:pr-created`).
  - `/check_branch_status` (auto-launched at 73 / 74 / 83 / 84).
  - `/rebase`.
- **Failure exits:**

  | Label | Cause | Recovery |
  |---|---|---|
  | `status-73:merge-conflict-failed` | `fix-conflict` crashed (`run_guarded` net) or the Jenkins job died without transitioning (watchdog) | `/check_branch_status`, fix, `mcp-coder gh-tool set-status status-10:pr-created` |
  | `status-74:pr-merge-conflict` | still `dirty`, no open PR found, or `unknown` after a failed rebase | resolve manually (`/rebase` / `/check_branch_status`), then set 10 |
  | `status-83:ci-fix-failed` | `fix-ci` crashed or the job died | `/check_branch_status`, fix, set 10 |
  | `status-84:pr-ci-failed` | fix attempts exhausted, LLM timeout, MCP unavailable, or formatter-config error (comment Category line) | fix CI manually, set 10 |
  | — (label stays 72 / 82) | current branch could not be determined → exit 1 | check the Jenkins log; set `status-71` / `status-81` to retry |

- **Review-comment rules:** keep the "Review feedback is never auto-fixed" and "Triage session" paragraphs (lines 1213–1215), shortened only where a sentence repeats a table row.

### `automated-review.md`

Source: section "9. Automated Review" (lines 1158–1186) plus the `14f` / `17f` rows and the notes from lines 1138–1156.

- **Labels:**
  - 14 → 14i, 17 → 17i, plus all `14f-*` / `17f-*`.
  - Arrow chain from lines 1166–1176: plan success → 05, escalate → 04, error → `14f-*`; code success → 08, escalate → 07, error → `17f-*`.
- **Actor:** fully automated, **only** when `auto_review_plan` / `auto_review_implementation` is on (default off; link `../../configuration/config.md`). Use "can run" wording.
- **Slash commands:** `/check_branch_status` (failure labels), `/implementation_finalise` (`17f-tasks`).
- **How a review runs:** keep lines 1178–1184 (rounds cap 5, reviewer / supervisor, review logs, handed-off comment) and the quality-gate note at line 1186.
- **Failure exits:**
  - All 3 `14f-*` and 6 `17f-*` labels, with cause and recovery from lines 1138–1146.
  - Recovery re-queues with `set-status status-14:plan-review-bot` / `status-17:code-review-bot`.
  - Alternative: hand off to the interactive supervisor with `status-04` / `status-07` (line 1154).
  - Note: a CI-less repo ends on `17f-ci-unknown` (line 1156).

## HOW — back-links (one line each)

| File | Add |
|---|---|
| `plan-creation.md` | `auto_review_plan` on → see [Automated review](automated-review.md) |
| `plan-review.md` | escalations from `status-14` arrive here — see [Automated review](automated-review.md) |
| `implementation.md` | `auto_review_implementation` on → see [Automated review](automated-review.md) |
| `code-review.md` | escalations from `status-17` arrive here — see [Automated review](automated-review.md) |
| `pr-merge.md` | while the PR waits, see [PR follow-up](pr-follow-up.md) |

## ALGORITHM

```
read fix_conflict/core.py run_fix_conflict_workflow -> list verdict -> label
read fix_ci/core.py run_fix_ci_workflow -> list _fail call sites -> 84, success -> 10
read review/config.py -> success / escalate / failure_labels per lane
write both docs from these facts
add the five back-links
```

## DATA

Not applicable.

## Checks

- `check_file_size` (`max_lines=750`).
- All `14f-*` / `17f-*` names in `labels.json` appear in `automated-review.md`; 73 / 74 / 83 / 84 appear in `pr-follow-up.md` (check with `search_files`).
- Format, then commit: `docs(processes): add pr-follow-up and automated-review docs`.
