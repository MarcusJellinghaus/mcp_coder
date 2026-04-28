# Step 4 — Decommission langchain SSL plumbing

## LLM prompt

> Read `pr_info/steps/summary.md` and `pr_info/steps/step_4.md`. Implement Step 4
> exactly as specified. This step removes redundant call sites and obsolete
> tests in lockstep — they must change together because removing the import
> from `langchain/__init__.py` invalidates patch targets like
> `patch("mcp_coder.llm.providers.langchain.ensure_truststore")`. Run pylint,
> pytest (fast unit pattern), mypy, and lint-imports. All must pass. This is
> one commit.

## WHERE

- Deleted: `src/mcp_coder/llm/providers/langchain/_ssl.py`
- Modified (source): `src/mcp_coder/llm/providers/langchain/__init__.py`,
  `src/mcp_coder/llm/providers/langchain/_models.py`
- Modified (tests):
  - `tests/llm/providers/langchain/test_langchain_models.py`
  - `tests/llm/providers/langchain/test_langchain_provider_system_messages.py`
  - `tests/llm/providers/langchain/test_langchain_streaming.py`
  - `tests/llm/providers/langchain/test_langchain_streaming_timeout.py`
  - `tests/llm/providers/langchain/test_langchain_agent_timeout.py`

## WHAT

### Source removals

1. **`langchain/__init__.py`**:
   - Remove `from ._ssl import ensure_truststore`.
   - Remove the 4 `ensure_truststore()` call sites (currently around lines
     312, 418, 496, 650 — search the file for `ensure_truststore()` to locate
     them precisely).

2. **`langchain/_models.py`**:
   - Remove `from ._ssl import ensure_truststore`.
   - Remove the 3 `ensure_truststore()` call sites (currently around lines 47,
     83, 121 — one inside each of `list_gemini_models`, `list_openai_models`,
     `list_anthropic_models`).

3. **Delete** `src/mcp_coder/llm/providers/langchain/_ssl.py`.

### Test removals

1. **`test_langchain_models.py`**:
   - Delete the entire `TestListModelsEnsureTruststore` class (3 test methods
     asserting `mock_ts.assert_called_once()`).
   - Drop any other `patch(f"{_MODELS}.ensure_truststore")` mocks in the file.

2. **`test_langchain_provider_system_messages.py`**:
   - Delete the entire `TestEnsureTruststoreCalled` class (2 test methods).
   - Drop any other `patch(f"{_MOD}.ensure_truststore")` mocks in the file.

3. **`test_langchain_streaming.py`**, **`test_langchain_streaming_timeout.py`**,
   **`test_langchain_agent_timeout.py`**:
   - Drop `patch(f"{_MOD_LC}.ensure_truststore")` lines from the `with (...)`
     mock stacks. The remaining mocks in each `with` block stand on their own.

## HOW

- Sequence: do the source removals first, then the test removals. After the
  source removal, any test that still patches
  `mcp_coder.llm.providers.langchain.ensure_truststore` will fail with
  `AttributeError: ... does not have the attribute 'ensure_truststore'` — that
  signals which test files still need cleanup.
- Use `mcp__workspace__edit_file` with targeted `old_string` / `new_string`
  edits for each call site and each mock line.
- Use `mcp__workspace__delete_this_file` for `_ssl.py`.

## ALGORITHM

For each langchain caller of `ensure_truststore()`:
- Locate the line in the function body.
- Remove the line; preserve surrounding blank-line spacing where it improves
  readability, otherwise leave one blank line.

For each test mock:
- Remove the `patch(...ensure_truststore...)` from the `with (...)` block,
  including the trailing comma if present.

For each obsolete test class:
- Delete the entire class block including the docstring and all methods.

## DATA

No data structure changes. No public API changes (the langchain package's
public symbols `ask_langchain` / `ask_langchain_stream` keep their signatures).

## TDD note

This step is "remove dead code." There are no new tests. The acceptance signal
is: the existing test suite (minus the deleted classes / mocks) passes
unchanged.

## Risks & checklist

- After removing `from ._ssl import ensure_truststore`, the name no longer
  exists on the `mcp_coder.llm.providers.langchain` module. Any test still
  patching it will fail at `patch.start()`. Use a project-wide search for
  `ensure_truststore` to find every mock that needs dropping (the 5 files
  listed above are exhaustive per the issue).
- `_ssl.py` has no other importers outside the langchain subpackage (the
  Step-2 relocation copied — not moved — its content; production code already
  reaches `ssl_setup` via `cli/main.py` after Step 3).

## Acceptance for this step

- `src/mcp_coder/llm/providers/langchain/_ssl.py` no longer exists.
- No `ensure_truststore` references remain inside
  `src/mcp_coder/llm/providers/langchain/**`.
- `TestListModelsEnsureTruststore` and `TestEnsureTruststoreCalled` no longer
  exist.
- No `patch(...ensure_truststore...)` calls remain in any test file.
- `pylint`, `pytest` (fast unit pattern), `mypy`, `lint-imports` all green.
