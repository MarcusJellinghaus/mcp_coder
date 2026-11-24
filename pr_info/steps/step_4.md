# Step 4: Docs — npm example and per-session grant scope

Read `pr_info/steps/summary.md` first (section "Design", part 4).

## LLM prompt

> Implement step 4 of `pr_info/steps/summary.md` as described in
> `pr_info/steps/step_4.md`. Edit only `docs/configuration/toolkits.md`. Other
> docs changes belong to issue #1453. Run pytest (unit markers excluded as in
> CLAUDE.md) in case a test reads the docs. Then commit as one commit.

## WHERE

- `docs/configuration/toolkits.md`

## WHAT

1. **npm example** (section `### npm`, around lines 300–327): delete
   - `[tool.mcp-coder.toolkit.command.format]` `check = …`;
   - `[tool.mcp-coder.toolkit.command.check]` `full = …` (all its lines);
   - `[tool.mcp-coder.toolkit.command.test]` `full = …` and `mutation = …`.

   Keep `format.apply`, `check.quick`, `check.standard`, `test.quick`, `test.standard` and `test.unattended`. Realign the `=` columns if needed.
2. **"Which sessions." bullet** under `### LLM access` (around line 230): replace "implement task and its fix calls, finalisation, CI fix (union of all grants), and rebase fix turns (…)" with the per-session scope:
   - implement task: the depths of `implement_task` and `implement_final`;
   - fix turns: the binding entry being fixed;
   - finalisation and CI fix: `implement_final`;
   - rebase fix turns: unchanged (the active rebase binding at the resolved depth).

   Add one sentence: a request that falls back grants the lower depth that runs, and the re-run list in the prompt lists exactly the granted commands.

## HOW / ALGORITHM / DATA

Docs only; no code. Keep the existing bullet style and line wrapping (about 80 columns).

## Tests

None new. If any test under `tests/` asserts content of `docs/configuration/toolkits.md` and fails, update that assertion to the new text.
