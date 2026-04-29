# Step 1 — Promote `truststore` to core dependencies

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_1.md`. Implement Step 1
> exactly as specified. Run pylint, pytest (fast unit pattern with the
> `-m "not ..."` exclusion), mypy, and lint-imports. All must pass. This is one
> commit.

## WHERE

- `pyproject.toml`

## WHAT

- Move `"truststore>=0.9.0"` out of `[project.optional-dependencies] langchain-base`
  into the core `[project] dependencies` array.

## HOW

- Remove the `"truststore>=0.9.0"` line from the `langchain-base` extra (keep
  the other 4 entries: `langchain-core`, `langchain-mcp-adapters`, `langgraph`,
  `httpx`).
- Insert `"truststore>=0.9.0"` into the core `dependencies` list, alphabetically
  adjacent to similar runtime libs (e.g. between `tabulate>=0.9.0` and
  `textual>=1.0.0`, or wherever fits the existing ordering).
- Leave the `[[tool.mypy.overrides]] module = ["truststore"]` block (~line 305 in pyproject.toml) unchanged — truststore still lacks type stubs.

## ALGORITHM

Pure manifest edit — no algorithm.

## DATA

`pyproject.toml` is the only changed file. No source/test changes in this step.

## TDD note

A manifest change can't be TDD'd directly. The implicit test is that the
existing test suite still imports `truststore` successfully (it always could —
it's already an installed transitive dep in dev). Run the full quality gate to
confirm no regression.

## Acceptance for this step

- `truststore>=0.9.0` is in `[project] dependencies`.
- `truststore>=0.9.0` is no longer in `[project.optional-dependencies]
  langchain-base`.
- `pylint`, `pytest` (fast unit pattern), `mypy`, `lint-imports` all green.
