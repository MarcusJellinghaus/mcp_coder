# Enable ruff ANN (without ANN401) — Implementation Summary

Issue: #1171. Adds ruff's `ANN` annotation rule group with `ANN401` (bans `Any`)
excluded. 421 of 485 current `ANN*` hits are `ANN401`, concentrated at
legitimate library/CLI boundaries — excluded project-wide, mypy strict already
covers what `ANN401` would add. The remaining 64 are real missing annotations,
all but one in `tests/`.

## Architectural / design changes

- **Two new shared test-double helpers**, replacing 4 + 3 near-duplicate
  implementations:
  - `tests/langchain_doubles.py` (new, top-level under `tests/`): one
    parameterized `make_scripted_chat_model(next_message, llm_type)` factory
    that builds a `BaseChatModel` test double. Replaces 4 structurally
    identical classes (`_ScriptedModel`, `_FakeChatModel`, `_TwoCallModel`,
    `_LoopingModel`) that only differed in which messages they returned per
    invoke. Callers supply that difference as a one-line `next_message`
    callback; the shared factory owns the `bind_tools`/`_generate`/
    `_agenerate` boilerplate once, with real `langchain_core` types instead of
    the current `# type: ignore[no-untyped-def]`.
  - `unavailable_command_stub` added to the existing
    `tests/cli/commands/conftest.py`: one function replacing 3 identical
    `def execute_x(*args, **kwargs): # type: ignore` import-fallback stubs.
- **Why top-level `tests/langchain_doubles.py` and not `tests/utils/` or
  `tests/llm/`**: `.importlinter`'s `test_module_independence` contract
  forbids `tests.icoder` and `tests.llm` from importing each other (the
  scripted-model duplication exists today *because* of this boundary — see
  `approval_harness.py`'s docstring). A module outside every package named in
  that contract lets both sides import the same helper with **zero
  `.importlinter` changes**, since no edge is created between the two
  independent packages.
- **No other structural change.** The remaining 64 - 7 (3 stubs) - 10
  (scripted-model `_generate`/`_agenerate` params) = standalone sites get
  direct annotations in place, mirroring the real signature they stand in for
  (CLI `execute_*` → `argparse.Namespace`, `open()` replacement, a
  conftest-declared fixture type). No new abstractions for those.
- `ANN401` stays off project-wide; no new `ANN` suppressions anywhere.

## Sequencing

The `pyproject.toml` rule-group flip is the **last** step, after every
annotation site is already fixed. Until then `ruff` doesn't check `ANN` at
all, so every intermediate step stays green without temporary per-file
ignores.

## Files created

- `tests/langchain_doubles.py`
- `tests/test_langchain_doubles.py`

## Files modified

- `pyproject.toml` (ruff `[tool.ruff.lint]` select/ignore — step 7 only)
- `src/mcp_coder/llm/mlflow_logger.py` (step 1)
- `tests/llm/providers/langchain/approval_harness.py` (step 2)
- `tests/llm/providers/langchain/test_approval_integration.py` (step 2)
- `tests/icoder/test_icoder_permission_wiring.py` (step 2)
- `tests/cli/commands/conftest.py` (step 3)
- `tests/cli/commands/test_check_branch_status.py` (step 3)
- `tests/cli/commands/test_create_pr.py` (step 3)
- `tests/cli/commands/test_implement.py` (step 3)
- `tests/icoder/test_cli_icoder_parser.py` (step 4)
- `tests/icoder/test_event_log.py` (step 4)
- `tests/llm/providers/copilot/test_copilot_cli.py` (step 5)
- `tests/llm/providers/langchain/test_langchain_agent_streaming.py` (step 6)
- `tests/llm/providers/langchain/test_langchain_streaming.py` (step 6)

## Steps

1. `src/mcp_coder/llm/mlflow_logger.py` — add `-> None` to `__init__`.
2. Shared scripted-`BaseChatModel` factory; migrate 4 call sites.
3. Shared import-fallback stub; migrate 3 call sites.
4. Annotate the 2 icoder mock/stub-callable sites.
5. Annotate the 6 `test_copilot_cli.py` fixture-parameter sites.
6. Annotate the 2 `_RaisingAsyncIter.__init__` sites.
7. Flip `pyproject.toml`: select `ANN`, ignore `ANN401`; full verification.

Each step is one commit: code + tests + `ruff`/`mypy`/`pylint`/`pytest` passing.
