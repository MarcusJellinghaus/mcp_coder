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

### Step 1: Shipped Default Prompts + `prompt_loader.py` Module with Tests
> [Detail](./steps/step_1.md) — New `mcp_coder.prompts` package: `prompt_loader.py`, shipped defaults, `get_prompts_config()` in `pyproject_config.py`, `.importlinter` update

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 2: Add `project_dir` to Interface + Load Prompts in `prompt_llm()` / `prompt_llm_stream()`
> [Detail](./steps/step_2.md) — `interface.py` gains `project_dir` param, calls `load_prompts()`, passes results to providers

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 3: Langchain Provider — Prepend System Messages
> [Detail](./steps/step_3.md) — `ask_langchain()` accepts `system_prompt`/`project_prompt`, builds `SystemMessage` objects, prepends to message lists

- [x] Implementation (tests + production code)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

### Step 4: Claude Provider — Accept and Inject System Prompts via CLI Flags
> [Detail](./steps/step_4.md) — `build_cli_command()` gains `--append-system-prompt`/`--system-prompt` flags, CLAUDE.md redundancy detection, prompt concatenation in `interface.py`

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 5: CLI `prompt` Command — `--add-system-prompts` Flag
> [Detail](./steps/step_5.md) — Add flag to parser, wire `project_dir` to `prompt_llm()`/`prompt_llm_stream()` conditionally

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 6: iCoder — Pass `project_dir` for Prompt Injection
> [Detail](./steps/step_6.md) — `RealLLMService` gains `project_dir`, iCoder always injects prompts

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

### Step 7: `verify` Command Prompt Check + iCoder `/info` Prompt Paths
> [Detail](./steps/step_7.md) — PROMPTS section in `verify` output, prompt paths in `/info` command

- [ ] Implementation (tests + production code)
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review — verify all steps integrated correctly
- [ ] PR summary prepared
