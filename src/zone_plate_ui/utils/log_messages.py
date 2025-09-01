
import logging
from enum import Enum
from loguru import logger

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Log the message using Loguru
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


class log():
    CFG_LOG_CONFIG_SUCCESS = "CFG_LOG_CONFIG_SUCCESS"
    CFG_LOG_CONFIG_FAILURE = "CFG_LOG_CONFIG_FAILURE"
    CFG_APP_CONFIG_SUCCESS = "CFG_APP_CONFIG_SUCCESS"
    CFG_APP_CONFIG_FAILURE = "CFG_APP_CONFIG_FAILURE"

    # Message code and templates mapping
    DEFINED_MESSAGES = {
        # Configuration messages (1000-1999)
        "CFG_LOG_CONFIG_SUCCESS": {
            "CODE": 1000,
            "MESSAGE": "Log configuration successfully processed"
        },
        "CFG_LOG_CONFIG_FAILURE": {
            "CODE": 1001,
            "MESSAGE": "Failed to process log configuration: {error}"
        },
        "CFG_APP_CONFIG_SUCCESS": {
            "CODE": 1002,
            "MESSAGE": "App configuration successfully processed"
        },
        "CFG_APP_CONFIG_FAILURE": {
            "CODE": 1003,
            "MESSAGE": "Failed to process app configuration: {error}"
        }
    }

    DEFAULT_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<blue>{name}</blue>:<blue>{module}</blue>:<blue>{function}</blue>:<blue>{line}</blue> | "
        "<level>{message}</level> | "
        "\n{exception}"
    )

    EXTRA_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<blue>{name}</blue>:<blue>{module}</blue>:<blue>{function}</blue>:<blue>{line}</blue> | "
        "<level>{message}</level> | "
        "<light-blue>{extra}</light-blue>"
        "\n{exception}"
    )
    
    @staticmethod
    def log_format(record) -> str: 
        """
        Format log messages based on whether extra information is available.
        
        This function checks if the log record contains extra information.
        If it does, it returns a format string that includes the extra field.
        Otherwise, it returns the default format string.
        
        Args:
            record: The loguru record object containing log information
            
        Returns:
            str: The appropriate format string to use
        """
        # Check if the record has any extra data
        if record["extra"]:
            return log.EXTRA_FORMAT
        
        return log.DEFAULT_FORMAT
    
    @staticmethod
    def _get_message(message_key: str, **kwargs) -> str:
        """
        Get a message using a message key and format it with provided kwargs.

        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting

        Returns:
            Formatted message string
        """
        if message_key not in log.DEFINED_MESSAGES:
            return f"Unknown message key: {message_key}"

        message_template = log.DEFINED_MESSAGES[message_key]["MESSAGE"]

        # If there are kwargs, try to format the message with them
        if kwargs:
            try:
                return message_template.format(**kwargs)
            except KeyError as e:
                return f"{message_template} (Formatting error: missing {e})"

        return message_template
        
    @staticmethod
    def _add_message_code(message_key: str, extra_kwargs: dict) -> dict:
        """
        Add the message code to the extra context for structured logging.

        Args:
            message_key: A log class constant
            extra_kwargs: Dictionary of extra kwargs for the log

        Returns:
            Updated dictionary with message_code added if available
        """
        if message_key in log.DEFINED_MESSAGES:
            code = log.DEFINED_MESSAGES[message_key].get("CODE")
            if code:
                extra_kwargs['message_code'] = code

        return extra_kwargs
    
    @staticmethod
    def debug(message_key: str, **kwargs) -> None:
        """
        Log a debug level message using a log class constant.
        
        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).debug(message)
    
    @staticmethod
    def info(message_key: str, **kwargs) -> None:
        """
        Log an info level message using a log class constant.
        
        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).info(message)
    
    @staticmethod
    def warning(message_key: str, **kwargs) -> None:
        """
        Log a warning level message using a log class constant.
        
        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).warning(message)
    
    @staticmethod
    def error(message_key: str, **kwargs) -> None:
        """
        Log an error level message using a log class constant.
        
        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).error(message)
    
    @staticmethod
    def critical(message_key: str, **kwargs) -> None:
        """
        Log a critical level message using a log class constant.
        
        Args:
            message_key: A log class constant
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).critical(message)
    
    @staticmethod
    def exception(message_key: str, exc_info: bool = True, **kwargs) -> None:
        """
        Log an exception with traceback using a log class constant.
        
        Args:
            message_key: A log class constant
            exc_info: Whether to include exception info (default: True)
            **kwargs: Arguments for string formatting and extra context
                     that will be included in the structured log output
        """
        # Extract items to be used only for formatting, if any
        format_kwargs = kwargs.copy()
        extra_kwargs = {}
        
        # Check if 'extra' is explicitly provided
        if 'extra' in kwargs:
            extra_kwargs = kwargs.pop('extra')
        else:
            # Otherwise, use all kwargs as both formatting values and extra context
            extra_kwargs = kwargs.copy()
        
        # Get the message using the formatting kwargs
        message = log._get_message(message_key, **format_kwargs)
        
        # Add message code to the extra context
        extra_kwargs = log._add_message_code(message_key, extra_kwargs)
        
        # Pass the extra context to loguru
        logger.bind(**extra_kwargs).exception(message)
