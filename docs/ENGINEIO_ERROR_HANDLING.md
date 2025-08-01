# EngineIO Error Handling

## Overview

This document describes the EngineIO error handling that was implemented to address the "Too many packets in payload" errors that can occur in the Chainlit application.

## Problem

The application was experiencing EngineIO/Socket.IO errors in the console logs:
```
ValueError: Too many packets in payload
```

These errors are typically transient and occur due to:
- Network connection issues
- Client-side packet fragmentation
- Socket.IO protocol version mismatches
- Browser connection problems

## Solution

### 1. Error Handling Utility

Created `utils/error_handling.py` with:
- **Graceful error handling**: Catches EngineIO errors and returns user-friendly messages
- **Logging suppression**: Reduces noise from non-critical EngineIO logs
- **Decorator pattern**: Easy to apply to async functions

### 2. Chainlit Configuration

Updated `.chainlit/config.toml` with Socket.IO settings:
```toml
[socketio]
# Maximum number of packets in a single payload
max_payload_size = 1000000
# Enable compression
compression = true
# Enable binary messages
binary = false
# Enable polling fallback
allow_upgrades = true
```

### 3. Application Integration

Updated `app.py` to:
- Import and initialize error handling
- Suppress noisy EngineIO logs
- Handle unhandled exceptions gracefully

## Implementation Details

### Error Handling Decorator

```python
@handle_engineio_errors
async def your_function():
    # Your code here
    pass
```

The decorator:
- Catches EngineIO-specific errors
- Returns graceful error responses
- Logs warnings instead of errors
- Re-raises non-EngineIO errors

### Logging Configuration

Automatically suppresses noisy logs from:
- `engineio`
- `socketio`
- `engineio.async_server`
- `engineio.async_socket`

## Testing

Added comprehensive tests in `tests/unit/test_error_handling.py`:
- EngineIO error handling
- SocketIO error handling
- Normal function execution
- Error handling setup
- Non-EngineIO error propagation

## Benefits

1. **Reduced Log Noise**: EngineIO errors are logged as warnings instead of errors
2. **Better User Experience**: Users get friendly error messages instead of crashes
3. **Improved Stability**: Transient connection issues don't break the application
4. **Maintainability**: Centralized error handling logic

## Usage

The error handling is automatically applied when the application starts. No additional configuration is needed.

### Manual Application

To apply error handling to specific functions:

```python
from utils.error_handling import handle_engineio_errors

@handle_engineio_errors
async def your_async_function():
    # Your code here
    pass
```

## Monitoring

Monitor the application logs for:
- `WARNING` level messages from EngineIO errors (expected)
- `ERROR` level messages from other issues (investigate)

## Troubleshooting

If you still see EngineIO errors:

1. **Check network connectivity**: Ensure stable internet connection
2. **Browser compatibility**: Try different browsers
3. **Clear browser cache**: Clear cookies and cache
4. **Check Chainlit version**: Ensure you're using a compatible version

## Related Files

- `utils/error_handling.py` - Error handling implementation
- `.chainlit/config.toml` - Socket.IO configuration
- `app.py` - Application integration
- `tests/unit/test_error_handling.py` - Test suite 