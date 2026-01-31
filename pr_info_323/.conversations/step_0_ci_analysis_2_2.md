# CI Failure Analysis

The CI pipeline failed in the file-size job because two files exceed the maximum allowed line count of 750 lines. The file size check command `mcp-coder check file-size --max-lines 750 --allowlist-file .large-files-allowlist` reported the following violations:

1. `tests/utils/vscodeclaude/test_orchestrator.py` - 837 lines (87 lines over the limit)
2. `src/mcp_coder/utils/vscodeclaude/orchestrator.py` - 783 lines (33 lines over the limit)

These files are part of the vscodeclaude feature implementation and were not added to the `.large-files-allowlist` file, which contains a list of grandfathered files that are permitted to exceed the line limit.

To fix this issue, there are two options: (1) refactor the violating files to reduce their line counts below 750 lines, which is the preferred approach for maintainability, or (2) add the files to `.large-files-allowlist` as a temporary measure if refactoring cannot be done immediately. Given that the orchestrator module is new code from the vscodeclaude feature implementation, the best approach would be to split the orchestrator.py file into smaller, focused modules (e.g., extracting helper functions or classes into separate files) and correspondingly organize the test file to match the new structure.