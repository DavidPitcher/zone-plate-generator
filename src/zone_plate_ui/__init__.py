"""Zone Plate Generator application package."""

import os
import logging
from flask import Flask

from .config import LocalConfig, DevConfig, ProdConfig
from .models import ZonePlateGenerator
from .controllers import main_bp, register_error_handlers

def create_app(config_class=None):
    """Application factory function.
    
    Args:
        config_class: Configuration class to use. If None, will determine 
                    from environment variable.
    
    Returns:
        A configured Flask application instance.
    """
    # Determine configuration to use
    if config_class is None:
        env = os.environ.get('FLASK_ENV', 'local')
        match env:
            case 'local':
                config_class = LocalConfig
            case 'development':
                config_class = DevConfig
            case 'production':
                config_class = ProdConfig
            case _:
                config_class = ProdConfig
    
    # Create application instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure logging based on environment
    log_level = logging.DEBUG if app.config.get('DEBUG', False) else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.info(f"Starting Zone Plate Generator with {config_class.__name__}")
    
    # Initialize configuration (create directories, etc.)
    config_class.init_app()
    
    # Initialize ZonePlateGenerator
    app.zone_plate_generator = ZonePlateGenerator(
        postscript_file=app.config['POSTSCRIPT_FILE'],
        output_dir=app.config['OUTPUT_DIR'],
        valid_types=app.config['VALID_TYPES'],
        valid_formats=app.config['VALID_OUTPUT_FORMATS']
    )
    
    # Register blueprint
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app
