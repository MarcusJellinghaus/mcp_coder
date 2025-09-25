"""Logging utilities for the MCP server."""

import json
import logging
import os
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, TypeVar, cast

import structlog
from pythonjsonlogger.json import JsonFormatter  # type: ignore[attr-defined]

# Type variable for function return types
T = TypeVar("T")

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
        console_formatter = logging.Formatter(
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

        stdlogger.info("Logging initialized: console=%s", log_level)


def log_function_call(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to log function calls with parameters, timing, and results."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        func_name = func.__name__
        module_name = func.__module__
        line_no = func.__code__.co_firstlineno

        # Prepare parameters for logging
        log_params = {}

        # Handle method calls (skip self/cls)
        if (
            args
            and hasattr(args[0], "__class__")
            and args[0].__class__.__module__ != "builtins"
        ):
            log_params.update(
                dict(zip(func.__code__.co_varnames[1 : len(args)], args[1:]))
            )
        else:
            log_params.update(dict(zip(func.__code__.co_varnames[: len(args)], args)))

        # Add keyword arguments
        log_params.update(kwargs)

        # Convert Path objects to strings and handle other non-serializable types
        serializable_params = {}
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
                parameters=serializable_params,
                module=module_name,
                lineno=line_no,
            )

        stdlogger.debug(
            "Calling %s with parameters: %s",
            func_name,
            json.dumps(serializable_params, default=str),
        )

        # Execute function and measure time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Prepare result for logging
            result_for_log: Any
            serializable_result: Any
            if isinstance(result, (list, dict)) and len(str(result)) > 1000:
                result_for_log = f"<Large result of type {type(result).__name__}, length: {len(str(result))}>"
                serializable_result = result_for_log
            else:
                result_for_log = result
                # Make result JSON serializable for structured logging
                try:
                    json.dumps(result)  # Test if result is JSON serializable
                    serializable_result = result
                except (TypeError, OverflowError):
                    serializable_result = str(result) if result is not None else None

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

            stdlogger.debug(
                "%s completed in %sms with result: %s",
                func_name,
                elapsed_ms,
                result_for_log,
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

            stdlogger.error(
                "%s failed after %sms with error: %s: %s",
                func_name,
                elapsed_ms,
                type(e).__name__,
                str(e),
                exc_info=True,
            )
            raise

    return cast(Callable[..., T], wrapper)
