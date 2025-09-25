"""Error handlers for the zone plate generator application."""

from flask import Flask, render_template, request
from werkzeug.exceptions import HTTPException
from typing import Optional, Dict, Any, Tuple, Type
from http import HTTPStatus


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, errors: Optional[Dict[str, str]] = None):
        self.message = message
        self.errors = errors or {}
        self.status_code = HTTPStatus.BAD_REQUEST
        super().__init__(self.message)


class GenerationError(Exception):
    """Custom exception for zone plate generation errors."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        self.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        super().__init__(self.message)


class FileNotFoundError(Exception):
    """Custom exception for file not found errors."""
    
    def __init__(self, message: str, filename: Optional[str] = None):
        self.message = message
        self.filename = filename
        self.status_code = HTTPStatus.NOT_FOUND
        super().__init__(self.message)


class AccessDeniedError(Exception):
    """Custom exception for access denied errors."""

    def __init__(self, message: str, reason: Optional[str] = None):
        self.message = message
        self.reason = reason
        self.status_code = HTTPStatus.FORBIDDEN
        super().__init__(self.message)


class HttpErrorManager:
    """Class-based manager for HTTP error handlers in Flask applications."""
    
    def __init__(self, app: Flask):
        """Initialize the HTTP error manager.
        
        Args:
            app: Optional Flask application to register handlers with
        """
        # Initialize app attribute to avoid linting issues
        self.app = app
        self._register_handlers()
    
    def _get_theme_config(self) -> Dict[str, Any]:
        """Get theme configuration for error pages."""   
        theme = request.cookies.get('theme', 'light')
        return {
            'current_theme': theme,
            'theme_config': self.app.config['THEMES'][theme],
            'themes': self.app.config['THEMES']
        }
    
    def _render_error_template(
            self, 
            error_code: int,
            error_message: str,
            error_details: Optional[Any] = None
        ) -> Tuple[str, int]:
        """Render error template with consistent formatting.
        
        Args:
            error_code: HTTP error code
            error_message: Main error message
            error_details: Optional error details
            
        Returns:
            Tuple of (rendered template, HTTP status code)
        """
        theme_config = self._get_theme_config()
        template_args = {
            'error_code': error_code,
            'error_message': error_message,
            **theme_config
        }
        
        if error_details is not None:
            template_args['error_details'] = error_details
            
        return render_template('error.html', **template_args), error_code
    
    def _register_handlers(self) -> None:
        """Register all error handlers with the Flask application."""

        # Custom exception handlers
        self.app.register_error_handler(ValidationError, self.handle_validation_error)
        self.app.register_error_handler(GenerationError, self.handle_generation_error)
        self.app.register_error_handler(FileNotFoundError, self.handle_file_not_found_error)
        self.app.register_error_handler(AccessDeniedError, self.handle_access_denied_error)
        
        # Standard HTTP error handlers
        self.app.register_error_handler(HTTPStatus.BAD_REQUEST.value, self.handle_bad_request)
        self.app.register_error_handler(HTTPStatus.FORBIDDEN.value, self.handle_forbidden)
        self.app.register_error_handler(HTTPStatus.NOT_FOUND.value, self.handle_not_found)
        self.app.register_error_handler(HTTPStatus.METHOD_NOT_ALLOWED.value, self.handle_method_not_allowed)
        self.app.register_error_handler(HTTPStatus.INTERNAL_SERVER_ERROR.value, self.handle_internal_error)
        
        # Fallback exception handler
        self.app.register_error_handler(Exception, self.handle_unhandled_exception)
    
    def handle_validation_error(self, error: ValidationError) -> Tuple[str, int]:
        """Handle validation errors (400)."""
        return self._render_error_template(
            error_code=error.status_code,
            error_message=error.message,
            error_details=error.errors
        )
    
    def handle_generation_error(self, error: GenerationError) -> Tuple[str, int]:
        """Handle zone plate generation errors (500)."""
        return self._render_error_template(
            error_code=error.status_code,
            error_message=error.message,
            error_details=error.details
        )
    
    def handle_file_not_found_error(self, error: FileNotFoundError) -> Tuple[str, int]:
        """Handle file not found errors (404)."""
        return self._render_error_template(
            error_code=error.status_code,
            error_message=error.message,
            error_details=error.filename
        )
    
    def handle_access_denied_error(self, error: AccessDeniedError) -> Tuple[str, int]:
        """Handle access denied errors (403)."""
        return self._render_error_template(
            error_code=error.status_code,
            error_message=error.message,
            error_details=error.reason
        )
    
    def handle_bad_request(self, error: HTTPException) -> Tuple[str, int]:
        """Handle bad request errors (400)."""
        return self._render_error_template(
            error_code=HTTPStatus.BAD_REQUEST.value,
            error_message="Bad request - invalid input provided"
        )
    
    def handle_forbidden(self, error: HTTPException) -> Tuple[str, int]:
        """Handle forbidden errors (403)."""
        return self._render_error_template(
            error_code=HTTPStatus.FORBIDDEN.value,
            error_message="Access denied"
        )
    
    def handle_not_found(self, error: HTTPException) -> Tuple[str, int]:
        """Handle not found errors (404)."""
        return self._render_error_template(
            error_code=HTTPStatus.NOT_FOUND.value,
            error_message="Page not found"
        )
    
    def handle_method_not_allowed(self, error: HTTPException) -> Tuple[str, int]:
        """Handle method not allowed errors (405)."""
        return self._render_error_template(
            error_code=HTTPStatus.METHOD_NOT_ALLOWED.value,
            error_message="Method not allowed"
        )
    
    def handle_internal_error(self, error: HTTPException) -> Tuple[str, int]:
        """Handle internal server errors (500)."""
        return self._render_error_template(
            error_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            error_message="Internal server error"
        )
    
    def handle_unhandled_exception(self, error: Exception) -> Tuple[str, int]:
        """Handle any unhandled exceptions."""
        return self._render_error_template(
            error_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
            error_message="An unexpected error occurred"
        )