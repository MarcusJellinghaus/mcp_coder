"""Logging utilities for the MCP server.

This module provides centralized logging configuration and utilities.
All other modules should use standard Python logging with the `extra`
parameter for structured data - only this module handles the underlying
logging infrastructure (including structlog for JSON file output).

Usage:
    >>> import logging
    >>> from mcp_coder.utils.log_utils import setup_logging
    >>>
    >>> # Initialize logging (call once at application startup)
    >>> setup_logging("INFO")  # Console output
    >>> setup_logging("DEBUG", log_file="app.log")  # JSON file output
    >>>
    >>> # In your modules, use standard logging with extra={} for structured data
    >>> logger = logging.getLogger(__name__)
    >>> logger.info("User logged in", extra={"user_id": "123", "ip": "192.168.1.1"})
    # Console: 2024-01-15 10:30:00 - mymodule - INFO - User logged in {"user_id": "123", "ip": "192.168.1.1"}
    # JSON file: {"asctime": "2024-01-15 10:30:00", "levelname": "INFO", ..., "user_id": "123", "ip": "192.168.1.1"}

Classes:
    ExtraFieldsFormatter: Formatter that appends extra fields to console log messages.

Functions:
    setup_logging: Configure logging with console or JSON file output.
    log_function_call: Decorator to log function calls with timing.
"""

import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast, overload

import structlog
from pythonjsonlogger.json import JsonFormatter

# Type variable for function return types
T = TypeVar("T")

# Type alias for dictionaries that can have string or tuple keys
# Used by _redact_for_logging to handle get_config_values() return format
RedactableDict = dict[str | tuple[str, ...], Any]

# Redaction placeholder for sensitive values
REDACTED_VALUE = "***"

# Standard LogRecord fields to exclude when extracting extra fields
# These are built-in attributes of logging.LogRecord that should not be treated as "extra" data
STANDARD_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "msg",
        "args",
        "asctime",  # Added by Formatter.format()
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "exc_info",
        "exc_text",
        "thread",
        "threadName",
        "taskName",
        "message",
    }
)


class ExtraFieldsFormatter(logging.Formatter):
    """Formatter that appends extra fields to log messages.

    This formatter extends the standard logging.Formatter to include any
    extra fields passed via the `extra` parameter in logging calls.
    Extra fields are appended to the log message as a JSON object.

    Example:
        >>> formatter = ExtraFieldsFormatter(
        ...     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ... )
        >>> handler.setFormatter(formatter)
        >>> logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
        # Output: 2024-01-15 10:30:00 - myapp - INFO - User logged in {"user_id": 123, "ip": "192.168.1.1"}
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record, appending any extra fields as JSON.

        Args:
            record: The log record to format.

        Returns:
            The formatted log message with extra fields appended as JSON.
        """
        # Get the base formatted message
        base_message = super().format(record)

        # Extract extra fields (attributes not in standard LogRecord fields)
        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_FIELDS
        }

        # If there are extra fields, append them as JSON
        if extra_fields:
            # Use default=str to handle non-serializable values
            suffix = json.dumps(extra_fields, default=str)
            return f"{base_message} {suffix}"

        return base_message


# Create standard logger
stdlogger = logging.getLogger(__name__)


