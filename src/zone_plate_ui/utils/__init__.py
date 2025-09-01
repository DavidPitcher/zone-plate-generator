"""Utility functions and classes for the Zone Plate Generator application.

This package contains utility modules for handling various aspects of the application
such as logging, configuration management, and helper functions.

Modules:
    log_messages: Provides structured logging capabilities with message codes,
                 templates, and logging methods for different severity levels.
"""

from zone_plate_ui.utils.log_messages import (
    log,
    InterceptHandler,
)

__all__ = [
    'log',
    'InterceptHandler',
]

# Version information
__version__ = '0.1.0'
