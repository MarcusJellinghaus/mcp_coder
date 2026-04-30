# Step 5 — Documentation

## LLM Prompt

> Implement Step 5 of issue #844. Read `pr_info/steps/summary.md` and Steps
> 1–4 (already merged) for context. This step adds user-facing documentation
> for the new branch info bar to `docs/icoder/icoder.md`. End with one
> commit; pylint + mypy + pytest must still pass (no code changes
> expected — docs only).

## WHERE

```
docs/icoder/icoder.md   (modify — add new section)
```

## WHAT

Add a new section titled **"Branch Info"** between "Status Line" and
"Slash Commands". Include:

- A short description of the row's purpose.
- A table of the four info fields (Branch · State, Issue, PR, Cache age)
  with example values and the placeholder semantics (`…`, `?`, `—`,
  `(no git)`, `(no issue)`).
- A table of the three buttons with their action.
- A "Update cadence" subsection listing 2s / 30s / branch-change / on-click.
- A note that PR lookup is **off by default**, not persisted, and
  **gated behind the toggle** (refresh-PR button still fires regardless).

## HOW

- Mirror the existing section style in `docs/icoder/icoder.md` (markdown
  tables, short paragraphs).
- No screenshots required.
- Cross-link from `docs/iCoder.md` only if the existing structure already
  cross-links other sections.

## ALGORITHM

N/A — content authoring.

## DATA

N/A.

## Tests

No new code tests. Re-run pytest to confirm nothing regressed; pylint + mypy
should be unaffected. Manually re-render the markdown locally to spot-check
formatting.
