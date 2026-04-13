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

### Step 1: Define config schema with FieldDef dataclass

Detail: [step_1.md](./steps/step_1.md)

- [ ] Implementation: add `FieldDef` dataclass, `_CONFIG_SCHEMA`, `_get_field_def()` helper, and tests
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `config: add FieldDef dataclass and _CONFIG_SCHEMA`

### Step 2: Return native TOML types, validate at load time, and update bool-field callers

Detail: [step_2.md](./steps/step_2.md)

- [ ] Implementation: remove `str()` coercion in `_get_nested_value`, add schema validation in `get_config_values`, replace `_get_standard_env_var` usage with schema lookup, update `get_cache_refresh_minutes` for native int
- [ ] Implementation: update bool-field callers (`cli/utils.py`, `coordinator/core.py`, `mlflow_config_loader.py`) from `== "True"` to `is True`
- [ ] Implementation: update all test mocks from string booleans to native booleans, update `test_mlflow_config.py`, `test_utils.py`, `test_core.py`, `test_mlflow_integration.py`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `config: return native TOML types with schema validation and update bool callers`

### Step 3: Update int, list, and langchain callers for native types

Detail: [step_3.md](./steps/step_3.md)

- [ ] Implementation: update `vscodeclaude/config.py` for native `int` (max_sessions) and native `list` (setup_commands)
- [ ] Implementation: remove env var override loop in `langchain/__init__.py`
- [ ] Implementation: update type annotations in `jenkins_operations/client.py` and `github_operations/base_manager.py`
- [ ] Implementation: update test mocks in `test_config.py` and `test_langchain_provider.py`
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `config: update int, list, and langchain callers for native types`

### Step 4: Schema-driven verify_config rewrite

Detail: [step_4.md](./steps/step_4.md)

- [ ] Implementation: rewrite `verify_config()` to walk `_CONFIG_SCHEMA` with `_verify_section` and `_verify_wildcard_repos` helpers
- [ ] Implementation: delete `_SECTION_ENV_VARS`, `_get_source_annotation()`, and `_get_standard_env_var()`
- [ ] Implementation: update existing verify tests for schema-driven output format, add tests for type mismatch, unknown key, missing required, absent section
- [ ] Quality checks pass: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared: `config: rewrite verify_config to walk schema`

## Pull Request

- [ ] PR review: verify all 4 steps committed and clean
- [ ] PR summary prepared
