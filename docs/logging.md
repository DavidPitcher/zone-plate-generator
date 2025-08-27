# Logging System

## Overview

This document describes the standardized logging system implemented in the Zone Plate Generator application. The logging system provides consistent error handling, standardized message formats, and module-specific logging capabilities.

## Components

The logging system consists of the following components:

1. **Centralized Logger Configuration**: A shared logging configuration is maintained in `utils/logging_utils.py`.
2. **Message Codes**: Each module has a specific range of message codes that can be used for identification and troubleshooting.
3. **Message Templates**: Standardized message templates ensure consistency across the application.
4. **Component Identification**: Each log message includes the component identifier (CONFIG, CONTROLLER, MODEL, etc.).

## Message Code Ranges

Message codes are organized by component and type:

- CONFIG: 1000-1999
  - Errors: 1001-1099
  - Information: 1100-1199
- CONTROLLER: 2000-2999
  - Errors: 2001-2099
  - Information: 2100-2199
- MODEL: 3000-3999
  - Errors: 3001-3099
  - Information: 3100-3199
- VIEW: 4000-4999
  - Errors: 4001-4099
  - Information: 4100-4199
- UTIL: 5000-5999
  - Errors: 5001-5099
  - Information: 5100-5199
- SYSTEM: 9000-9999
  - Errors: 9001-9099
  - Information: 9100-9199

## Usage

### Getting a Logger

To get a module-specific logger:

```python
from zone_plate_ui.utils.logging_utils import get_logger, Component

# Create a logger for a module
logger = get_logger(__name__, Component.MODEL)
```

### Logging with Message Codes

To log a message with a message code:

```python
# Informational message with message code
logger.info_with_code(
    "Application starting", 
    message_code="APP_STARTUP",
    config_class="ProdConfig"
)

# Debug level with error code
logger.debug_with_code(
    "Validating parameters", 
    message_code="VALIDATION_FAILED",
    param_name="focal_length"
)

# Info level with extra context but no code
logger.info_with_code(
    "Operation succeeded", 
    extra={'operation': 'generate', 'filename': 'output.png'}
)

# Warning with error code
logger.warning_with_code(
    "Resource unavailable", 
    message_code="RESOURCE_UNAVAILABLE",
    resource="database"
)

# Error with error code
logger.error_with_code(
    "File not found", 
    message_code="FILE_NOT_FOUND",
    filename="zone_plate.png"
)
```

Note that the `message_code` parameter can accept:
1. The full message code with component prefix (e.g., "SYS_APP_STARTUP")
2. The short message code without component prefix (e.g., "APP_STARTUP")

The component prefix is automatically determined from the logger's component type.

### Logging Exceptions

To log an exception with full traceback:

```python
from zone_plate_ui.utils.logging_utils import log_exception

try:
    # Code that might raise an exception
    do_something()
except Exception as e:
    log_exception(
        logger, 
        message_code="CTRL_UNHANDLED_ERROR",
        context="generate_route"
    )
```

## Log Format

Logs include:
- Timestamp
- Module name
- Log level
- Component identifier
- Message code (if applicable)
- Message
- Additional context data

Example:
```
2025-08-25 12:34:56 - zone_plate_ui.controllers.main - ERROR - [CTRL][2002] Zone plate generation failed: Invalid parameters
```

## Adding New Message Codes

To add new message codes:

1. Update the `MESSAGE_CODES` dictionary in `logging_utils.py`
   - Use the range 1-99 for error codes (e.g., `SYS_STARTUP_FAILED`: 9001)
   - Use the range 100-199 for informational codes (e.g., `SYS_APP_STARTUP`: 9100)
2. Add corresponding message template to `MESSAGE_TEMPLATES`
3. Use the new message code in your module

## Message Templates

Message templates provide standardized messages with placeholders for dynamic content. For example:

```python
"CTRL_VALIDATION_FAILED": "Validation failed: {error_details}"
"SYS_APP_STARTUP": "Application starting with configuration: {config_class}"
```

The placeholders are automatically filled with values from the `extra` dictionary or any additional keyword arguments passed to the logging method.
