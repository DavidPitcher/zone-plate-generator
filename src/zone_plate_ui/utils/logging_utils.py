"""Logging utilities for the Zone Plate Generator application."""

import logging
import os
import sys
import functools
from enum import Enum
from typing import Dict, Optional, Any, Callable
from pathlib import Path

# Define module component prefixes
class Component(Enum):
    """Component identifiers for the Zone Plate Generator application."""
    CONFIG = "CFG"
    CONTROLLER = "CTRL"
    MODEL = "MOD"
    VIEW = "VIEW"
    UTIL = "UTIL"
    SYSTEM = "SYS"

# Define error code ranges for each component
# CFG: 1000-1999
# CTRL: 2000-2999
# MOD: 3000-3999
# VIEW: 4000-4999
# UTIL: 5000-5999
# SYS: 9000-9999

# Message code and templates mapping
MESSAGE_CODES = {
    # Configuration messages (1000-1999)
    "CFG_ENV_NOT_FOUND": 1001,
    "CFG_INVALID_CONFIG": 1002,
    "CFG_DIR_CREATE_FAILED": 1003,
    "CFG_INIT_OUTPUT_DIR_SUCCESS": 1004,
    "CFG_FILE_NOT_FOUND": 1005,
    "CFG_INIT_SUCCESS": 1006,
    "CFG_INIT_FAILED": 1007,
    
    # Controller messages (2000-2999)
    "CTRL_VALIDATION_FAILED": 2001,
    "CTRL_GENERATION_FAILED": 2002,
    "CTRL_INVALID_TOKEN": 2003,
    "CTRL_TOKEN_EXPIRED": 2004,
    "CTRL_FILE_NOT_FOUND": 2005,
    "CTRL_ACCESS_DENIED": 2006,
    "CTRL_UNHANDLED_ERROR": 2007,
    "CTRL_BAD_REQUEST": 2008,
    "CTRL_METHOD_NOT_ALLOWED": 2009,
    "CTRL_REQUEST_SUCCESS": 2100,  # Informational code for successful requests
    "CTRL_DOWNLOAD_SUCCESS": 2101,  # Informational code for successful downloads
    
    # Model messages (3000-3999)
    "MOD_VALIDATION_FAILED": 3001,
    "MOD_FILE_CREATION_FAILED": 3002,
    "MOD_SUBPROCESS_FAILED": 3003,
    "MOD_OUTPUT_MISSING": 3004,
    "MOD_FILE_EMPTY": 3005,
    "MOD_CLEANUP_FAILED": 3006,
    "MOD_FILE_DELETE_FAILED": 3007,
    "MOD_GHOSTSCRIPT_MISSING": 3008,
    "MOD_GENERATION_SUCCESS": 3100,  # Informational code for successful generation
    "MOD_CLEANUP_SUCCESS": 3101,  # Informational code for successful cleanup
    
    # System messages (9000-9999)
    "SYS_STARTUP_FAILED": 9001,
    "SYS_SHUTDOWN_ERROR": 9002,
    "SYS_RESOURCE_UNAVAILABLE": 9003,
    "SYS_APP_SERVER_STARTUP": 9100,  
    "SYS_APP_ENVIRONMENT": 9101,
    "SYS_APP_SHUTDOWN": 9102
}

