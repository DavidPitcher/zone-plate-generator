"""Error handlers for the zone plate generator application."""

from flask import render_template, request, jsonify
from werkzeug.exceptions import HTTPException

from ..utils.logging_utils import get_logger, Component, log_exception

# Initialize logger with component type
logger = get_logger(__name__, Component.CONTROLLER)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    
    def __init__(self, message: str, errors: dict = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)


class GenerationError(Exception):
    """Custom exception for zone plate generation errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class FileNotFoundError(Exception):
    """Custom exception for file not found errors."""
    
    def __init__(self, message: str, filename: str = None):
        self.message = message
        self.filename = filename
        super().__init__(self.message)


class AccessDeniedError(Exception):
    """Custom exception for access denied errors."""
    
    def __init__(self, message: str, reason: str = None):
        self.message = message
        self.reason = reason
        super().__init__(self.message)


def get_theme_config(app):
    """Get theme configuration for error pages."""
    theme = request.cookies.get('theme', 'light')
    return {
        'current_theme': theme,
        'theme_config': app.config['THEMES'][theme],
        'themes': app.config['THEMES']
    }


def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(ValidationError)
    def validation_error(error):
        """Handle validation errors (400)"""
        logger.warning_with_code(
            "Validation error occurred",
            message_code="VALIDATION_FAILED",
            error_details=error.errors,
            message=error.message
        )
        
        # For AJAX requests, return JSON
        if request.is_json or request.headers.get('Content-Type') == 'application/json':
            return jsonify({
                'success': False,
                'error': error.message,
                'errors': error.errors
            }), 400
        
        # For regular requests, show error page
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=400,
                            error_message=error.message,
                            error_details=error.errors,
                            **theme_config), 400
    
    @app.errorhandler(GenerationError)
    def generation_error(error):
        """Handle zone plate generation errors (500)"""
        logger.error_with_code(
            "Zone plate generation error",
            message_code="GENERATION_FAILED",
            reason=error.message,
            details=error.details
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=500,
                            error_message=error.message,
                            error_details=error.details,
                            **theme_config), 500
    
    @app.errorhandler(FileNotFoundError)
    def file_not_found_error(error):
        """Handle file not found errors (404)"""
        logger.warning_with_code(
            "File not found error",
            message_code="FILE_NOT_FOUND", 
            filename=error.filename
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=404,
                            error_message=error.message,
                            error_details=error.filename,
                            **theme_config), 404
    
    @app.errorhandler(AccessDeniedError)
    def access_denied_error(error):
        """Handle access denied errors (403)"""
        logger.warning_with_code(
            "Access denied error", 
            message_code="ACCESS_DENIED",
            reason=error.reason
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=403,
                            error_message=error.message,
                            error_details=error.reason,
                            **theme_config), 403
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors (400)"""
        logger.warning_with_code(
            "Bad request", 
            message_code="BAD_REQUEST",
            details=str(error),
            path=request.path
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=400,
                            error_message="Bad request - invalid input provided",
                            **theme_config), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle forbidden errors (403)"""
        logger.warning_with_code(
            "Forbidden access", 
            message_code="ACCESS_DENIED",
            path=request.path,
            method=request.method
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=403,
                            error_message="Access denied",
                            **theme_config), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors (404)"""
        logger.warning_with_code(
            "Page not found", 
            message_code="FILE_NOT_FOUND",
            path=request.path
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=404,
                            error_message="Page not found",
                            **theme_config), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle method not allowed errors (405)"""
        logger.warning_with_code(
            "Method not allowed", 
            message_code="METHOD_NOT_ALLOWED",
            method=request.method,
            path=request.path
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=405,
                            error_message="Method not allowed",
                            **theme_config), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle internal server errors (500)"""
        log_exception(
            logger, 
            message_code="UNHANDLED_ERROR",
            path=request.path,
            method=request.method
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=500,
                            error_message="Internal server error",
                            **theme_config), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        """Handle any unhandled exceptions"""
        log_exception(
            logger, 
            message_code="UNHANDLED_ERROR",
            error=str(error),
            path=request.path,
            method=request.method
        )
        
        theme_config = get_theme_config(app)
        return render_template('error.html',
                            error_code=500,
                            error_message="An unexpected error occurred",
                            **theme_config), 500
