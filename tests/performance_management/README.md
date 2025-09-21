# Performance Test Management Workflow

## 🚀 Quick Start Prompt
```
Review `tests/performance_management/TASK_TRACKER.md` and provide a concise summary of what the next incomplete task is and what you'll do. Then execute only that one step and stop.
```

---

This folder contains tools and documentation for managing slow test performance in our test suite.

## Folder Structure

- `workflow.md` - Step-by-step workflow for performance analysis
- `slow_tests_inventory.md` - Current inventory of slow tests with markers
- `performance_analysis.md` - Analysis results and recommendations
- `tools/pytest_wf_*` - Batch files for automated analysis (in tools folder)
- `prompts/` - LLM prompts for test analysis

## Quick Start

1. Follow the workflow in `workflow.md`
2. Run batch scripts to gather data
3. Use prompts with LLM to analyze results
4. Update inventory and recommendations

## Files Overview

### Core Workflow Files
- **workflow.md**: Complete step-by-step process
- **slow_tests_inventory.md**: Tracked slow tests with metadata
- **performance_analysis.md**: Analysis results and next steps

### Automation
- **.\tools\pytest_wf_1_gather_slow_tests.bat**: Extract slow test data
- **.\tools\pytest_wf_4_analyze_markers.bat**: Analyze test markers
- **.\tools\pytest_wf_10_validate_improvements.bat**: Post-optimization validation
- **prompts/slow_test_analysis.md**: LLM prompts for analysis
