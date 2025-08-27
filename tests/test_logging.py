"""Unit tests for the logging system."""

import unittest
import logging
from io import StringIO

from src.zone_plate_ui.utils.logging_utils import (
    configure_logging, 
    get_logger, 
    Component,
    log_exception,
    MESSAGE_CODES,
    MESSAGE_TEMPLATES
)

class TestLogging(unittest.TestCase):
    """Test cases for the logging utilities."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure a test logger that writes to a StringIO buffer
        self.log_output = StringIO()
        self.handler = logging.StreamHandler(self.log_output)
        self.handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers and add test handler
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        root_logger.addHandler(self.handler)
        
        # Get a test logger
        self.logger = get_logger("test_logger", Component.MODEL)
    
    def test_component_in_log_message(self):
        """Test that component identifier is included in log messages."""
        self.logger.info("Test message")
        self.assertIn("MOD", self.log_output.getvalue())
        
    def test_message_code_in_log_message(self):
        """Test that message code is included in log messages."""
        self.logger.error_with_code(
            "Test error", 
            message_code="VALIDATION_FAILED"
        )
        self.assertIn("[3001]", self.log_output.getvalue())
        
    def test_message_template(self):
        """Test that message templates are correctly formatted."""
        self.logger.error_with_code(
            "Validation failed", 
            message_code="VALIDATION_FAILED",
            errors={"focal_length": "must be positive"}
        )
        self.assertIn("Parameter validation failed", self.log_output.getvalue())
        
    def test_log_exception(self):
        """Test logging exceptions."""
        try:
            raise ValueError("Test exception")
        except Exception:
            log_exception(
                self.logger, 
                message_code="MOD_VALIDATION_FAILED"
            )
        
        log_content = self.log_output.getvalue()
        self.assertIn("Exception ValueError", log_content)
        self.assertIn("[3001]", log_content)
        
    def test_message_codes_match_templates(self):
        """Test that all message codes have corresponding message templates."""
        for code_key in MESSAGE_CODES.keys():
            self.assertIn(code_key, MESSAGE_TEMPLATES, 
                          f"Message code {code_key} has no message template")


if __name__ == "__main__":
    unittest.main()
