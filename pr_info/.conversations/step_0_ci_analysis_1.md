# CI Failure Analysis

The CI pipeline failed on the file-size check job. The check enforces a maximum of 750 lines per file, and the file `tests/workflows/vscodeclaude/test_status.py` now has 837 lines, exceeding the limit by 87 lines.

This file grew beyond the threshold as part of implementing issue #413 (adding the `get_folder_git_status()` function). The implementation plan in `pr_info/steps/step_1.md` instructed adding a new test class `TestGetFolderGitStatus` to the existing test file, which pushed it over the 750-line limit.

To fix this, the test file needs to be split into smaller, focused test modules. The current file contains multiple test classes (`TestStatusDisplay`, `TestCacheAwareFunctions`, `TestGetNextActionBlocked`, `TestGetFolderGitStatus`) that could be separated into individual files such as `test_status_display.py`, `test_cache_aware.py`, `test_next_action.py`, and `test_folder_git_status.py` within the same `tests/workflows/vscodeclaude/` directory. Alternatively, the file could be added to `.large-files-allowlist` as a temporary measure, though the preferred approach is refactoring to keep test files maintainable.