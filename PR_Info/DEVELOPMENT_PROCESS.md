# Development Process

## High-Level Overview

Structured development workflow for **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Process Flow:**
1. **Feature Planning** - Discuss with LLM, create implementation steps
2. **Implementation Steps** - Code + validate + prepare commits (repeat per step)
3. **Feature Completion** - Review + summarize entire feature

**Key Principles:**
- Each implementation step includes code, quality validation, and commit preparation
- Context length limitations may require splitting validation checks
- Tools automate git operations and provide LLM-ready prompts
- All validation must pass before proceeding

---

## Detailed Process Steps

### 1. Feature Planning

**Objective:** Break down feature into manageable implementation steps

**Process:**
1. **Create separate branch** for the feature development
2. **Initial analysis** - Understand existing solution and requirements
3. **Create implementation plan** - Generate summary and step-by-step breakdown
4. **Review and refine** - Discuss and optimize the plan
5. **Finalize plan** - Update all planning documents

**Implementation Flow:**
- Use **Implementation Task Coordinator** to manage n implementation prompts
- Execute all implementation steps through coordinated prompts
- Each step references summary and specific step details

**Outputs:**
- New feature branch
- Updated `TASK_TRACKER.md` with new tasks
- Individual step detail files (`steps/step_N.md`)
- Background documentation (`summary.md`)
- ( Future: Updated `Task_Tracker.md` )

**Tools & Prompts:**

#### Initial Analysis Prompt:
```
## Discuss implementation steps
Please take a look at the existing solution
Do you understand the task below?
What are the implementation steps?
Do not yet modify any code!
```

#### Implementation Plan Creation Prompt:
```
## Python Project Implementation Plan Request
Create a **summary** (`pr_info/steps/summary.md`) and **implementation plan** with self-contained steps (`pr_info/steps/step_1.md`, `pr_info/steps/step_2.md`, etc.).
Can you also give a summary of the architectural / design changes in the summary document?

### Requirements:
- Follow **Test-Driven Development** where applicable. 
  Each step should have its own test implementation followed by related functionality implementation.  
- Each step must include a **clear LLM prompt** that references the summary and that specific step
- Apply **KISS principle** - minimize complexity, maximize maintainability
- Keep code changes minimal and follow best practices

### Each Step Must Specify:
- **WHERE**: File paths and module structure
- **WHAT**: Main functions with signatures
- **HOW**: Integration points (decorators, imports, etc.)
- **ALGORITHM**: 5-6 line pseudocode for core logic (if any)
- **DATA**: Return values and data structures
```

**Issue:** This prompt generates way too many unit tests.

**Issue:** Hardcoded `pr_info` path does not help for sub-problems.
Simple hack:`pr_info2`. ( Could be also branch name or something?)

#### Plan Review Prompt:
```
Please review the project plan for a new feature in folder PR_Info\steps.
Please revise the project plan with a balanced level of detail.
Please let me know if any complexity could be reduced.
Please let me know any questions / comments or suggestions you might have.

Please consider the already discussed and decided decisions (if any) under decisions.
We do not need to challenge them again unless absolutely necessary.
```

**Issue Pyproject.toml requirements updates**:
```
In case of after updating the pyproject.toml requirements, 
put something in the project plan to stop and tell me, 
so that I can install the requiremetns. 
This is important so that unit tests can work.
```

Wait for presentation of overall plan
```
Can we go through all suggested changes and questions step by step?
You explain, ask and I answer until we discussed all topics?
Please offer, whenever possible, simple options like 
- A
- B
- C
```

Wait for end of discussion
```
Please summarise changes you want to do to the project plan for confirmation 
( one liner bullet points)
and
please ask me whether I agree (Y/N)
```

After the agreement:
```
Can you update the plan by updating the different files in folder `pr_info\steps`
Please do targeted changes.
Please log the decisions from our discussion in `PR_Info\steps\Decisions.md`
```

Possibly review the project plan one more time (see above) or continue with the next step.


### 2. Implementation Steps

**Preparing for implementation:**

#### Task Tracker Update Prompt:
```
Please read the implementation steps in `pr_info/steps/` and
update `pr_info/TASK_TRACKER.md` to add all the implementation steps as tasks in the Tasks section.

Follow the task format specified in the TASK_TRACKER.md file,
marking each step as incomplete [ ] and linking to the corresponding step file.

Review `pr_info/DEVELOPMENT_PROCESS.md` for context on the workflow and task requirements.

Each task should include the 3 quality checks (pylint, pytest, mypy) and
git commit preparation as outlined in the development process.

Also add the pull request tasks for PR review and summary creation at the end in a section "Pull request"
```