# Message templates
MESSAGE_TEMPLATES = {
    # Configuration messages
    "CFG_ENV_NOT_FOUND": "Environment variable '{var_name}' not found, using default: {default}",
    "CFG_INVALID_CONFIG": "Invalid configuration value for '{config_key}'",
    "CFG_INIT_OUTPUT_DIR_FAILED": "Failed to create directory: {dir_path}",
    "CFG_INIT_OUTPUT_DIR_SUCCESS": "Output directory created and initialized successfully: {output_dir}",
    "CFG_FILE_NOT_FOUND": "Required configuration file not found: {file_path}",
    "CFG_INIT_SUCCESS": "Configuration initialized successfully: {config_class}",
    "CFG_INIT_FAILED": "Configuration initialization failed: {reason}",
    
    
    # Controller messages
    "CTRL_VALIDATION_FAILED": "Validation failed: {error_details}",
    "CTRL_GENERATION_FAILED": "Zone plate generation failed: {reason}",
    "CTRL_INVALID_TOKEN": "Invalid download token: {token}",
    "CTRL_TOKEN_EXPIRED": "Download token expired: {token}",
    "CTRL_FILE_NOT_FOUND": "File not found for download: {filename}",
    "CTRL_ACCESS_DENIED": "Access denied: {reason}",
    "CTRL_UNHANDLED_ERROR": "Unhandled exception in controller: {error}",
    "CTRL_BAD_REQUEST": "Bad request received: {details}",
    "CTRL_METHOD_NOT_ALLOWED": "Method not allowed: {method} {path}",
    "CTRL_REQUEST_SUCCESS": "Request processed successfully: {path}",
    "CTRL_DOWNLOAD_SUCCESS": "Download completed successfully: {filename}",
    
    # Model messages
    "MOD_VALIDATION_FAILED": "Parameter validation failed: {errors}",
    "MOD_FILE_CREATION_FAILED": "Failed to create temporary file: {reason}",
    "MOD_SUBPROCESS_FAILED": "Ghostscript process failed (exit code {exit_code}): {error}",
    "MOD_OUTPUT_MISSING": "Output file was not created: {file_path}",
    "MOD_FILE_EMPTY": "Output file is empty: {file_path}",
    "MOD_CLEANUP_FAILED": "Failed to clean up temporary resources: {error}",
    "MOD_FILE_DELETE_FAILED": "Failed to delete file: {file_path} - {error}",
    "MOD_GHOSTSCRIPT_MISSING": "Ghostscript executable not found in PATH",
    "MOD_GENERATION_SUCCESS": "Successfully generated zone plate: {file_path}",
    "MOD_CLEANUP_SUCCESS": "Successfully cleaned up temporary resources: {resource_type}",
    
    # System messages
    "SYS_STARTUP_FAILED": "Application startup failed: {reason}",
    "SYS_SHUTDOWN_ERROR": "Error during application shutdown: {error}",
    "SYS_RESOURCE_UNAVAILABLE": "System resource unavailable: {resource} - {reason}",
    "SYS_APP_SERVER_STARTUP": "Application starting on port {port}",
    "SYS_APP_ENVIRONMENT": (
        "Application environment details:\n"
        "Working Directory: {cwd}\n"
        "Module Path: {module_path}\n"
        "Script Directory: {script_dir}\n"
    ),
    "SYS_APP_SHUTDOWN": "Application shutting down gracefully",
}

