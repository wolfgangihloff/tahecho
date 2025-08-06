import functools
import logging
import traceback
from typing import Any, Callable

logger = logging.getLogger(__name__)


def handle_engineio_errors(func: Callable) -> Callable:
    """
    Decorator to handle EngineIO errors gracefully.
    These errors are often transient and don't affect core functionality.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)

            # Handle EngineIO specific errors
            if "Too many packets in payload" in error_msg:
                logger.warning("EngineIO payload error (transient): %s", error_msg)
                # Return a graceful error response
                return {"error": "Connection issue detected, please try again"}

            elif "engineio" in error_msg.lower() or "socketio" in error_msg.lower():
                logger.warning("EngineIO/SocketIO error (transient): %s", error_msg)
                return {"error": "Connection issue detected, please try again"}

            # Re-raise other errors
            logger.error("Unexpected error in %s: %s", func.__name__, error_msg)
            logger.error("Traceback: %s", traceback.format_exc())
            raise

    return wrapper


def setup_error_handling():
    """
    Set up error handling for the application.
    """
    # Suppress noisy EngineIO/SocketIO logs
    logging.getLogger("engineio").setLevel(logging.WARNING)
    logging.getLogger("socketio").setLevel(logging.WARNING)
    logging.getLogger("engineio.async_server").setLevel(logging.WARNING)
    logging.getLogger("engineio.async_socket").setLevel(logging.WARNING)

    # Set up custom error handler for unhandled exceptions
    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow keyboard interrupts to pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log unhandled exceptions
        logger.error(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    import sys

    sys.excepthook = handle_unhandled_exception
