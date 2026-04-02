# Step 1: Logging Infrastructure — NOTICE→OUTPUT, CleanFormatter, setup_logging()

## LLM Prompt
> Read `pr_info/steps/summary.md` for full context. Implement Step 1: Rename NOTICE→OUTPUT, create CleanFormatter, update setup_logging() formatter selection, and update tests. Run all three code quality checks after changes.

## WHERE
- `src/mcp_coder/utils/log_utils.py` — main changes
- `src/mcp_coder/utils/__init__.py` — rename export
- `tests/utils/test_log_utils.py` — update + new tests

## WHAT

### 1a. Rename NOTICE → OUTPUT (`log_utils.py`)

**Note:** This is not just a rename — the semantics change. NOTICE was documented as "never log at this level" (threshold-only). OUTPUT is actively logged at via `logger.log(OUTPUT, ...)`. The new comment block reflects this intentional change.

**Constant and level registration:**
```python
# BEFORE
NOTICE = 25
logging.addLevelName(NOTICE, "NOTICE")

# AFTER
OUTPUT = 25
logging.addLevelName(OUTPUT, "OUTPUT")
```

Update the module docstring and comments: replace all "NOTICE" references with "OUTPUT". Update the comment block above the constant to explain the dual-formatter design:

```python
# Custom OUTPUT log level (between INFO=20 and WARNING=30)
# OUTPUT is the default CLI threshold. At this threshold, CleanFormatter
# produces bare messages; at INFO/DEBUG, ExtraFieldsFormatter produces
# verbose timestamped output. Use logger.log(OUTPUT, ...) for user-facing
# CLI messages that should be clean at default verbosity.
OUTPUT = 25
logging.addLevelName(OUTPUT, "OUTPUT")
```

### 1b. New `CleanFormatter` class (`log_utils.py`)

**Signature:**
```python
class CleanFormatter(logging.Formatter):
    """Formatter for clean CLI output.

    Used when log threshold is OUTPUT. Produces:
    - OUTPUT-level records: bare message (no prefix)
    - WARNING/ERROR/CRITICAL: "LEVEL: message"

    Extra fields (passed via extra={}) are appended as JSON,
    independently of ExtraFieldsFormatter.
    """

    def format(self, record: logging.LogRecord) -> str:
        ...
```

**Algorithm (format method):**
```
1. Format message using record.getMessage()
2. If record.levelno > OUTPUT: prepend "LEVELNAME: " prefix
3. Extract extra fields (same logic as ExtraFieldsFormatter)
4. If extra fields exist: append JSON suffix
5. Return formatted string
```

**Important:** Do NOT inherit from `ExtraFieldsFormatter`. Duplicate the extra-fields extraction logic independently.

### 1c. Update `setup_logging()` (`log_utils.py`)

In the console logging branch (the `else` block where no `log_file` is specified):

```python
# BEFORE (always uses ExtraFieldsFormatter):
console_formatter = ExtraFieldsFormatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# AFTER (threshold-dependent):
if numeric_level >= OUTPUT:
    console_formatter = CleanFormatter()
else:
    console_formatter = ExtraFieldsFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
```

### 1d. Update `__init__.py` export

```python
# BEFORE
from .log_utils import NOTICE, log_function_call, setup_logging

# In __all__:
"NOTICE",

# AFTER
from .log_utils import OUTPUT, log_function_call, setup_logging

# In __all__:
"OUTPUT",
```

### 1e. Tests (`tests/utils/test_log_utils.py`)

**Rename `TestNoticeLevel` → `TestOutputLevel`:**
- Change all `NOTICE` references to `OUTPUT`
- Update `from mcp_coder.utils.log_utils import (` to import `OUTPUT` instead of `NOTICE`
- Update assertions: `logging.getLevelName(25) == "OUTPUT"`, `OUTPUT == 25`
- Update `setup_logging("NOTICE")` → `setup_logging("OUTPUT")`

**New `TestCleanFormatter` class:**
```python
class TestCleanFormatter:
    """Tests for CleanFormatter class."""

    def test_output_level_no_prefix(self) -> None:
        """OUTPUT-level messages have no prefix."""
        # Create record at level OUTPUT (25), format it
        # Assert result == "Test message" (no prefix, no timestamp)

    def test_warning_level_has_prefix(self) -> None:
        """WARNING-level messages get 'WARNING: ' prefix."""
        # Create record at WARNING level, format it
        # Assert result == "WARNING: Test message"

    def test_error_level_has_prefix(self) -> None:
        """ERROR-level messages get 'ERROR: ' prefix."""
        # Create record at ERROR level, format it
        # Assert result == "ERROR: Test message"

    def test_extra_fields_appended_as_json(self) -> None:
        """Extra fields are appended as JSON."""
        # Create record at OUTPUT level with extra field
        # Assert JSON suffix is present

    def test_no_extra_fields_no_json(self) -> None:
        """No JSON suffix when no extra fields."""
        # Create record at OUTPUT level without extra fields
        # Assert no "{" in output
```

**New `TestSetupLoggingFormatterSelection` class:**
```python
class TestSetupLoggingFormatterSelection:
    """Tests for formatter selection based on threshold."""

    def test_output_threshold_uses_clean_formatter(self) -> None:
        """OUTPUT threshold should use CleanFormatter."""
        # Call setup_logging("OUTPUT"), check handler's formatter type

    def test_info_threshold_uses_extra_fields_formatter(self) -> None:
        """INFO threshold should use ExtraFieldsFormatter."""
        # Call setup_logging("INFO"), check handler's formatter type

    def test_debug_threshold_uses_extra_fields_formatter(self) -> None:
        """DEBUG threshold should use ExtraFieldsFormatter."""
        # Call setup_logging("DEBUG"), check handler's formatter type
```

## DATA

- `OUTPUT` constant: `int = 25`
- `CleanFormatter.format()` returns: `str`
- No new data structures

## HOW — Integration Points

- `CleanFormatter` is used only inside `setup_logging()` — no external import needed yet (Step 3 will import `OUTPUT` constant)
- `ExtraFieldsFormatter` remains unchanged and fully backward-compatible
- The `__init__.py` export rename is the only breaking change for external consumers importing `NOTICE`

## Commit Message
```
refactor(logging): rename NOTICE→OUTPUT, add CleanFormatter

- Rename NOTICE constant to OUTPUT (level 25, no alias)
- New CleanFormatter: bare messages at OUTPUT, prefixed at WARNING+
- setup_logging() selects formatter based on threshold
- Update tests for OUTPUT level and CleanFormatter
```
