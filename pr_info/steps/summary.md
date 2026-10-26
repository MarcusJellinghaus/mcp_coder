# Summary — Split `tests/llm/test_interface.py` (#1325)

Part of #353. Process: `docs/processes-prompts/refactoring-guide.md`.

## Goal
`tests/llm/test_interface.py` (2249 lines, allowlisted) is split into prefixed siblings in `tests/llm/`, one per interface concern. One misplaced class moves to `tests/prompts/test_prompt_loader.py`. After the split every touched file is under 600 lines, and `tests/llm/test_interface.py` is removed from `.large-files-allowlist`.

**Pure refactoring:** whole top-level classes move verbatim with `mcp__mcp-tools-py__move_symbol`. No logic edits, renames, merges or deletions of tests. No source (`src/`) change.

## Architectural / design changes
- **No production change.** `src/mcp_coder/llm/interface.py` is untouched. It stays a thin coordinator: `prompt_llm` / `prompt_llm_stream` validate the input, resolve the provider and dispatch to claude, langchain or copilot.
- **Test layout mirrors the source by concern.** One source module (`interface.py`) maps to one test *namespace*: `test_interface.py` plus `test_interface_<concern>.py` siblings. The concerns follow the source: the claude path of `prompt_llm`, the mlflow collaborator, `prompt_llm_stream`-only behaviour, `logs_dir` derivation, the langchain branch, system-prompt building and the copilot branch.
- **Base file role.** `test_interface.py` keeps the cross-function contract (`project_dir` required → cwd, unsupported-provider errors for both functions), the end-to-end mocked claude chain, and the shared constant `PROJECT_DIR`.
- **Shared constant.** `PROJECT_DIR` stays in `test_interface.py`. Siblings import it with `from tests.llm.test_interface import PROJECT_DIR` (precedent: `tests/llm/providers/langchain/test_langchain_agent_streaming_tool_output.py:5`). Siblings never import a `Test*` class, because pytest would then collect it twice.
- **Misplaced test.** `TestIsClaudeMd` tests `mcp_coder.prompts.prompt_loader.is_claude_md`, so it moves to that module's test file. Rule used: a test class belongs to the module whose function it *calls*.
- No `conftest.py`, fixture, marker, `.importlinter` or `tach.toml` change.

## Files

| File | Action | Classes after the split | Tests |
|---|---|---|---:|
| `tests/llm/test_interface.py` | modify (drained to the base) | `PROJECT_DIR`, `TestPromptLLMProjectDirRouting`, `TestIntegration`, the "integration tests removed" comment, `TestPromptLLMProjectDir`, `TestUnsupportedProviderListsAllProviders` | 10 |
| `tests/prompts/test_prompt_loader.py` | modify (receives 1 class) | + `TestIsClaudeMd` | 40 → 46 |
| `tests/llm/test_interface_prompt_llm.py` | create | `TestPromptLLMRouting`, `TestLLMTimeoutErrorNormalization`, `TestPromptLLM` | 26 |
| `tests/llm/test_interface_mlflow.py` | create | `TestMlflowConversationIntegration` | 6 |
| `tests/llm/test_interface_logs_dir.py` | create | `TestPromptLLMLogsDirDerivation`, `TestPromptLLMStreamLogsDirDerivation` | 6 |
| `tests/llm/test_interface_langchain.py` | create | `TestPromptLlmLangchainRouting` | 12 |
| `tests/llm/test_interface_stream.py` | create | `TestPromptLlmStream`, `TestPromptLlmStreamToolsParam` | 15 |
| `tests/llm/test_interface_system_prompts.py` | create | `TestPromptLlmInjectPrompts`, `TestBuildClaudeSystemPrompts` | 9 |
| `tests/llm/test_interface_copilot.py` | create | `TestPromptLlmCopilotRouting`, `TestCopilotSystemPromptHandling`, `TestCopilotTimeoutHandling`, `TestCopilotProviderValidation` | 8 |
| `.large-files-allowlist` | modify (step 7) | remove the line `tests/llm/test_interface.py` | — |

No folder is created. No other file changes (`docs/architecture/architecture.md:183` stays accurate).

## Steps (one commit each)

