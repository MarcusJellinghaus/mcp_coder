# Implementation

The `implement` workflow works through the plan step by step, with quality checks and a commit after each step.

## Labels

| Label | Category |
|---|---|
| `status-05:plan-ready` | bot_pickup |
| `status-06:implementing` | bot_busy |
| `status-07:code-review` | human_action |
| `status-17:code-review-bot` | bot_pickup |

`status-05:plan-ready` → `status-06:implementing` → `status-07:code-review`

With `auto_review_implementation` on (default off, see [configuration](../../configuration/config.md)), success goes to `status-17:code-review-bot` instead. See [Code review](07-code-review.md).

## Actor

Fully automated. The coordinator dispatches `implement` on Jenkins (`WORKFLOW_MAPPING`).

**Quality gates:**

- All code changes are validated through **pylint** → **pytest** → **mypy**, by the LLM and by routine when implementation is done.
- Formatting with the project's configured formatter.
- Git commits only after all checks pass.

**Iteration:**

- The plan contains several steps; implementation loops over them.
- Each step starts with a fresh context.

**Output:** Implemented code with all quality checks passed.

**Process:**

- Updates `TASK_TRACKER.md` with implementation steps
- Implements each step from the tracker
- Runs quality checks (pylint → pytest → mypy) after each step
- Formats code with the project's configured formatter
- Commits changes with descriptive messages
- Uses prompts ([prompts.md](../../../src/mcp_coder/prompts/prompts.md)):
  - [Implementation Prompt Template](../../../src/mcp_coder/prompts/prompts.md#implementation-prompt-template-using-task-tracker)
  - [Task Tracker Update](../../../src/mcp_coder/prompts/prompts.md#task-tracker-update-prompt)
  - [Mypy Fix](../../../src/mcp_coder/prompts/prompts.md#mypy-fix-prompt)

**Alternative paths:**

- Plan issues discovered → return to `status-04:plan-review`.
- Critical blocker, fundamental redesign needed → return to `status-02:awaiting-planning`.

## Slash commands

| Command | Purpose | Resulting label |
|---|---|---|
| [`/implementation_finalise`](../../../.claude/skills/implementation_finalise/SKILL.md) | Finish open tasks after a failed run | — |
| [`/commit_push`](../../../.claude/skills/commit_push/SKILL.md) | Format, review, commit and push in one command | — |
| [`/check_branch_status`](../../../.claude/skills/check_branch_status/SKILL.md) | Check CI, rebase need, tasks and labels (auto-launched by the failure labels) | — |

## Failure exits

Recovery for all: fix the cause, then `mcp-coder gh-tool set-status status-05:plan-ready`.

| Label | Cause | Recovery |
|---|---|---|
| `status-06f:implementing-failed` | General implementation failure | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-ci:ci-fix-needed` | CI exhausted 3 fix attempts | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-timeout:llm-timeout` | LLM API timeout during implementation | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-prep:task-tracker-prep-failed` | Task tracker preparation failed | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-mcp:mcp-unavailable` | MCP server unavailable during implementation | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-nochange:no-changes-after-retries` | LLM produced no file changes after 3 retry attempts | `mcp-coder gh-tool set-status status-05:plan-ready` |
| `status-06f-blocked:implementation-blocked` | Agent wrote `pr_info/.blocked.txt` — it could not verify the work and refused to claim it | `mcp-coder gh-tool set-status status-05:plan-ready` |

## Additional prompt details

#### Detailed Implementation Process

( TODO - TO BE REVIEWED )

**Preparing for implementation:**

##### 4.1 Task Tracker Update Prompt

See: [Task Tracker Update Prompt](../../../src/mcp_coder/prompts/prompts.md#task-tracker-update-prompt) in `src/mcp_coder/prompts/prompts.md`

- commit afterwards with

  ```
  TASK_TRACKER.md with implementation steps and PR tasks updated
  ```

**Objective:** Complete each implementation step with full validation

Each step consists of two main phases:

##### 4.2 Code Implementation and Quality Validation

**Process:**

- Implement the required functionality
- Follow TDD practices where applicable
- Run comprehensive quality checks
- Fix all issues until checks pass

**Quality Validation Steps:**

- **Run pytest:**
  - Execute all tests
  - Check for side effects (test files, temporary data)
  - Ensure cleanup - no remaining artifacts after test completion
  - Fix any test failures
- **Run pylint:**
  - Check code quality and style
  - Resolve any issues found
- **Run mypy:**
  - Perform type checking
  - Fix type-related issues

**Context Length Considerations:**

- **Preferred:** Complete all implementation and validation in one conversation
- **If context limit reached:** Acceptable to run mypy checks and fixes separately
- **Less preferred but possible:** Run pytest and pylint separately if needed

**Tools:**

- Run all checks (pylint, pytest, mypy) via MCP tools

**Implementation Prompt Template using task tracker**

See: [Implementation Prompt Template using task tracker](../../../src/mcp_coder/prompts/prompts.md#implementation-prompt-template-using-task-tracker) in `src/mcp_coder/prompts/prompts.md`

Possible follow up question:

```
Did you implement everything of the current step?
Do you have a commit message?
Did you tick of the tasks in the task tracker?
```

**Common Implementation Failures & Responses:**

- **Checks do not work**
  - Sometimes, mypy tests were forgotten and do not work:
    - Prompt

      ```
      Please run mypy checks and work on possible issues and fix it.
      ```

    - run pylint and pytest after that
    - run formatter after that
    - commit with auto and/or with mypy fixing info, or ask session for a commit message

      ```
      Please provide a concise commit message  in markdown code format (```)
      ```

      - triple ticks might or might not be provided
      - Claude might add a useless footer:

        ```
         🤖 Generated with [Claude Code](https://claude.ai/code)

          Co-Authored-By: Claude <noreply@anthropic.com>
        ```

- **Third-party dependencies needed:**
  - New Python packages required beyond current `pyproject.toml`
  - Dependencies not available in project's virtual environment
  - *Response:* Update `pyproject.toml` dependencies, run `pip install -e .[dev]` to reinstall project with new requirements

- **Implementation gets stuck in a certain step**
  - Working prompt:

    ```
    Please take a look at 
    pr_info/TASK_TRACKER.md
  
    The next step could not be implemented
  
    Do you know why?
    Please analyse carefully.
    ```

- **Implementation doesn't work:**
  - *Analyze root cause:* Ask for real issue details
  - *Too big:* Break down into several smaller tasks
  - *Too complex:* Simplify approach, create multiple files
  - *Incorrect task description:* May need implementation with next task
  - *Third-party library issues:* Library doesn't work as expected, causes confusion
  - *Response:* Fix issue, improve task description, update plan
  - *Initial technology evaluation missing* Add a step 0 to evaluate a technology. Execute that, update plan

- **Implementation works but requires no changes:**
  - Task was unnecessary or already implemented
  - *Response:* Mark as complete, update plan for remaining tasks
  
- **Check for slower and slower unit tests**

- **Check for file / folder / module names**
  - Files or folders might have wrong location or names. Eg test files should follow the same folder structure like the code.

**Possible prompt for too complex task**

```
Please look at pr_info/TASK_TRACKER.md and pick the next task that should be done.
Please let me know on which task you are working on.

Actually, please do not work on the task right now.

Rather review the task (and the summary and the related code base etc)
And tell me what needs to be done
Please tell me whether this is feasible, how complicated it is, whether it could be simplified or whether it needs to broken down in several sub tasks.
```

##### 4.3 One shot tasks

( still to be done)

##### 4.4 Working with Todos

Put some todos in your code and work on them using

```commandline
Please take a look
[this file]

There are many todos in there - please take the first one, can we work on just the first one
Tell me what needs to be done, do not yet modify any code!
```

##### 4.5 Commit Preparation

**Process:**

- format
- get commit message
  - Parse commit message from chat conversation
  - If no commit message found, auto create one
- commit changes

**Commit Message Prompt when working on a step:**

```
Please provide a short concise commit message stating the step name in the title.
```

**Commit message prompt after a small change:**

```
Can you provide a short commit message with short info on relevant changes?
```

This could benefit from `format_and_commit` tool.

**Tools:**

- `mcp-coder commit auto` - to commit all changes with a commit message generated via LLM from the git diff
