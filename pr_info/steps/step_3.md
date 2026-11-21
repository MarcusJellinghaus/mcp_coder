# Step 3: prompts explain the move markers

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_3.md` only (steps 1–2 are already done). Follow TDD: write the test first and see it fail, then edit the prompts. Respect the prompt-file constraints listed below exactly. Use the MCP tools for all file, check and git operations. When done, all checks listed below must pass. This step is exactly one commit.

## WHERE

- `src/mcp_coder/prompts/prompts.md`, the prompts `#### PR Summary Generation` and `#### PR Description Refresh`
- `tests/workflow_steps/test_pr_description.py`

## WHAT

No code. One sentence (a single line) is added to each prompt, and one phrase in the refresh prompt is reworded.

## HOW

1. In **both** prompts, insert the following line, followed by one blank line, directly above the line `Git diff to analyze:`:

   ```text
   The diff collapses moved code: lines like `# [moved from <file>: N lines not shown]`, `# [moved to <file>: N lines not shown]` and `# [moved: N lines not shown]` appear with a `+` or `-` diff prefix after a few preview lines of a moved block and stand for the rest of that block moved unchanged. If the marker names another file, describe the block as moved; if it names the file being diffed itself, describe the block as re-indented or reordered in place (e.g. wrapped in `try:`), not relocated. Never describe a marked block as an addition or removal.
   ```

2. In `PR Description Refresh`, change `still describe the full git diff below.` to `still describe the branch diff below.`

## Constraints (must hold, `prompt_parsing` depends on them)

- The sentence must be **one line**. No line may start with `#`–`#####` followed by a space: `prompt_parsing` treats such lines as headers even inside code blocks, and the same marker line in both prompts would make `get_prompt` raise a duplicate-header `ValueError` for every prompt. The markers stay inline mid-sentence in single backticks.
- No triple backticks inside the sentence.
- No literal placeholders `[git_diff_content]`, `[pr_title]`, `[pr_body]` in the new text. Other square brackets are fine.
- Leave the existing `## Summary` / `## Changes` lines alone.

## ALGORITHM

None.

## DATA

`get_prompt(str(PROMPTS_FILE_PATH), name)` for either prompt returns text that contains `moved from`. All existing placeholders are still present.

## Tests (write first)

In `tests/workflow_steps/test_pr_description.py`, next to `test_refresh_prompt_has_placeholders`:

```python
@pytest.mark.parametrize("name", ["PR Summary Generation", "PR Description Refresh"])
def test_pr_prompts_explain_moved_markers(name: str) -> None:
    """Both PR prompts explain the compact diff's moved-code markers."""
    assert "moved from" in get_prompt(str(PROMPTS_FILE_PATH), name)
```

The existing `test_refresh_prompt_has_placeholders` must still pass.

## Checks

- `mcp__mcp-tools-py__run_format_code`
- `mcp__mcp-tools-py__run_pylint_check`
- `mcp__mcp-tools-py__run_mypy_check`
- `mcp__mcp-tools-py__run_pytest_check` with `extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not copilot_cli_integration and not install_integration and not jenkins_integration and not langchain_integration and not llm_integration and not setup_integration and not textual_integration"]`. The full unit run matters here: a header-parsing mistake breaks every `get_prompt` caller.

## Commit message

`feat(prompts): explain compact-diff move markers in PR prompts`
