# Step 2 — Docs: describe the fix-conflict outcomes

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_2.md` exactly.
> Documentation only — no code or test changes. Keep wording short and consistent with the
> outcome table in the summary. Run pylint, the fast pytest suite and mypy to confirm
> nothing broke, then make exactly one commit.

## Precondition

Step 1 is committed: `src/mcp_coder/workflows/fix_conflict/core.py` contains `def _fail(`.
If not, write one line to `pr_info/.blocked.txt` and stop.

## WHERE / WHAT

No functions, algorithm or data — text edits only.

1. `docs/cli-reference.md` — `fix-conflict` **Description** (~line 523):
   - Replace "back to `status-10:pr-created` on success, or `status-74:pr-merge-conflict`
     if the PR is still blocked. If the state stays `unknown`, the issue stays at
     `status-72:fixing-merge-conflict` for the next coordinator poll." with the outcomes:
     - settled and not `dirty`, or still `unknown` after a successful rebase →
       `status-10:pr-created`;
     - still conflicting (`dirty`), no open PR found, or still `unknown` after a failed
       rebase/push → `status-74:pr-merge-conflict` with a "Fix Conflict Failed" comment
       (verdict, rebase reason, base, conflicting/uncommitted files).
   - Keep the `run_guarded()` / `status-73` crash sentence.

2. `docs/processes-prompts/development-process.md`
   - §10 tree (~lines 1194-1197), replace the `status-72` sub-branches with:
     ```
     │                        ├─ settled, not dirty            → status-10:pr-created
     │                        ├─ unknown, rebase ok            → status-10:pr-created
     │                        ├─ still conflicting (dirty)     → status-74  (human)
     │                        ├─ no open PR / unknown + rebase failed → status-74  (human)
     │                        └─ job crashed                   → status-73  (human)
     ```
     Keep the tree's column alignment readable.
   - Human-action table (~line 1148), `status-74:pr-merge-conflict` row: replace
     "Rebase could not resolve the conflict" with "fix-conflict could not get the PR
     mergeable (conflict, rebase failed, or no open PR) — see the issue comment".

3. `docs/getting-started/label-setup.md` (~line 299), `status-74:pr-merge-conflict` row:
   replace "Rebase could not resolve the conflict — needs manual resolution" with
   "fix-conflict could not get the PR mergeable (conflict, rebase failed, or no open PR) —
   needs a human".

## HOW

- Do NOT change `src/mcp_coder/config/labels.json` (avoids a `define-labels` re-sync).
- Search the docs for any remaining "stays at `status-72`" / "next coordinator poll" wording
  about fix-conflict and update it the same way.
