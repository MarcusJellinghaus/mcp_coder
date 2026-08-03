# Step 8 — Remove dead `*-rounds` labels; verify `core.py` < 600

See `pr_info/steps/summary.md` (§"Goal", §"Module layout"). The cap no longer routes to a
rounds failure label (Step 6), so `plan_review_rounds` / `code_review_rounds` are
unreachable. Remove them everywhere and confirm the line-count budget.

## PRE-MERGE SWEEP (must run before this step lands)
`mcp-coder gh-tool define-labels` **deletes** `status-*` labels absent from config, so any
open issue carrying `status-14f-rounds` / `status-17f-rounds` would lose its status label.
Sweep for such issues (e.g. MarcusJellinghaus/mcp-tools-sql#44) and `set-status` them to
`status-14:plan-review-bot` / `status-17:code-review-bot` first.

## WHERE (7 files)
- `src/mcp_coder/workflows/review/config.py` — remove `"rounds"` from both `failure_labels`
  dicts (`REVIEW_IMPLEMENTATION` and `REVIEW_PLAN`).
- `src/mcp_coder/config/labels.json` — remove the two entries `plan_review_rounds`
  (`status-14f-rounds:...`) and `code_review_rounds` (`status-17f-rounds:...`).
- `docs/processes-prompts/development-process.md` — remove the two `*-rounds` recovery rows
  (lines around the `14f-rounds` / `17f-rounds` table entries).
- `docs/processes-prompts/github_Issue_Workflow_Matrix.html` — remove the two
  `status-...-rounds` label cards (`14f-r`, `17f-r`).
- `tests/config/test_label_config.py` — remove `plan_review_rounds` / `code_review_rounds`
  expectations.
- `tests/cli/commands/test_define_labels.py` — remove the two `*-rounds` label-name
  expectations.
- `tests/workflows/review/test_config.py` — remove `"rounds"` from the expected
  `failure_labels` (mirrors the config change).

## HOW
- `_fail` uses `config.failure_labels.get(reason, config.failure_labels["general"])`, so
  dropping the `"rounds"` key is safe even if a stray path passes `"rounds"` — it falls back
  to `general`. Confirm no live path still passes `"rounds"` to `_fail` after Step 6.
- Grep the repo for `rounds` label ids to confirm nothing else references them:
  `plan_review_rounds`, `code_review_rounds`, `14f-rounds`, `17f-rounds`.

## ALGORITHM
_None — data/doc/test deletion._

## DATA
`failure_labels` for both lanes: `{"general", "timeout", "mcp_unavailable"}` (+ `"ci"` for
implementation). No `"rounds"` key. `labels.json` no longer defines the two `*-rounds`
labels.

## TDD / VERIFY
- Label tests updated first, then the config/JSON/doc removals, so the suite stays green.
- Run `mcp-coder check file-size --max-lines 600` and confirm
  `src/mcp_coder/workflows/review/core.py` is **under 600 lines** (final AC). If it is still
  over, the remaining lever is relocating another cohesive helper — but with `_set_label`,
  `_fail` (Step 4), the note helpers (Step 2), and the cap/escalate dedup (Step 6), it
  should be comfortably under.
- Full review test suite green; `test_define_labels` / `test_label_config` pass without the
  rounds labels.

## LLM PROMPT
> Implement Step 8 from `pr_info/steps/step_8.md` (see `pr_info/steps/summary.md`). First
> confirm the pre-merge sweep note is handled. Remove the `"rounds"` key from both
> `failure_labels` dicts in `workflows/review/config.py`; remove the `plan_review_rounds`
> and `code_review_rounds` label entries from `config/labels.json`; remove their rows/cards
> from `docs/processes-prompts/development-process.md` and
> `github_Issue_Workflow_Matrix.html`; and remove their expectations from
> `tests/config/test_label_config.py`, `tests/cli/commands/test_define_labels.py`, and
> `tests/workflows/review/test_config.py` (tests first). Grep to confirm no remaining
> references. Verify `core.py` < 600 with `mcp-coder check file-size --max-lines 600`. Run
> pylint, pytest (`-n auto` with integration exclusions), and mypy; all must pass. One commit.
