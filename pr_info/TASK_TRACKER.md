# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Key-order test for `verify_langchain` — [step_1.md](./steps/step_1.md)

- [x] Implementation: add `test_langchain_verify_row_order.py` pinning today's row order (no production change)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move `_load_langchain_config` to `_config_source.py` — [step_2.md](./steps/step_2.md)

- [x] Implementation: move `TestLoadLangchainConfig` to `test_langchain_config_source.py` and retarget patches; create `_config_source.py`; update `_setup.py`, `__init__.py`, `verification.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move `_resolve_session_id` into `__init__` — [step_3.md](./steps/step_3.md)

- [x] Implementation: retarget `require_langchain_history` patches; move `_resolve_session_id` into `__init__.py`; strip unused imports and update docstring in `_setup.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: `resolve_target` imports `_create_chat_model` from `._setup` — [step_4.md](./steps/step_4.md)

- [x] Implementation: retarget `resolve_target` chat-model patches to `_setup._create_chat_model`; change lazy import; fix `validate` docstring/comment
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Split `verification.py` into `_provider_checks.py` — [step_5.md](./steps/step_5.md)

- [x] Implementation: add `test_langchain_provider_checks.py` and `test_langchain_verification_mcp_split.py`, retarget patches; create `_provider_checks.py` with `check_provider`; slim `verification.py`; update `verify_sections.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Product texts move to `_product.py` — [step_6.md](./steps/step_6.md)

- [x] Implementation: create `_product.py` with four constants; replace literals in backends, `_models`, `_preflight`, `_config_diagnostics`, `_errors_404`, `_provider_checks`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: Import-linter contracts for the model layer — [step_7.md](./steps/step_7.md)

- [ ] Implementation: add `langchain_model_layer` and `langchain_model_layer_ancestors` contracts to `.importlinter`; raise `import-linter>=2.15` in `pyproject.toml`; sanity-check both contracts bite
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 8: Architecture documentation for the LangChain model layer — [step_8.md](./steps/step_8.md)

- [ ] Implementation: add `### LangChain model layer` subsection to `docs/architecture/architecture.md`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: review the full branch diff against `main`
- [ ] PR summary prepared
