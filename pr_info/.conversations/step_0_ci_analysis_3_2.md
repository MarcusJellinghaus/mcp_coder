# CI Failure Analysis

The CI pipeline failed the file-size check because tests/workflows/vscodeclaude/test_issues.py contains 1113 lines, exceeding the 750-line maximum threshold. This file is not currently in the .large-files-allowlist, which means it violates the project's code quality standards for file size.

The root cause is that test_issues.py has grown too large during development. The file contains comprehensive test coverage for VSCode Claude issue selection and filtering functionality, with multiple test classes covering various scenarios including issue filtering, priority ordering, branch checking, and caching. While the test coverage is thorough, the file size indicates it should be refactored into smaller, more focused test modules.

To resolve this CI failure, you have two options: (1) Refactor tests/workflows/vscodeclaude/test_issues.py by splitting it into multiple smaller test files organized by logical groupings (e.g., separate files for issue selection, priority ordering, branch operations, and caching tests), or (2) Add the file to .large-files-allowlist as a temporary measure if refactoring cannot be done immediately. The recommended approach is option 1, as it aligns with the project's code quality goals stated in the allowlist comment to "reduce over time per #353".

The unit-tests job failure mentioned in the context may be related, but based on this log excerpt, the immediate blocker is the file-size violation that must be addressed before the CI pipeline can pass.