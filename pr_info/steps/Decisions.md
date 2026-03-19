# Decisions

## D1: Remove `method` field from `LLMResponseDict`
**Decision:** Remove the `method: str` field from the `LLMResponseDict` TypedDict and all places that set it (cli, api, langchain response construction).
**Rationale:** Consistent with removing the `method` concept entirely. No runtime code reads this field.

## D2: Explicitly include `CIFixConfig.method` in step 2e
**Decision:** Explicitly call out removal of `method: str` from the `CIFixConfig` dataclass in `implement/core.py`.
**Rationale:** Completeness — the field was implicitly covered but should be explicitly listed to avoid being missed.

## D3: Remove `method` param from logging utils AND fix `claude_code_api.py` calls
**Decision:** Remove the `method` parameter from all three logging functions in `logging_utils.py`, and update the calls in both `claude_code_cli.py` and `claude_code_api.py` to match the new signatures.
**Rationale:** More thorough cleanup. Even though `claude_code_api.py` is not being deleted, its logging calls should be updated to avoid broken internal state.

## D4: Add langchain routing unit test
**Decision:** Add a mock-based unit test that verifies `prompt_llm(provider="langchain")` correctly routes to `ask_langchain()`.
**Rationale:** The reconstruction bug meant the langchain path was already broken for `create_plan`. A dedicated routing test provides confidence the fix works.
