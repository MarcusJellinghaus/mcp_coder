# Step 2 — Automated Rebase prompt + drift test

Goal: add the automated-rebase prompt to `prompts.md` (SKILL.md minus the
confirmation step) and lock its conflict-strategy table in sync with SKILL.md.
One commit.

## WHERE
- MODIFY `src/mcp_coder/prompts/prompts.md` — add a `## Automated Rebase` section.
- CREATE `tests/workflows/rebase/test_prompt.py`.

## WHAT
A prompt retrievable via `get_prompt(str(PROMPTS_FILE_PATH), "Automated Rebase")`
(`PROMPTS_FILE_PATH` from `mcp_coder.constants`). Mirror the retrieval/format of
an existing entry (e.g. "CI Failure Analysis") so the loader test passes. The
prompt **body must be enclosed in a ``` fenced code block** under the header:
`get_prompt` extracts the code block that follows the header and raises if the
body is prose rather than a fenced block.

Prompt must instruct the LLM to:
1. `git status` first; fetch `origin`; rebase current branch onto `origin/<base>`
   (base is provided in the appended context).
2. **Capture baseline** pytest/pylint/mypy results **before** starting the rebase
   (needed for no-regression comparison).
3. Resolve conflicts per the strategy table (in sync with SKILL.md): `pr_info/`
   → `--theirs`; code/tests → additive merge; config → additive, prefer HEAD;
   lockfiles → accept `--theirs`. There is **no lockfile-regeneration step** —
   this repo has no tracked lockfile, so a lockfile conflict cannot arise. Any
   genuinely unfamiliar/unknown conflict → `git rebase --abort` with a
   human-readable reason (the generic abort rule already in the prompt).
4. Re-run all checks after the rebase; ensure **nothing regressed** vs. baseline
   (no-regression, not absolute-pass).
5. **Do NOT push.** Stop after a clean, verified rebase (Python performs the
   force-push).
6. On any unresolvable conflict / unfixable regression: restore the original
   branch state (`git rebase --abort`, or reset if the rebase already completed),
   then report `aborted`.
7. **Emit an outcome marker** as the final lines of the response:
   ```
   REBASE_OUTCOME: success        # or: aborted
   REBASE_REASON: <one-line human-readable reason; "n/a" on success>
   ```

## HOW
- No code imports change; the prompt is loaded by the orchestrator in Step 6.
- Canonical SKILL: `.claude/skills/rebase/SKILL.md`. Drift source of truth is the
  **packaged** copy at
  `find_data_file("mcp_coder", "resources/claude/skills/rebase/SKILL.md")`, a
  build-time artifact copied from the canonical file. This canonical→packaged
  duplication is the established convention here, so reading the packaged copy in
  the drift test is fine.

## DRIFT RECONCILIATION (lockfiles)
The packaged SKILL.md conflict-strategy table still has a lockfile row
(`Lockfiles … → Accept theirs (--theirs), notify user to regenerate`). To keep
the `issubset` drift test green with the simplest change, **keep a matching plain
lockfile row in the prompt** (accept `--theirs`, notify to regenerate) — no `uv
lock`. The prompt does not add a `uv lock` regeneration row.

## ALGORITHM (drift test)
```
skill = read packaged SKILL.md
prompt = get_prompt(PROMPTS_FILE_PATH, "Automated Rebase")
rows(x) = {normalize(line) for line in x.splitlines()
           if line.strip().startswith("|") and "---" not in line}
strat = rows under SKILL "## Conflict Resolution Strategies" heading
assert strat.issubset(rows(prompt))   # every SKILL strategy row present in prompt
```

## DATA
Prompt is a `str`. Marker lines are plain text parsed later by `_parse_outcome_marker`.

## TESTS (write first)
`test_prompt.py`:
1. `get_prompt(str(PROMPTS_FILE_PATH), "Automated Rebase")` returns a non-empty
   string (confirms the body is a fenced code block — `get_prompt` raises
   otherwise).
2. Prompt contains the marker tokens `REBASE_OUTCOME:` and `REBASE_REASON:`.
3. Prompt mentions the baseline-before-rebase ordering (e.g. asserts presence of
   both a "baseline"/"before" cue and "regress").
4. Drift: every conflict-strategy table row in the packaged SKILL.md appears in the
   prompt (algorithm above).

## LLM PROMPT
> Read `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`. Implement Step 2
> (TDD). First write `tests/workflows/rebase/test_prompt.py` covering: the
> `"Automated Rebase"` prompt loads via `get_prompt`, contains `REBASE_OUTCOME:`
> and `REBASE_REASON:`, references no-regression/baseline ordering, and that every
> conflict-strategy table row from the packaged SKILL.md
> (`resources/claude/skills/rebase/SKILL.md`) appears in the prompt. Then add a
> `## Automated Rebase` section to `src/mcp_coder/prompts/prompts.md` matching the
> retrieval/format of an existing prompt, with the body in a ``` fenced code block,
> encoding the workflow and marker contract in this step (SKILL.md minus the
> confirmation step; no lockfile-regeneration step; keep a plain lockfile row to
> satisfy the drift test; the LLM must NOT push and must emit the outcome marker).
> Run pylint, pytest (`-n auto`, unit markers), mypy; fix everything. Exactly one
> commit.
