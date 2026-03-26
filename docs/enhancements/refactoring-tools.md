# Refactoring Tools — Enhancement Ideas

Observations from first use of MCP refactoring tools on issue #592.

## `move_symbol`

### Import style: absolute instead of relative
When moving `is_git_repository` from `readers.py` to `repository_status.py`, the tool rewrites consumer imports as:
```python
import mcp_coder.utils.git_operations.repository_status
# ...
mcp_coder.utils.git_operations.repository_status.is_git_repository(project_dir)
```
Expected (matching existing codebase style — relative imports within package):
```python
from .repository_status import is_git_repository
# ...
is_git_repository(project_dir)
```

### Comment shuffling in `__init__.py`
Section comments (e.g. `# Repository status operations`) got separated from their corresponding imports during the move. The tool should preserve comment–import associations or leave unrelated lines untouched.

## `compact-diff`

### Separate committed vs uncommitted output
Currently has `--committed-only` flag. Consider also:
- `--uncommitted-only` — show only working tree changes (useful mid-refactoring to check just the latest move)
- Default behavior shows both, which can be noisy during incremental work

### Exclude patterns
Already supports `--exclude PATTERN`. Works well for filtering out non-code files (e.g. `--exclude "*.md"`).

### Missed consumers with fully-qualified imports
`move_symbol` updated files using relative imports (e.g. `from .readers import ...`) but missed files using fully-qualified absolute imports (e.g. `from mcp_coder.utils.git_operations.readers import ...`). Five files were left with stale imports that caused `ModuleNotFoundError` at test time.

## General

- Consider a `--relative-imports` flag on `move_symbol` to prefer relative imports within the same package.
- Consider a `--preserve-comments` or `--no-reformat` flag to avoid shuffling unrelated lines.
