# Implementation Decisions Log

## File Structure Decision
**Decision**: Use `src/mcp_coder/prompts/prompts.md` as a single comprehensive documentation file
- **Rationale**: User wants to write lengthy markdown with prompts, documentation, experiences, and other information mixed together
- **Alternative considered**: Multiple separate prompt files or directory structure
- **Impact**: Simpler structure, single source of truth, easier maintenance

## Header Level Support
**Decision**: Support any header level (`#`, `##`, `###`, `####`) when matching prompts
- **Rationale**: More flexible for comprehensive documentation with varied structure
- **Implementation**: `get_prompt("Short Commit")` matches both `# Short Commit` and `#### Short Commit`

## Duplicate Header Handling
**Decision**: Raise `ValueError` when duplicate headers are found
- **Rationale**: Prevents ambiguity and catches accidental mistakes
- **Scope**: Check duplicates both within files and across files in directory
- **Error format**: Include all duplicate locations with file names and line numbers

## Cross-File Duplicate Detection
**Decision**: Use virtual file concatenation approach
- **Rationale**: Simplifies logic by turning multi-file problem into single-string problem
- **Implementation**: Read all `.md` files, concatenate content, run single parsing logic
- **Benefit**: Automatic cross-file duplicate detection with simpler code

## Validation Strategy
**Decision**: Two-level validation approach
- **Level 1**: `validate_prompt_markdown(single_file)` - validates individual file
- **Level 2**: `validate_prompt_directory(directory)` - validates all files + cross-file duplicates
- **Return format**: Detailed dict with `{"valid": bool, "errors": [list]}`
- **Purpose**: Provide actionable information for fixing files

## Flexible Input Handling
**Decision**: Support wildcards and auto-detection in `get_prompt()`
- **File path**: `"prompts/prompts.md"`
- **Directory**: `"prompts"` auto-expands to `prompts/*.md`
- **Wildcard**: `"prompts/*"` or `"prompts/*.md"`
- **String content**: Actual markdown text (auto-detected)
- **Detection heuristic**: If contains newlines or starts with `#`, treat as content; otherwise file path

## Error Handling Philosophy
**Decision**: Fail completely on parsing errors, keep it simple
- **Rationale**: Markdown should be well-formed, no complex error recovery needed
- **Exception types**: `ValueError` for content issues, `FileNotFoundError` for missing files
- **Approach**: Clear error messages, but no partial results or graceful degradation

## Testing Strategy
**Decision**: Unit tests only, no separate integration tests
- **Rationale**: Simpler approach, test both file paths and string content in same test suite
- **Test data**: Use StringIO or plain strings for test content
- **Coverage**: Reasonable coverage without being excessive
- **Integration**: Test real file functionality within unit tests, not separate test file

## Implementation Approach
**Decision**: Keep 3-step implementation plan
- **Step 1**: Core implementation + comprehensive unit tests
- **Step 2**: Package integration + file creation + validation functions
- **Step 3**: Documentation + final validation
- **Rationale**: Manageable chunks, clear progression, maintains TDD approach

## Markdown Format Specification
**Decision**: Keep format specification simple for now
- **Format**: Headers followed by code blocks with triple backticks
- **Parsing**: Simple regex-based approach
- **Assumptions**: Well-formed input, no complex edge case handling initially
- **Future**: Can enhance format specification later if needed
