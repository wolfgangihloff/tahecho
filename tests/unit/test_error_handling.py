import asyncio
import logging
from unittest.mock import MagicMock, patch

import pytest

from tahecho.utils.error_handling import handle_engineio_errors, setup_error_handling


class TestErrorHandling:
    """Test error handling functionality."""

    @pytest.mark.asyncio
    async def test_engineio_error_handling(self):
        """Test that EngineIO errors are handled gracefully."""

        @handle_engineio_errors
        async def test_function():
            raise ValueError("Too many packets in payload")

        # Test the error handling
        with patch("tahecho.utils.error_handling.logger") as mock_logger:
            result = await test_function()

            # Should return error response instead of raising
            assert result == {"error": "Connection issue detected, please try again"}
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_other_errors_still_raised(self):
        """Test that non-EngineIO errors are still raised."""

        @handle_engineio_errors
        async def test_function():
            raise ValueError("Some other error")

        # Test that other errors are still raised
        with pytest.raises(ValueError, match="Some other error"):
            await test_function()

    def test_setup_error_handling(self):
        """Test that error handling setup works correctly."""
        with patch("tahecho.utils.error_handling.logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            setup_error_handling()

            # Verify that logging levels were set
            mock_get_logger.assert_called()

    @pytest.mark.asyncio
    async def test_engineio_socketio_error_handling(self):
        """Test that SocketIO errors are also handled."""

        @handle_engineio_errors
        async def test_function():
            raise RuntimeError("socketio connection failed")

        with patch("tahecho.utils.error_handling.logger") as mock_logger:
            result = await test_function()

            assert result == {"error": "Connection issue detected, please try again"}
            mock_logger.warning.assert_called()

    @pytest.mark.asyncio
    async def test_normal_function_execution(self):
        """Test that normal functions work without errors."""

        @handle_engineio_errors
        async def test_function():
            return "success"

        result = await test_function()
        assert result == "success"
