# Step 2 — Merge system + project prompt into a single `SystemMessage`

**Goal:** Fix Issue 1. After this step a first turn against a single-system provider
works; turn 2 still breaks (that is Issue 2, fixed in steps 4–5).

## WHERE

* Modify `src/mcp_coder/llm/providers/langchain/__init__.py` — `_build_system_messages`
  (currently lines 47–68)
* Modify `tests/llm/providers/langchain/test_langchain_provider_system_messages.py`

`_build_system_messages` **stays in `__init__.py`** — see the summary: it has only two
call sites (both in this file), it was never a divergence source, and moving it would
churn five test imports for no benefit.

## WHAT

Signature unchanged:

```python
def _build_system_messages(
    system_prompt: str | None, project_prompt: str | None
) -> list[Any]: ...
```

Behaviour changes from "one message per prompt" to "at most one merged message".

## HOW

* No new imports. Update the docstring to describe the merge and the `"\n\n"` separator,
  and change `Returns:` to "List with at most one merged `SystemMessage` (may be empty)".
* Both call sites (`ask_langchain`, `ask_langchain_stream`) are unchanged — they already
  pass the returned list straight through.

## ALGORITHM

```
from langchain_core.messages import SystemMessage
parts = [p for p in (system_prompt, project_prompt) if p]
if not parts:
    return []
return [SystemMessage(content="\n\n".join(parts))]
```

## DATA

* both prompts → `[SystemMessage("<system>\n\n<project>")]`
* one prompt → `[SystemMessage("<that prompt>")]`
* neither / empty strings → `[]`

## Tests (update first)

In `test_langchain_provider_system_messages.py`:

1. Rename `test_both_prompts_produce_two_messages` →
   `test_both_prompts_produce_single_merged_message`: assert `len(msgs) == 1` and
   `msgs[0].content == "system instructions\n\nproject context"`.
2. `test_system_only`, `test_project_only`, `test_none_produces_empty_list`,
   `test_empty_strings_produce_empty_list` — unchanged, must still pass.
3. `test_system_messages_appear_first_in_invoke` — `len(call_args) == 3` → `== 2`
   (1 system + 1 human); assert the single system content is the merged string.
4. `test_system_messages_appear_first_in_stream` — same change for the streaming path.
5. `test_agent_mode_passes_system_messages` — expected content list
   `["sys", "proj"]` → `["sys\n\nproj"]`.

`test_langchain_agent_system_messages.py` needs **no** change here: it constructs two
`SystemMessage` objects by hand and passes them to `run_agent`, which is testing
prepending, not the merge.

## Merge-safety audit (part of this step)

Before committing, confirm nothing depends on receiving two separate system messages —
`_build_system_messages` is shared by all langchain backends (openai/gemini/anthropic/
ollama):

```
search_files(pattern="SystemMessage")
search_files(pattern="system_messages")
```

Expected finding (already spot-checked): only tests assert two; no production or backend
code does. Record the result in the commit message. If the audit turns up production code
that assumes two, **stop and report** rather than working around it.

## Checks

```
mcp__tools-py__run_pylint_check
mcp__tools-py__run_pytest_check(extra_args=["-n", "auto", "-m", "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"])
mcp__tools-py__run_mypy_check
```

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement step 2 only: make _build_system_messages in
src/mcp_coder/llm/providers/langchain/__init__.py return a single merged SystemMessage
(system prompt and project prompt joined with a blank line), and update the assertions
listed in the step file in
tests/llm/providers/langchain/test_langchain_provider_system_messages.py.

Update the tests first, watch them fail, then change the implementation. Also run the
merge-safety audit described in the step file and report its result in the commit
message. Leave _build_system_messages in __init__.py — do not move it.

Then run pylint, pytest and mypy via the MCP tools and fix anything they report.
Produce exactly one commit.
```

## Implementation note (step 2 run)

**pytest still could not be executed — the updated assertions are unverified.**

The `mcp-workspace` breakage recorded in [step_1.md](./step_1.md#implementation-note-step-1-run)
is unchanged: `src/mcp_coder/checks/branch_status.py:17` imports
`mcp_workspace.checks.branch_status_rendering`, which the test venv
(`C:\Jenkins\workspace\Windows-Agents\Executor\repo\.venv`) does not have. That import
runs at `import mcp_coder` time, so the whole suite fails at collection/import — the
"tests fail first" step could not be observed for the right reason, and the post-change
green run could not be obtained either. `pylint` and `mypy` report the same module as
unresolvable (`E0401` / `import-not-found`), confirming it is environmental.

Verified instead:

* **pylint**: only the project-wide baseline `E0401` deferred optional-dep imports
  (`langchain_core.messages`, `langchain_mcp_adapters`, `httpx`, `mcp.server.fastmcp`)
  plus the stale-`mcp_workspace` cascade (`E1123`/`E0611`/`E1101` in `branch_status`
  callers). Nothing new in the two files touched here.
* **mypy**: 8 pre-existing errors, all in `branch_status` / `create_pr` / `check_branch_status`
  callers of the stale package. None in `langchain/__init__.py` or the test file.
* **black / isort**: no changes.

**Re-run `pytest tests/llm/providers/langchain/test_langchain_provider_system_messages.py`
once `mcp-workspace` is reinstalled before trusting step 2 as green.**

### Merge-safety audit result

`search_files(pattern="SystemMessage")` and `search_files(pattern="system_messages")` over
the whole tree: **no production code assumes two system messages.** Every production
consumer treats the list as opaque and concatenates it —
`langchain/__init__.py:324` and `:629` (`(system_messages or []) + history + [Human]`),
`agent.py:402` and `:552` (same shape), `_messages.py:43`
(`result = list(system_messages or [])`). No backend module (openai/gemini/anthropic/
ollama) reads the list at all. The only two-message expectations were in tests:
`test_langchain_provider_system_messages.py` (updated here) and
`test_langchain_agent_system_messages.py`, which hand-builds its own two `SystemMessage`s
to test prepending and is deliberately untouched (Decisions.md #5).

One stale **doc** line was found and corrected in the same commit:
`docs/repository-setup/python.md:59` still described "Two `SystemMessage` objects".