| Step | Move | `test_interface.py` count after |
|---|---|---:|
| 1 | `TestIsClaudeMd` → `tests/prompts/test_prompt_loader.py` (+ record baseline) | 92 |
| 2 | claude path of `prompt_llm` → `test_interface_prompt_llm.py` | 66 |
| 3 | mlflow → `test_interface_mlflow.py` | 60 |
| 4 | `logs_dir` → `test_interface_logs_dir.py` | 54 |
| 5 | langchain → `test_interface_langchain.py` | 42 |
| 6 | stream → `test_interface_stream.py` | 27 |
| 7 | system prompts → `test_interface_system_prompts.py` + allowlist removal | 18 |
| 8 | copilot → `test_interface_copilot.py` + full verification | 10 |

Invariant counts after every step: `tests/llm/` = 1391 (1397 before step 1), `tests/prompts/` = 46 (40 before step 1), whole suite = 6463. Record the real baseline in step 1. If it differs from these numbers, apply the same deltas to the recorded values.

TDD note: this is a pure move, so no new tests are written. The 98 existing tests are the safety net. Each step proves this with collect counts (nothing lost, nothing collected twice) and a passing unit run.

## Rules that apply to every step

### Allowed edits (everything else is forbidden)
- Import statements in the source and destination files.
- Removing section-banner comments that are left with nothing under them.
- The `.large-files-allowlist` line removal (step 7 only).
- Moving whole top-level statements unchanged, only as the last resort in "How to move" step 4 below.
- Nothing inside a class body changes: no `@patch` strings, method-local imports or decorators.
- `PROJECT_DIR`, its comment (lines 13–14) and the comment `# Real integration tests for LLM interface are removed` (3 lines, originally 488–490) stay in `test_interface.py` unchanged.
- No `pytestmark` is added (the original has none). New test files need no module docstring.

### How to move
1. Use only `mcp__mcp-tools-py__move_symbol`. Before every real call, run it with `dry_run=true`. The dry run must list exactly `tests/llm/test_interface.py` and that step's destination.
2. Use at most 3 symbols per call, listed in source order. Larger calls have timed out on other splits and left empty files.
3. Known tool behaviour:
   - It adds `from tests.llm.test_interface import PROJECT_DIR` to the destination.
   - It leaves method-local imports in place.
   - It removes source imports that become unused.
   - It leaves a blank-line-separated comment behind.
   - It decides where the moved block lands; leave it there.
4. If code lands wrong, try at most two other tool options (a different grouping or call order). Undo a failed attempt with `move_symbol` back to the source. Only after that, move whole top-level statements by hand without changing them.
5. After the move, run `mcp__mcp-tools-py__run_format_code` (it fixes `I001` in new import blocks). Then fix only what ruff `F401` or pytest collection reports.

### Checks (MCP tools only, no Bash)
`FAST_UNIT` = `not git_integration and not claude_cli_integration and not claude_api_integration and not copilot_cli_integration and not formatter_integration and not github_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not textual_integration`

- `run_format_code`, `run_ruff_check`, `run_pylint_check`, `run_mypy_check`.
- `run_pytest_check(extra_args=["-n", "auto", "-m", FAST_UNIT])` passes.
- Counts: `run_pytest_check(extra_args=["--collect-only", "-qq", "tests/llm", "tests/prompts"])` prints one `path: N` line per file. Directory totals are the sums. `run_pytest_check(extra_args=["--collect-only", "-q"])` gives the whole-suite total. If `-qq` prints no per-file lines, fall back to `--collect-only -q <file>` per file.
- Marker check: run the same `--collect-only -qq` call with `-m FAST_UNIT` over the files the step touched. The counts must equal the unfiltered counts, so no moved test drops out of the CI unit job.
- `mcp__mcp-workspace__check_file_size` passes. Every touched file is under 600 lines.
- Compact diff (`mcp__mcp-workspace__git` `diff`, `compact=true`). It may show only suppressed moved blocks, import lines, new-file headers, blank-line hunks and (step 7) the allowlist line. No hunk may appear in a test body, `PROJECT_DIR`, the comments or the module docstring.
- Commit: run `run_format_code`, then `git add` and `git commit` with the message given in the step.

### Failure handling
Whenever a step says "blocked", write one line describing the cause to `pr_info/.blocked.txt` and stop. Do not commit, and do not try to repair it by hand. Triggers in every step:
- A dry run or real call lists or changes any other file.
- `move_symbol` times out or reports `Token <…> cannot be matched`.
- A test body, decorator, `@patch` string or method-local import changes.
- `PROJECT_DIR` or a comment leaves `test_interface.py`.
- A collect count differs from the step's expected value.
- A test that passed before fails after the move.
- A hand edit outside the allowed-edits list would be needed.
