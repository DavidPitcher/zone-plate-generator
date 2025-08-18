"""Error handlers for the zone plate generator application."""

import logging
from flask import render_template, request

# Initialize logger
logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Custom 404 page"""
        theme = request.cookies.get('theme', 'light')
        return render_template('error.html', 
                            error_code=404,
                            error_message="Page not found",
                            theme_config=app.config['THEMES'][theme]), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Custom 500 page"""
        logger.error(f"Internal server error: {error}")
        theme = request.cookies.get('theme', 'light')
        return render_template('error.html', 
                            error_code=500,
                            error_message="Internal server error",
                            theme_config=app.config['THEMES'][theme]), 500
