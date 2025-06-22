import sys
import logging
import inspect
from typing import Dict, Any, Callable
from loguru import logger
from pathlib import Path

# Create logs directory if it doesn't exist
# LOGS_DIR = Path("logs")
# LOGS_DIR.mkdir(exist_ok=True)


def configure_logger(console_level: str = "INFO", log_format: str = None) -> None:
    """Configure loguru logger with console and file outputs

    Args:
        console_level: Minimum level for console logs
        file_level: Minimum level for file logs
        rotation: When to rotate log files (size or time)
        retention: How long to keep log files
        log_format: Optional custom format string
    """
    # Remove default configuration
    logger.remove()

    # Use default format if none provided
    if log_format is None:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    # Add console handler
    logger.add(
        sys.stderr,
        format=log_format,
        level=console_level,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # # Add file handler
    # logger.add(
    #     LOGS_DIR / "app.log",
    #     format=log_format,
    #     level=console_level,
    # )


# Intercept standard library logging to loguru
class InterceptHandler(logging.Handler):
    """Intercepts standard library logging and redirects to loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = inspect.currentframe(), 0
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def patch_std_logging():
    """Patch all standard library loggers to use loguru"""
    # Replace all existing handlers with the InterceptHandler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Update all existing loggers
    for name in logging.root.manager.loggerDict.keys():
        logging_logger = logging.getLogger(name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Update specific common libraries
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]


def setup_logging(console_level: str = "INFO", intercept_stdlib: bool = True) -> None:
    """Setup logging for the entire application

    Args:
        console_level: Minimum level for console output
        file_level: Minimum level for file output
        intercept_stdlib: Whether to patch standard library logging
    """
    # Configure loguru
    configure_logger(console_level=console_level)

    # Optionally patch standard library logging
    if intercept_stdlib:
        patch_std_logging()

    # Add extra context to logger
    logger.configure(extra={"app_name": "decipher-research-agent"})

    logger.info("Logging configured successfully")


def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    """Hook function that wraps the tool execution"""
    logger.info(f"About to call {function_name} with arguments: {arguments}")
    result = function_call(**arguments)
    logger.info(f"Function call completed with result: {result}")
    return result
