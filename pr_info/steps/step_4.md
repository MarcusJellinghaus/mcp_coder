# Step 4 — Fold `langchain-integration.yml` into `ci.yml`, with coverage

See [summary.md](summary.md) for the overall design.

## WHERE

- `.github/workflows/ci.yml` (add job)
- `.github/workflows/langchain-integration.yml` (delete)

## WHAT

No Python functions — workflow YAML only.

- Add a `langchain-integration` job to `ci.yml`, copying
  `langchain-integration.yml`'s existing job body (env secrets, checkout,
  `astral-sh/setup-uv`, `actions/setup-python`, install
  `.[dev,langchain]`, the `pytest tests/llm/providers/langchain/... -m
  langchain_integration` step, the `actions/upload-artifact@v4` for the
  junit XML).
- Add `if: github.event_name == 'pull_request' || (github.event_name ==
  'push' && github.ref == 'refs/heads/main')` to the job — this reproduces
  the old workflow's `on: push: branches: [main]` / `pull_request:
  branches: [main]` restriction inside `ci.yml`'s broader
  `push: branches: ["**"]` trigger.
- Extend the pytest step with `--cov=src/mcp_coder --cov-report=` and
  `COVERAGE_FILE: .coverage.langchain`.
- Add an `actions/upload-artifact@v4` step for the coverage data file:
  `name: coverage-data-langchain`, `path: .coverage.langchain`,
  `retention-days: 1`.
- Delete `.github/workflows/langchain-integration.yml`.

## HOW

Same checkout action version as the rest of `ci.yml` (`actions/checkout@v6`
— the old workflow used `@v4`; align it with the rest of this file while
folding it in, since there's no reason for it to diverge once it's no
longer a separate file). Everything else copied as-is from the old
workflow body.

## ALGORITHM

N/A — job relocation plus the same `--cov`/artifact additions as step 3.

## DATA

N/A.

## Precondition that may not hold

The folded-in job depends on repository secrets
(`OPENAI_API_KEY`/`GEMINI_API_KEY`/`ANTHROPIC_API_KEY`/
`MCP_CODER_LLM_LANGCHAIN_BACKEND`/`MCP_CODER_LLM_LANGCHAIN_MODEL`) that
the standalone `langchain-integration.yml` already used successfully —
this step does not change what secrets are needed, so no new risk is
introduced. No blocked-file condition for this step.

## Verification

- Diff the new job body against the deleted file to confirm nothing was
  dropped beyond the trigger block (which the `if:` guard replaces) and
  the `checkout` version bump.
- Standard checks (pylint, pytest fast-unit selection, mypy) — this step
  doesn't touch src/tests code, so these should be unaffected.
- As in step 3, the workflow's own correctness is confirmed by the PR's
  Actions run, not a local test.

## Commit

One commit: the `ci.yml` addition and the file deletion together, message
e.g. `ci: fold langchain-integration.yml into ci.yml with coverage`.

## LLM prompt

> Implement Step 4 of [summary.md](summary.md). Move
> `langchain-integration.yml`'s job into `.github/workflows/ci.yml` as a
> `langchain-integration` job, guarded by an `if:` that reproduces its
> original push-to-main/pull-request trigger restriction, add
> `--cov=src/mcp_coder --cov-report=` with `COVERAGE_FILE:
> .coverage.langchain` to its pytest step, upload that file as artifact
> `coverage-data-langchain`, and delete the old workflow file. Run the
> project's standard checks and commit as one commit.
