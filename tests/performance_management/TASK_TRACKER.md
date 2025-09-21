# Performance Test Management - Task Tracker

## Instructions for LLM

This tracks **Performance Analysis Workflow** consisting of multiple **Analysis Steps** (tasks).

**Workflow Process:** See [complete_workflow.md](./complete_workflow.md) for detailed steps, prompts, and commands.

**How to update tasks:**
1. Change [ ] to [x] when analysis step is fully complete
2. Change [x] to [ ] if task needs to be reopened
3. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Analysis step complete
- [ ] = Analysis step not complete

---

## Current Analysis Tasks

### Phase 1: Data Gathering
- [x] **Step 1**: Run Initial Performance Analysis
  - Execute: `.\tools\pytest_wf_1_gather_slow_tests.bat`
  - Review generated output file in `tests/performance_management/output/`

### Phase 2: LLM Analysis
- [x] **Step 2**: Analyze Slow Test Data with LLM
  - Use LLM prompt from complete_workflow.md with the generated output file
  - Identify top 10 slowest tests and patterns
  - Get optimization recommendations and marker strategy
  - Update `slow_tests_inventory.md` and `performance_analysis.md` with findings

### Phase 3: Marker Analysis
- [ ] **Step 3**: Analyze Test Markers
  - Execute: `.\tools\pytest_wf_4_analyze_markers.bat`
  - Review the generated marker analysis output file
  - Update `slow_tests_inventory.md` with current marker usage patterns

### Phase 4: Implementation
- [ ] **Step 4**: Implement Optimizations
  - Apply recommended optimizations to slow tests
  - Add appropriate markers to tests based on analysis
  - Refactor test code based on analysis recommendations

### Phase 5: Validation
- [ ] **Step 5**: Validate Improvements
  - Execute: `.\tools\pytest_wf_10_validate_improvements.bat`
  - Review the validation output comparing before/after performance
  - Document improvements achieved in `performance_analysis.md`

### Phase 6: Documentation & Cleanup
- [ ] **Step 6**: Update Final Documentation
  - Update `performance_analysis.md` with final results and lessons learned
  - Clean up temporary output files
  - Archive completed analysis data

### Phase 7: Reset
- [ ] **Step 7**: Reset Task Tracker
  - Reset all checkboxes to [ ] for next analysis cycle
  - Update analysis cycle information
  - Archive completed analysis
