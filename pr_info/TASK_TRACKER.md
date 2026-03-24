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

### Step 1: Create `_http.py` — Shared httpx Client Factory
- [x] Implementation: `_http.py` (SSL context + httpx client factories) + tests in `test_langchain_http.py` + conftest update
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add Error Classification and Diagnostics to `_exceptions.py`
- [x] Implementation: `classify_connection_error()`, `format_diagnostics()`, `_is_connection_reset()` + tests in `test_langchain_diagnostics.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3A: Inject HTTP Clients into OpenAI Backend
- [x] Implementation: pass `http_client`/`http_async_client` to `ChatOpenAI`/`AzureChatOpenAI` + tests in `test_langchain_openai.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3B: Inject HTTP Clients into Anthropic Backend
- [x] Implementation: pass `http_client`/`http_async_client` to `ChatAnthropic` + tests in `test_langchain_anthropic.py`
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4A: Inject HTTP Clients into Model Listing (`_models.py`)
- [ ] Implementation: pass `http_client` to `openai.OpenAI()` and `anthropic.Anthropic()` + tests in `test_langchain_models.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 4B: Document Gemini SDK Limitation
- [ ] Implementation: add limitation comment to `gemini_backend.py` + test in `test_langchain_gemini.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5A: Improve Verify Command Failure Output
- [ ] Implementation: guard classification in `verify.py` except block + tests in `test_verify_orchestration.py`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5B: Add httpx Dependency and mypy Override
- [ ] Implementation: add `httpx>=0.27.0` to langchain extras + mypy override in `pyproject.toml`
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request
- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
