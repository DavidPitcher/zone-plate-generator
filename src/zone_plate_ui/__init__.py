"""Zone Plate Generator application package."""

import os
from flask import Flask
from zone_plate_ui.utils import log
from zone_plate_ui.config import LocalConfig, DevConfig, ProdConfig, LogConfig
from zone_plate_ui.models import ZonePlateGenerator
from zone_plate_ui.controllers import zoneplate_bp, HttpErrorManager

def create_app(config_class=None):
    """Application factory function.
    
    Args:
        config_class: Configuration class to use. If None, will determine 
                    from environment variable.
    
    Returns:
        A configured Flask application instance.
    """

    app = Flask(__name__)
    HttpErrorManager(app)

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
                
    config_instance = config_class()
    config_instance.load_env_config()
    LogConfig.init_app(config_instance)
    app.config.from_object(config_instance)
    
    # Initialize configuration (create directories, etc.)
    try:
        config_class.init_app()
        log.info(
            log.CFG_APP_CONFIG_SUCCESS,
            environment=app.config['FLASK_ENV'],
            port=app.config['PORT'],
            gs_timeout=app.config['GS_TIMEOUT'],
            maz_zones=app.config['MAX_ZONES'],
            max_content_length=app.config['MAX_CONTENT_LENGTH']
        )
    except Exception as e:
        log.error(log.CFG_APP_CONFIG_FAILURE, error=str(e))
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
    app.register_blueprint(zoneplate_bp)
    
    return app