def _is_testing_environment() -> bool:
    """Check if we're currently running in a testing environment (pytest)."""
    import sys

    # Check if pytest is running
    return (
        "pytest" in sys.modules
        or "_pytest" in sys.modules
        or hasattr(sys, "_called_from_test")
        or "PYTEST_CURRENT_TEST" in os.environ
    )


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Configure logging - if log_file specified, logs only to file; otherwise to console."""
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    # Don't clear handlers if we're in a testing environment (pytest)
    # This prevents conflicts with pytest's logging capture
    if not _is_testing_environment():
        # Clear existing handlers
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    else:
        root_logger = logging.getLogger()

    root_logger.setLevel(numeric_level)

    # Ensure all existing loggers also get the new level
    for name in logging.Logger.manager.loggerDict:
        logger = logging.getLogger(name)
        logger.setLevel(numeric_level)

    # Suppress verbose DEBUG logs from third-party libraries
    # These logs obscure meaningful debug output from project loggers
    logging.getLogger("urllib3.connectionpool").setLevel(logging.INFO)
    logging.getLogger("github.Requester").setLevel(logging.INFO)

    # Set up logging based on whether log_file is specified
    if log_file:
        # FILE LOGGING ONLY - no console output
        # Create directory if needed
        os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        # In testing environment, only add handler if it doesn't already exist
        if _is_testing_environment():
            # Check if file handler for this file already exists
            file_handler_exists = any(
                isinstance(h, logging.FileHandler)
                and h.baseFilename == os.path.abspath(log_file)
                for h in root_logger.handlers
            )
            if file_handler_exists:
                return  # Handler already exists, don't add another

        # Configure JSON file handler
        json_handler = logging.FileHandler(log_file)
        json_handler.setLevel(numeric_level)

        # This formatter ensures timestamp and level are included as separate fields in JSON
        json_formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d"
        )
        json_handler.setFormatter(json_formatter)
        root_logger.addHandler(json_handler)

        # Configure structlog processors for file logging
        # Only configure if not in testing environment to avoid conflicts
        if not _is_testing_environment():
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.processors.JSONRenderer(),
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        # Log initialization message to file only
        stdlogger.info("Logging initialized: file=%s, level=%s", log_file, log_level)
    else:
        # CONSOLE LOGGING ONLY (fallback when no file specified)
        # In testing environment, only add handler if no console handler exists
        if _is_testing_environment():
            console_handler_exists = any(
                isinstance(h, logging.StreamHandler)
                and not isinstance(h, logging.FileHandler)
                for h in root_logger.handlers
            )
            if console_handler_exists:
                return  # Console handler already exists, don't add another

        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_formatter = ExtraFieldsFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Configure structlog processors for console logging
        # Only configure if not in testing environment to avoid conflicts
        if not _is_testing_environment():
            structlog.configure(
                processors=[
                    structlog.stdlib.filter_by_level,  # This will respect the logging level
                    structlog.stdlib.add_logger_name,
                    structlog.stdlib.add_log_level,
                    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
                    structlog.processors.StackInfoRenderer(),
                    structlog.processors.format_exc_info,
                    structlog.processors.UnicodeDecoder(),
                    structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
                ],
                context_class=dict,
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )

        stdlogger.debug("Logging initialized: console=%s", log_level)

    stdlogger.debug(
        "Suppressing DEBUG logs from: urllib3.connectionpool, github.Requester"
    )


def _redact_for_logging(
    data: RedactableDict,
    sensitive_fields: set[str],
) -> RedactableDict:
    """Create a copy of data with sensitive fields redacted for logging.

    Args:
        data: Dictionary containing data to be logged.
        sensitive_fields: Set of field names whose values should be redacted.
            For tuple keys, the last element of the tuple is checked against
            sensitive_fields (e.g., ("github", "token") matches "token").

    Returns:
        A shallow copy of data with sensitive field values replaced by "***".
        Nested dictionaries are processed recursively.
    """
    result = data.copy()
    for key in result:
        # Check if key matches sensitive fields
        # For tuple keys, check the last element
        key_to_check: str | None = None
        if isinstance(key, str):
            key_to_check = key
        elif isinstance(key, tuple) and len(key) > 0:
            last_element = key[-1]
            if isinstance(last_element, str):
                key_to_check = last_element

        if key_to_check is not None and key_to_check in sensitive_fields:
            result[key] = REDACTED_VALUE
        elif isinstance(result[key], dict):
            result[key] = _redact_for_logging(result[key], sensitive_fields)
    return result


# Overload signatures for proper typing
@overload
def log_function_call(func: Callable[..., T]) -> Callable[..., T]: ...


@overload
def log_function_call(
    func: None = None,
    *,
    sensitive_fields: list[str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def log_function_call(
    func: Callable[..., T] | None = None,
    *,
    sensitive_fields: list[str] | None = None,
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log function calls with parameters, timing, and results.

    Can be used as @log_function_call or @log_function_call(sensitive_fields=[...]).

    Args:
        func: The function to decorate (when used without parentheses).
        sensitive_fields: Optional list of field names whose values should be
            redacted in logs. Applies to both parameters and return values.

    Returns:
        Decorated function or decorator depending on usage.
    """
    sensitive_set = set(sensitive_fields) if sensitive_fields else set()

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            func_name = fn.__name__
            module_name = fn.__module__
            line_no = fn.__code__.co_firstlineno

            # Get logger for the decorated function's module (not log_utils)
            func_logger = logging.getLogger(module_name)

            # Prepare parameters for logging
            log_params: dict[str, Any] = {}

            # Handle method calls (skip self/cls)
            if (
                args
                and hasattr(args[0], "__class__")
                and args[0].__class__.__module__ != "builtins"
            ):
                log_params.update(
                    dict(zip(fn.__code__.co_varnames[1 : len(args)], args[1:]))
                )
            else:
                log_params.update(dict(zip(fn.__code__.co_varnames[: len(args)], args)))

            # Add keyword arguments
            log_params.update(kwargs)

            # Convert Path objects to strings and handle other non-serializable types
            serializable_params: dict[str, Any] = {}
            for k, v in log_params.items():
                if isinstance(v, Path):
                    serializable_params[k] = str(v)
                else:
                    try:
                        # Test if it's JSON serializable
                        json.dumps(v)
                        serializable_params[k] = v
                    except (TypeError, OverflowError):
                        # If not serializable, convert to string
                        serializable_params[k] = str(v)

            # Apply redaction for sensitive fields
            # Cast needed because serializable_params is dict[str, Any] but
            # _redact_for_logging accepts RedactableDict
            params_for_log = (
                _redact_for_logging(
                    cast(RedactableDict, serializable_params),
                    sensitive_set,
                )
                if sensitive_set
                else serializable_params
            )

            # Check if structured logging is enabled
            has_structured = any(
                isinstance(h, logging.FileHandler) for h in logging.getLogger().handlers
            )

            # Log function call
            if has_structured:
                structlogger = structlog.get_logger(module_name)
                structlogger.debug(
                    "Calling function",
                    function=func_name,
                    parameters=params_for_log,
                    module=module_name,
                    lineno=line_no,
                )

            func_logger.debug(
                "%s(%s)", func_name, json.dumps(params_for_log, default=str)
            )

            # Execute function and measure time
            start_time = time.time()
            try:
                result = fn(*args, **kwargs)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                # Prepare result for logging
                result_for_log: Any
                serializable_result: Any
                if isinstance(result, (list, dict)) and len(str(result)) > 1000:
                    result_for_log = (
                        f"<Large result of type {type(result).__name__}, "
                        f"length: {len(str(result))}>"
                    )
                    serializable_result = result_for_log
                else:
                    result_for_log = result
                    # Make result JSON serializable for structured logging
                    try:
                        json.dumps(result)  # Test if result is JSON serializable
                        serializable_result = result
                    except (TypeError, OverflowError):
                        serializable_result = (
                            str(result) if result is not None else None
                        )

                # Apply redaction to result if it's a dict
                if sensitive_set and isinstance(serializable_result, dict):
                    serializable_result = _redact_for_logging(
                        serializable_result, sensitive_set
                    )
                if sensitive_set and isinstance(result_for_log, dict):
                    result_for_log = _redact_for_logging(result_for_log, sensitive_set)

                # Log completion
                if has_structured:
                    structlogger.debug(
                        "Function completed",
                        function=func_name,
                        execution_time_ms=elapsed_ms,
                        status="success",
                        result=serializable_result,
                        module=module_name,
                        lineno=line_no,
                    )

                func_logger.debug(
                    "%s -> %s (%sms)", func_name, result_for_log, elapsed_ms
                )
                return result

            except Exception as e:
                # Log exceptions
                elapsed_ms = round((time.time() - start_time) * 1000, 2)

                if has_structured:
                    structlogger.error(
                        "Function failed",
                        function=func_name,
                        execution_time_ms=elapsed_ms,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        module=module_name,
                        lineno=line_no,
                        exc_info=True,
                    )

                func_logger.error(
                    "%s FAILED: %s: %s (%sms)",
                    func_name,
                    type(e).__name__,
                    str(e),
                    elapsed_ms,
                    exc_info=True,
                )
                raise

        return cast(Callable[..., T], wrapper)

    # Handle both @log_function_call and @log_function_call(sensitive_fields=[...])
    if func is not None:
        # Called without parentheses: @log_function_call
        return decorator(func)
    # Called with parentheses: @log_function_call(sensitive_fields=[...])
    return decorator
