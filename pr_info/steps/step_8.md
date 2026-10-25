# Step 8 — README pitch section

## LLM prompt

> Read `pr_info/steps/summary.md`, then do this step (`pr_info/steps/step_8.md`).
> Add a short pitch section to `README.md`, near the top and above the existing diagrams (before `## 🎯 Vision & Architecture`). Then point the overview's README link at the new anchor.
> Format, then commit as one commit.

## WHERE

```
README.md                                       (new section before line 16)
docs/processes-prompts/development-process.md   (link → README.md#<new-anchor>)
```

## WHAT

- New section `## Why a structured process` (≤ 15 lines). It pitches a well-structured, spec-driven-style process:
  - issue → refined spec → reviewed plan → implementation in small verified steps → reviewed code → PR;
  - each step leaves an artifact (issue text, `pr_info/steps/`, commits, review logs);
  - quality gates (pylint, pytest, mypy, CI) on every step;
  - you decide scope and merge; the rest can run unattended; failures come back as labelled issues;
  - link: [Development Process](docs/processes-prompts/development-process.md).
- Keep the existing intro (lines 3–14). Do not duplicate its bullets; merge or trim only where a sentence repeats the new section.
- In `development-process.md`, change the README link to `../../README.md#why-a-structured-process`.

## HOW / ALGORITHM / DATA

Markdown only, so there is no algorithm or data.

## Checks

- Run `tools/lychee_check.bat` via Bash: 0 errors.
- Format, then commit: `docs(readme): add structured-process pitch`.
