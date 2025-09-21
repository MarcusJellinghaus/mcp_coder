# Performance Test Management - Task Tracker

## Instructions for LLM

This tracks **Performance Analysis Workflow** consisting of multiple **Analysis Steps** (tasks).

**Workflow Process:** See [complete_workflow.md](./complete_workflow.md) for detailed steps, prompts, and commands.

**How to update tasks:**
1. Change [ ] to [x] when analysis step is fully complete
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Analysis step complete
- [ ] = Analysis step not complete

---

## Current Analysis Tasks

### Phase 1: Data Gathering
- [x] **Step 1**: Run Initial Performance Analysis
  - Execute: `.\tools\pytest_wf_1_gather_slow_tests.bat`
  - Review generated output file
  - Status: Complete - Generated slow_tests_20250921_180813.txt

### Phase 2: LLM Analysis
- [ ] **Step 2**: Analyze Slow Test Data with LLM
  - Use LLM prompt from complete_workflow.md
  - Identify top 10 slowest tests and patterns
  - Get optimization recommendations
  - Status: Not started

### Phase 3: Marker Analysis
- [ ] **Step 3**: Analyze Test Markers
  - Execute: `.\tools\pytest_wf_4_analyze_markers.bat`
  - Review current marker usage
  - Status: Not started

### Phase 4: Implementation
- [ ] **Step 4**: Implement Optimizations
  - Apply recommended optimizations to slow tests
  - Add appropriate markers to tests
  - Refactor test code based on analysis
  - Status: Not started

### Phase 5: Validation
- [ ] **Step 5**: Validate Improvements
  - Execute: `.\tools\pytest_wf_10_validate_improvements.bat`
  - Compare before/after performance
  - Document improvements achieved
  - Status: Not started

### Phase 6: Documentation & Cleanup
- [ ] **Step 6**: Update Final Documentation
  - Update `performance_analysis.md` with results
  - Document lessons learned
  - Clean up temporary output files
  - Status: Not started

### Phase 7: Reset
- [ ] **Step 7**: Reset Task Tracker
  - Reset all checkboxes to [ ] for next analysis cycle
  - Update analysis cycle information
  - Archive completed analysis
  - Status: Not started

---

## Analysis Cycle Information
- **Last Analysis Date**: [Not started]
- **Output File**: [Will be generated]
- **Key Findings**: [To be documented]

## Next Steps
Follow the workflow in `complete_workflow.md` starting with Step 1.
