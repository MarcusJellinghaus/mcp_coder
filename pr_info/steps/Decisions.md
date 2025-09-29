# Decisions Made During Project Plan Review

## Implementation Structure Decisions

### Step Organization
- **Decision**: Expand from 8 to 10 steps with smaller, more manageable tasks
- **Rationale**: Original Steps 3-5 were too large (4 methods + tests each), smaller steps provide faster feedback
- **Result**: Each step now has 2-3 methods maximum with immediate testing

### Testing Approach  
- **Decision**: Implementation + unit tests together in each step, with real integration tests
- **Rationale**: Tests close to implementation provide fast feedback (very important requirement)
- **Result**: Steps 3-8 each include both implementation and unit testing

### Integration Testing Strategy
- **Decision**: Single evolving integration test across Steps 4, 6, 8 building full issue lifecycle  
- **Rationale**: Integration tests are VERY IMPORTANT (explicitly emphasized), single test avoids complexity
- **Result**: 
  - Step 4: create_issue → get_issue → close_issue → reopen_issue
  - Step 6: enhance with label operations (add → remove → set labels)
  - Step 8: enhance with comment operations (add → edit → delete comment)

### Error Handling Strategy
- **Decision**: Hybrid error handling approach
- **Rationale**: Need clear failure signals for auth issues while maintaining consistency with existing code
- **Result**: 
  - Raise exceptions for authentication/permission errors
  - Return empty dict/list for other errors (consistent with PullRequestManager)
  - Integration tests fail clearly with exceptions on permission issues

## Data and Scope Decisions

### Data Model Completeness
- **Decision**: Keep all planned IssueData fields (number, title, body, state, labels, user, created_at, updated_at, url, locked)
- **Rationale**: Comprehensive from start preferred over minimal MVP approach
- **Result**: Full TypedDict definitions implemented in Step 1

### Testing Coverage Level
- **Decision**: KISS approach for unit tests - essential coverage only
- **Rationale**: Focus on integration tests for validation, unit tests for basic functionality
- **Result**: Unit tests cover happy path + basic error handling + input validation only

### Implementation Priority  
- **Decision**: Full feature set in single implementation cycle
- **Rationale**: Prefer complete solution over incremental MVP approach
- **Result**: All issue operations (CRUD), label management, comment management in Steps 1-10

## Technical Implementation Decisions

### Method Grouping
- **Decision**: Logical grouping based on functionality and dependencies
- **Rationale**: get_available_labels needed as input for add_labels, reopen_issue belongs with issue lifecycle
- **Result**:
  - Step 5: get_available_labels + add_labels (input dependency)
  - Step 4: create_issue + close_issue + reopen_issue (complete lifecycle)

### Integration Test Organization
- **Decision**: Keep integration tests in same file, enhance across steps
- **Rationale**: Single evolving test is simpler than multiple test files or shared test utilities
- **Result**: One comprehensive integration test file that grows in Steps 4, 6, 8, 10


## New Decisions from Project Plan Review Discussion

### Integration Testing Approach
- **Decision**: Single evolving integration test (Option A)
- **Discussion**: User confirmed preference for single test creating only one GitHub issue across all test phases
- **Rationale**: Meets constraint of creating only one test issue, simpler and more robust
- **Result**: Keep existing plan for single integration test that grows in Steps 4, 6, 8, 10

### Label Operations Structure
- **Decision**: Keep separate methods for label operations (Option A)  
- **Discussion**: User chose separate methods over consolidated approach
- **Rationale**: Explicit API is worth the small amount of extra code
- **Result**: Maintain add_labels, remove_labels, set_labels as distinct methods

### Authentication and Test Repository
- **Decision**: Use existing github_test_setup fixture and user config system
- **Discussion**: User confirmed dedicated test repo and token exist, accessible via user config
- **Rationale**: Existing system works well for PullRequestManager and LabelsManager tests
- **Result**: Follow same authentication patterns as existing GitHub operations tests

### Rate Limiting Strategy
- **Decision**: No special rate limiting handling (Option A)
- **Discussion**: User confirmed existing tests work fine without special handling
- **Rationale**: Current approach with existing PR/Labels tests is sufficient
- **Result**: Use same simple approach as existing integration tests

### BaseGitHubManager Usage
- **Decision**: Inherit from BaseGitHubManager instead of copying code
- **Discussion**: User corrected the approach - "Do not copy BaseGitHubManager, USE it"
- **Rationale**: Inheritance provides code reuse, automatic updates, consistency with existing managers
- **Result**: IssueManager inherits from BaseGitHubManager, significantly simplifying Steps 2-3

### GitHub Enterprise Support
- **Decision**: Plan for configurable base URL but implement later
- **Discussion**: User preferred Option B (basic GitHub Enterprise support) but then said "Let's go back... Don't worry about this now"
- **Rationale**: Focus on current implementation, enhance GitHub Enterprise support later
- **Result**: Use existing BaseGitHubManager as-is, GitHub Enterprise support as future enhancement

### Issue Summary Method
- **Decision**: Skip get_issue_summary method for now (Option B)
- **Discussion**: User chose to focus on core functionality first
- **Rationale**: Keep current plan focused, add summary method later if needed
- **Result**: No additional summary method in current implementation

### Step Organization
- **Decision**: Keep current step organization (Option A)
- **Discussion**: User confirmed current organization is fine despite Step 3 being lighter
- **Rationale**: Good to have some lighter steps for variety and feedback points
- **Result**: Maintain existing 10-step structure without rebalancing
