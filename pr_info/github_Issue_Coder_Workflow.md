# GitHub Issue Workflow - Status Labels & Transitions

## Status Labels

### Waiting for User (Human Action Required)
- `status:created` - Fresh issue, may need refinement
  - **Color:** `#10b981` (Emerald)
- `status:plan-review` - First implementation plan available for review/discussion
  - **Color:** `#3b82f6` (Blue)
- `status:code-review` - Implementation complete, needs code review
  - **Color:** `#f59e0b` (Amber)
- `status:pr-created` - Pull request created, awaiting approval/merge
  - **Color:** `#8b5cf6` (Violet)

### Bot Needs Pickup (Bot Should Start Working)
- `status:awaiting-planning` - Issue is refined and ready for implementation planning
  - **Color:** `#6ee7b7` (Light Emerald)
- `status:plan-ready` - Implementation plan approved, ready to code
  - **Color:** `#93c5fd` (Light Blue)
- `status:ready-pr` - Approved for pull request creation
  - **Color:** `#fbbf24` (Light Amber)

### Bot Busy (Bot Is Actively Working)
- `status:planning` - Implementation plan being drafted (auto/in-progress)
  - **Color:** `#a7f3d0` (Lightest Emerald)
- `status:implementing` - Code being written (auto/in-progress)
  - **Color:** `#bfdbfe` (Lightest Blue)
- `status:pr-creating` - Bot is creating the pull request (auto/in-progress)
  - **Color:** `#fed7aa` (Lightest Amber)

**Final State:** Issue closed after PR approval/merge

## Workflow Transitions

### 0. → Created

- **Actor:** Developer using GitHub
- **Interface:** GitHub issue creation
- **Trigger:** Manual issue creation
- **Action:** Create new issue with initial description
- **Comment:** Issue is created with `status:created` label, ready for refinement

### 1. Created → Awaiting Planning

- **Actor:** Developer using GitHub
- **Interface:** Manual issue editing (description, comments) or label change
- **Trigger:** When issue details are sufficiently refined and clear
- **Action:** Refine issue description and change label to `status:awaiting-planning`
- **Comment:** Issue is now well-defined and ready for implementation planning

### 2. Awaiting Planning → Planning

- **Actor:** Bot (automating LLM)
- **Interface:** Automatic detection of `status:awaiting-planning` label
- **Trigger:** System detects label change and begins implementation plan drafting
- **Action:** Generate first draft of implementation plan using LLM
- **Comment:** Bot analyzes requirements and creates structured implementation approach

### 3. Planning → Plan Review

- **Actor:** Bot (automating LLM)
- **Interface:** Automatic plan generation completion
- **Trigger:** When first draft of implementation plan is ready
- **Action:** Post implementation plan and change label to `status:plan-review`
- **Comment:** Implementation plan is ready for human review and discussion

### 4. Plan Review → Plan Ready

- **Actor:** Developer using LLM
- **Interface:** Label change to `status:plan-ready` (with LLM chat support)
- **Trigger:** Manual approval after reviewing and discussing the implementation plan
- **Action:** Review plan with LLM assistance and approve by changing label
- **Comment:** Plan has been reviewed and approved for implementation

### 5. Plan Ready → Implementing

- **Actor:** Bot (automating LLM)
- **Interface:** Automatic detection of `status:plan-ready` label
- **Trigger:** System detects approval and begins code implementation
- **Action:** Execute implementation plan by writing code
- **Comment:** Bot begins coding according to the approved implementation plan

### 6. Implementing → Code Review

- **Actor:** Bot (automating LLM)
- **Interface:** Comment/notification when implementation is complete
- **Trigger:** “Implementation ready” signal from bot
- **Action:** Complete implementation and change label to `status:code-review`
- **Comment:** Implementation is complete and ready for human code review

### 7. Code Review → Ready PR

- **Actor:** Developer using LLM
- **Interface:** Label change to `status:ready-pr` (with LLM support for decision)
- **Trigger:** Manual decision that code is ready for pull request
- **Action:** Review code with LLM assistance and approve for PR creation
- **Comment:** Code has been reviewed and approved for pull request creation

### 8. Ready PR → PR Creating

- **Actor:** Bot (automating LLM)
- **Interface:** Automatic detection of `status:ready-pr` label
- **Trigger:** System detects approval and begins PR creation process
- **Action:** Prepare and initiate pull request creation
- **Comment:** Bot begins creating pull request with proper description and metadata

### 9. PR Creating → PR Created

- **Actor:** Bot (automating LLM)
- **Interface:** Automatic PR creation completion
- **Trigger:** When pull request has been successfully created
- **Action:** Complete PR creation and change label to `status:pr-created`
- **Comment:** Pull request has been created and is ready for team review

### 10. PR Created → Closed

- **Actor:** Developer using GitHub
- **Interface:** GitHub PR approval and merge
- **Trigger:** PR approval and merge automatically closes the issue
- **Action:** Review, approve, and merge the pull request
- **Comment:** Issue is resolved and closed after successful PR merge

## Improvement Ideas & Questions

### Default Labels

- **Question 0**: Can we define a default label for new issues?
- **Answer**: Yes, GitHub allows automatic label assignment via templates, workflows, or bot triggers on issue creation

### Process Types Analysis

- **Step 0**: Manual issue creation (with default `status:created` label)
- **Step 1**: Manual/human refinement
- **Step 2**: **Automated process** - Bot detects label change and starts planning
- **Step 3**: **Automated process** - Bot completes plan generation
- **Step 4**: **LLM conversation process** - Human discusses plan with LLM using prompts
- **Step 5**: **Automated process** - Bot detects approval and starts implementation
- **Step 6**: **Automated process** - Bot completes implementation
- **Step 7**: **LLM conversation process** - Human reviews code with LLM using prompts
- **Step 8**: **Automated process** - Bot detects approval and starts PR creation
- **Step 9**: **Automated process** - Bot completes PR creation

### Implementation Considerations

#### Default Label Setup

- Configure GitHub issue templates with `status:created` as default label
- Or use GitHub Actions to auto-assign label on issue creation
- Or use bot webhook to immediately add label when issue is created

#### LLM Conversation Processes (Steps 4 & 7)

- Need chat interface integrated with GitHub
- Require structured prompts for plan review and code review
- Should save conversation context in GitHub comments
- Need clear decision points to trigger label changes

#### Automation Reliability

- All automated steps need error handling and rollback mechanisms
- Need monitoring for stuck processes
- Should have timeout mechanisms for long-running tasks
- Need notification system for failed automation steps

## Alternative Paths

- **Actor:** Developer using LLM
- **Interface:** Label change back to earlier status (with LLM support)
- **Trigger:** Decision that more implementation work is needed
- **Action:** Change label back to `status:plan-ready` to restart implementation
- **Comment:** Code review identified issues requiring additional implementation work

### Code Review → Awaiting Planning (Complete Restart)

- **Actor:** Developer using LLM
- **Interface:** Label change back to planning phase
- **Trigger:** Decision that approach needs fundamental reconsideration
- **Action:** Change label back to `status:awaiting-planning` for complete restart
- **Comment:** Code review identified fundamental issues requiring new implementation plan