**Objective:** Complete each implementation step with full validation

Each step consists of two main phases:

#### 2.1 Code Implementation and Quality Validation

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
- `tools/checks2clipboard.bat` - **Primary tool**: Run all checks (pylint, pytest, mypy) and copy results to clipboard for LLM analysis
  - Handles test side effects checking
  - Provides structured output for LLM review
  - Sequential execution: pylint → pytest → mypy
  - Only proceeds if previous checks pass

**Implementation Prompt Template:**
```
Please review the implementation plan in PR_Info, especially the summary and steps/step_{XX}.md.
Please implement!
Please verify your implementation running the various checks of the MCP server and by solving potential issues (and repeat).
Please do not invent extra complexity not mentioned in the project plan.
Please let me know in case you encounter any issues or need a decision.
Please work only on step {XX}
```

or using task tracker

```
Please look at `pr_info/TASK_TRACKER.md` and pick the next task that should be done.
Please let me know on which task you are working on.
Please implement!
Please verify your implementation running the various checks of the MCP server and by solving potential issues (and repeat).
Please do not invent extra complexity not mentioned in the project plan.
Please let me know in case you encounter any issues or need a decision.
Please provide a short concise commit message stating the step name in the title. Don not perform a commit!
Once you are done, please check again that task description on `pr_info/TASK_TRACKER.md` to ensure that everything is done.
Once everything is done, please mark the task as done.
Please work only on one task. Do not pick further tasks.

Please also take a look at the tests\readme and only run those tests that are required in your context -i.e. avoid slow integration tests.
```

Possible follow up question:
```
Did you implement everything of the current step?
Do you have a commit message?
Did you tick of the tasks in the task tracker?
```

**Common Implementation Failures & Responses:**

- **Third-party dependencies needed:**
  - New Python packages required beyond current `pyproject.toml`
  - Dependencies not available in project's virtual environment
  - *Response:* Update `pyproject.toml` dependencies, run `pip install -e .[dev]` to reinstall project with new requirements

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
  
- ** Check for slower and slower unit tests **

** Possible prompt for too complex task**

```
Please look at pr_info/TASK_TRACKER.md and pick the next task that should be done.
Please let me know on which task you are working on.

Actually, please do not work on the task right now.

Rather review the task (and the summary and the related code base etc)
And tell me what needs to be done
Please tell me whether this is feasible, how complicated it is, whether it could be simplified or whether it needs to broken down in several sub tasks.
```




#### 2.2 Commit Preparation

**Process:**
- Parse commit message from chat conversation
- If no commit message found, ask user for commit message
- Create commit summary
- User performs manual commit

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
- `tools/format_all.bat` - Run all formatting tools (ruff, black, isort)
- `tools/commit_summary.bat` - Generate commit summary prompt with git diff and copy to clipboard
  - Includes both staged and untracked files
  - Provides structured format for commit message generation
  - Handles git status and diff extraction

### 3. Feature Completion

**Objective:** Review and document the completed feature

After all implementation steps are complete:

#### 3.1 Run more detailed checks

Run certain checks in an automated way and deal with possibly highlighted issues:
- Pylint warnings
- (custom checks - to be developed)
- Check pytest runtime


#### 3.2 PR Review

**Process:**
- Review the entire pull request for the feature via an LLM prompt
  - `tools/pr_review.bat` - Generate detailed PR review prompt with git diff
- Review of of LLM review output, possible further implementation steps (see above).

**Tools:**

#### 3.3 Create Summary

**Process:**
- Generate comprehensive feature summary
- Document what was implemented and why
- Create PR description for external review
- Clean up PR_Info folder

**Tools:**
- `tools/pr_summary.bat` - Generate PR summary creation prompt
  - Reads PR_Info folder context
  - Includes full git diff for comprehensive summary
  - Saves result as `PR_Info/summary.md`
  - Provides structured prompt for LLM summary generation
  - Cleans up development artifacts: deletes `steps/` subfolder and clears Tasks section from `TASK_TRACKER.md`

**Final Clean State:**
After feature completion, the cleaned `TASK_TRACKER.md` should contain only the template structure:
```markdown
# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Implementation Steps** (tasks).

**Development Process:** See [DEVELOPMENT_PROCESS.md](./DEVELOPMENT_PROCESS.md) for detailed workflow, prompts, and tools.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Implementation step complete (code + all checks pass)
- [ ] = Implementation step not complete
- Each task links to a detail file in PR_Info/ folder

---

## Tasks

```