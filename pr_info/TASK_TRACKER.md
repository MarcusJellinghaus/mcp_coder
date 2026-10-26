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

### Step 1: Record baseline; move `TestIsClaudeMd` to `tests/prompts/test_prompt_loader.py`
See [step_1.md](./steps/step_1.md)

- [x] Implementation: record baseline counts + marker check, move `TestIsClaudeMd` via `move_symbol` (dry run first)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Move claude path of `prompt_llm` to `tests/llm/test_interface_prompt_llm.py`
See [step_2.md](./steps/step_2.md)

- [x] Implementation: move `TestPromptLLMRouting`, `TestLLMTimeoutErrorNormalization`, `TestPromptLLM` via `move_symbol` (dry run first)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Move mlflow tests to `tests/llm/test_interface_mlflow.py`
See [step_3.md](./steps/step_3.md)

- [x] Implementation: move `TestMlflowConversationIntegration` via `move_symbol` (dry run first)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Move `logs_dir` derivation tests to `tests/llm/test_interface_logs_dir.py`
See [step_4.md](./steps/step_4.md)

- [x] Implementation: move `TestPromptLLMLogsDirDerivation`, `TestPromptLLMStreamLogsDirDerivation` via `move_symbol` (dry run first)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 5: Move langchain routing tests to `tests/llm/test_interface_langchain.py`
See [step_5.md](./steps/step_5.md)

- [x] Implementation: move `TestPromptLlmLangchainRouting` via `move_symbol` (dry run first); method-local imports stay in place
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 6: Move `prompt_llm_stream` tests to `tests/llm/test_interface_stream.py`
See [step_6.md](./steps/step_6.md)

- [x] Implementation: move `TestPromptLlmStream`, `TestPromptLlmStreamToolsParam` via `move_symbol` (dry run first)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 7: Move system-prompt tests to `tests/llm/test_interface_system_prompts.py`; remove allowlist entry
See [step_7.md](./steps/step_7.md)

- [x] Implementation: move `TestPromptLlmInjectPrompts`, `TestBuildClaudeSystemPrompts` via `move_symbol` (dry run first); remove `tests/llm/test_interface.py` from `.large-files-allowlist`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 8: Move copilot tests to `tests/llm/test_interface_copilot.py`; final verification
See [step_8.md](./steps/step_8.md)

- [x] Implementation: move copilot classes via `move_symbol` in two calls (8a: 3 classes, 8b: `TestCopilotProviderValidation`); final checks (lint-imports, tach, vulture, file size, counts, marker check, search check)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

## Pull Request

- [ ] PR review: compact diff against base branch shows only moved blocks, import changes, new-file headers, blank-line hunks and the allowlist line
- [ ] PR summary prepared
