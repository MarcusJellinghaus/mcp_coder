# Step 14 — `refresh_pr_description` + prompt

## Precondition (check first)
Call `mcp__mcp-tools-py__get_library_source("mcp_workspace.github_operations.pr_manager.PullRequestManager.update_pull_request")`.
If it is not found, write one line to `pr_info/.blocked.txt`
(`Blocked: PullRequestManager.update_pull_request missing (MarcusJellinghaus/mcp-workspace#349)`) and stop.
If it is found but `pyproject.toml` pins an `mcp-workspace` version that predates it, raise the pin in this step.

## LLM prompt
> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_14.md` exactly, starting with its precondition.
> Write the tests first, then the code and prompt.
> Run pylint, pytest (fast unit set, `-n auto`), mypy and lint-imports; all must pass. Format the code and make exactly one commit.

## WHERE
- `src/mcp_coder/workflow_steps/pr_description.py`
- `src/mcp_coder/prompts/prompts.md` — new `#### PR Description Refresh` right after `#### PR Summary Generation` (~line 148)
- `tests/workflow_steps/test_pr_description.py`

## WHAT
```python
def refresh_pr_description(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> bool:
    """Refresh the open PR's title/body from the full branch diff. Best-effort, never raises.

    Returns:
        True if the PR was updated, False if unchanged, skipped or failed.
    """
```

## ALGORITHM
```
prs = PullRequestManager(pd).find_pull_request_by_head(branch); if not prs: warn; return False
pr = mgr.get_pull_request(prs[0]["number"]); base = detect_base_branch(pd, current_branch=branch)
diff = get_branch_diff(pd, base_branch=base, exclude_paths=["pr_info/"]); empty diff or no base -> return False
text = prompt_llm(prompt(pr_title, pr_body, diff), provider, timeout=300, ...)["text"].strip()
if text.upper().startswith("UNCHANGED"): log; return False
title, body = parse_pr_summary(text); for n in closing_issue_numbers(pr["body"]): body = ensure_closing_reference(body, n)
return bool(mgr.update_pull_request(pr["number"], title=title, body=body))
```
Whole body in `try/except Exception` → `logger.warning("PR description refresh failed (non-blocking): %s", e)`; return False.

## HOW
- Imports: `PullRequestManager` (`mcp_coder.mcp_workspace_github`), `get_branch_diff` (`mcp_coder.mcp_workspace_git`),
  `detect_base_branch` (`mcp_coder.workflow_utils.base_branch`), `prompt_llm` (`mcp_coder.llm.interface`),
  `prepare_llm_environment` (`mcp_coder.llm.env`), `get_prompt_with_substitutions` (`mcp_coder.prompt_manager`),
  `PROMPTS_FILE_PATH` (`mcp_coder.constants`), `get_branch_name_for_logging` (`mcp_coder.utils.git_utils`).
  Same `prompt_llm` keyword set as `generate_pr_summary`.
- `update_pull_request` returns `{}` on GitHub error → `bool({})` is False.
- Prompt (`[pr_title]`, `[pr_body]`, `[git_diff_content]` placeholders): same TITLE/BODY format and RULES as
  "PR Summary Generation"; "If the current title and body still describe the diff accurately, reply with exactly
  `UNCHANGED` and nothing else."
- Never changes a label.

## Tests (write first)
Patch at `mcp_coder.workflow_steps.pr_description.*`.
- LLM returns `TITLE:/BODY:` → `update_pull_request` called with parsed title and a body that still contains
  `Closes #12` taken from the current body; returns True.
- Current body closes #12 and #13 → both kept.
- LLM returns `UNCHANGED` → no update; False.
- No open PR → False, no LLM call.
- Empty diff → False, no LLM call.
- LLM raises → False, warning logged.
- `update_pull_request` returns `{}` → False.
- Prompt header "PR Description Refresh" loads from the real `prompts.md` and contains all three placeholders.

## DATA
`bool`.