class ZonePlateFormatter(logging.Formatter):
    """Custom formatter for Zone Plate Generator logs with color support."""

    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[41m\033[37m",  # Red background, white text
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record):
        """Format the log record with message code, component, and color by level."""
        # Get color for this log level
        color = self.COLORS.get(record.levelno, self.RESET)
        
        # Add message code to the log record if available
        if hasattr(record, 'message_code'):
            record.msg = f"[{record.message_code:04d}] {record.msg}"
        # Legacy support for error_code
        elif hasattr(record, 'error_code'):
            record.msg = f"[{record.error_code:04d}] {record.msg}"
        
        # Add component prefix if available
        if hasattr(record, 'component'):
            record.msg = f"[{record.component}] {record.msg}"
            
        # Store original levelname
        original_levelname = record.levelname
        
        # Color-code the levelname and make it bold
        record.levelname = f"{self.BOLD}{color}{original_levelname}{self.RESET}"
        
        # Call the original format method to get the formatted message
        formatted_msg = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        # Find where the message part begins (after the levelname)
        message_start = formatted_msg.find(" - ") + 3
        if message_start > 3:  # Found the separator
            # Color only the message part, not the metadata
            formatted_msg = (
                formatted_msg[:message_start] + 
                color + 
                formatted_msg[message_start:] + 
                self.RESET
            )
        
        return formatted_msg

def configure_logging(app_name: str = "zone_plate_ui", level: int = None) -> None:
    """Configure global logging settings.
    
    Args:
        app_name: Application name to include in log records
        level: Logging level to use (if None, uses DEBUG for local/dev and INFO for prod)
    """
    
    if level is None:
        env = os.environ.get("FLASK_ENV", "local")
        level = logging.DEBUG if env in ("local", "development") else logging.INFO
    
    root_logger = logging.getLogger()
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set up console handler with color support
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = ZonePlateFormatter(
        '%(asctime)s:%(name)s:%(module)s:%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)

    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    app_logger = logging.getLogger(app_name)
    app_logger.setLevel(level)
    #app_logger.propagate = False
    app_logger.info(f"Logging configured for {app_name} at level {logging.getLevelName(level)}")

    return


def get_logger(module_name: str, component: Component = Component.SYSTEM) -> logging.Logger:
    """Get a configured logger for a module.
    
    Args:
        module_name: The name of the module requesting the logger
        component: The component type (CONFIG, CONTROLLER, MODEL, etc.)
        
    Returns:
        logging.Logger: A configured logger instance with enhanced logging methods
        
    The returned logger has the following enhanced methods:
        - debug_with_code(message_code, **kwargs)
        - info_with_code(message_code, **kwargs)
        - warning_with_code(message_code, **kwargs)
        - error_with_code(message_code, **kwargs)
        - critical_with_code(message_code, **kwargs)
        
    The message_code parameter is required and must refer to a code defined in the 
    MESSAGE_CODES dictionary. The code can be provided with or without the component prefix. 
    For example, both "APP_STARTUP" and "SYS_APP_STARTUP" are valid when using a 
    SYSTEM component logger.
    
    The logger will use the message template associated with the message code. Any variables
    required by the template should be provided in the kwargs or the extra dictionary.
    """
    logger = logging.getLogger(module_name)
    
    # Create log method decorators that attach message codes and component info
    def create_log_method(original_method, code_prefix):
        @functools.wraps(original_method)
        def wrapped(message_code, **kwargs):
            # Add component to record attributes
            kwargs['extra'] = kwargs.get('extra', {})
            kwargs['extra']['component'] = component.value
            
            # Try with the component prefix first (e.g., "SYS_APP_STARTUP")
            code_key = f"{code_prefix}_{message_code}"
            
            # If not found, try with the raw code
            if code_key not in MESSAGE_CODES and message_code in MESSAGE_CODES:
                code_key = message_code
            
            if code_key not in MESSAGE_CODES:
                print(f"Warning: Unknown message code: {code_key}")
                msg = f"Log message for unknown code {message_code}"
                return original_method(msg, **kwargs)
                
            # Add message code to extra
            kwargs['extra']['message_code'] = MESSAGE_CODES[code_key]
            
            # Use message template if available
            if code_key not in MESSAGE_TEMPLATES:
                print(f"Warning: No template found for message code: {code_key}")
                msg = f"Log message for code {code_key} (no template)"
                return original_method(msg, **kwargs)
                
            template = MESSAGE_TEMPLATES[code_key]
            try:
                # Create a dict for template formatting
                format_dict = {}
                
                # Add non-extra kwargs to format_dict
                for k, v in kwargs.items():
                    if k != 'extra':
                        format_dict[k] = v
                        
                # Add extra dict items to format_dict if present
                if 'extra' in kwargs and isinstance(kwargs['extra'], dict):
                    for k, v in kwargs['extra'].items():
                        format_dict[k] = v
                        
                # Try to format the message template
                msg = template.format(**format_dict)
            except KeyError as e:
                # Log a warning about missing template variables
                print(f"Warning: Template variable missing for {code_key}: {str(e)}")
                msg = f"Log message for code {code_key} (template formatting failed)"
            
            return original_method(msg, **kwargs)
        return wrapped
    
    # Create enhanced logging methods with error code handling
    logger.debug_with_code = create_log_method(logger.debug, component.value)
    logger.info_with_code = create_log_method(logger.info, component.value)
    logger.warning_with_code = create_log_method(logger.warning, component.value)
    logger.error_with_code = create_log_method(logger.error, component.value)
    logger.critical_with_code = create_log_method(logger.critical, component.value)
    
    return logger


def log_exception(logger, message_code: str, **context):
    """Log an exception with traceback and context information.
    
    Args:
        logger: Logger instance to use
        message_code: Message code identifier (e.g., "CTRL_UNHANDLED_ERROR")
        **context: Additional context variables to include in the log
    """
    exc_info = sys.exc_info()
    
    # Extract error details
    if exc_info and exc_info[0]:
        exception_type = exc_info[0].__name__
        exception_msg = str(exc_info[1]) if exc_info[1] else ""
        
        # Add exception info to context
        context['error'] = f"{exception_type}: {exception_msg}"
        
        # Log with the provided message code and exception info
        logger.error_with_code(
            message_code,
            exc_info=True,
            **context
        )
    else:
        # No exception context available
        logger.error_with_code(
            message_code,
            exc_info=True,
            **context
        )
