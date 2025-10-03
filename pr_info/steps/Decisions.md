# Implementation Decisions Log

## Test Granularity Reduction
**Date**: Current discussion
**Decision**: Reduce test coverage target from 95% across all modules to 80% focused on critical paths

### Tests to Remove/Defer:
- Complex mypy retry logic with conversation saving
- Comprehensive JSON conversation data capture  
- All possible git error scenarios
- Detailed formatter failure modes
- Step number extraction from task names
- Progress summary formatting variations
- File path resolution edge cases
- Complex conversation filename collision handling
- Task tracker auto-population logic
- Identical mypy output detection
- Multiple LLM method switching

### Tests to Keep (High Priority):
- Git status validation (clean/dirty detection)
- Branch checking (not on main/master)
- Task tracker existence validation
- Project directory validation
- Main workflow loop orchestration
- Task retrieval from task tracker
- LLM integration (mocked responses)
- Git operations (commit, push) - basic success/failure
- Error handling and recovery paths
- Argument parsing validation
- CLI command routing
- Integration with existing CLI patterns

**Rationale**: Removes ~30% of test complexity while maintaining reliability for core workflow functionality, error conditions that break the workflow, CLI integration points, and git operation safety checks.
