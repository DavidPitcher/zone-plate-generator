"""Zone Plate Generator application package."""

import os
from flask import Flask

from .config import LocalConfig, DevConfig, ProdConfig
from .models import ZonePlateGenerator
from .controllers import main_bp, register_error_handlers
from .utils.logging_utils import configure_logging, get_logger, Component

# Configure application-level logger
configure_logging(app_name="zone_plate_ui")
logger = get_logger(__name__, Component.SYSTEM)

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
    
    # Initialize configuration (create directories, etc.)
    try:
        config_class.init_app()
        logger.info_with_code(
            message_code="CFG_INIT_SUCCESS",
            extra={'config_class': config_class.__name__}
        )
    except Exception as e:
        logger.error_with_code(
            message_code="CFG_INIT_FAILED",
            extra={'reason': str(e)}
        )
        raise
    
    # Initialize ZonePlateGenerator
    app.zone_plate_generator = ZonePlateGenerator(
        postscript_file=app.config['POSTSCRIPT_FILE'],
        postscript_args_file=app.config['POSTSCRIPT_ARGS_FILE'],
        output_dir=app.config['OUTPUT_DIR'],
        valid_types=app.config['VALID_TYPES'],
        valid_formats=app.config['VALID_OUTPUT_FORMATS']
    )
    
    # Register blueprint
    app.register_blueprint(main_bp)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app
