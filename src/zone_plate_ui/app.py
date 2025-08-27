"""Entry point for the zone plate generator application."""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

from zone_plate_ui import create_app, logger
from zone_plate_ui.utils.logging_utils import log_exception

# Create the application instance
try:
    app = create_app()
except Exception as e:
    # Log any startup exceptions
    log_exception(logger, message_code="SYS_STARTUP_FAILED", reason=str(e))
    sys.exit(1)


def main():
    """Main entry point for the application"""
    try:
        port = app.config['PORT']
        debug = app.config.get('DEBUG', False)

        logger.info_with_code(
            message_code="SYS_APP_SERVER_STARTUP",
            extra={
                'port': port
            }
        )
        
        logger.debug_with_code(
            message_code="SYS_APP_ENVIRONMENT",
            extra={
                'cwd': str(Path.cwd()),
                'module_path': str(Path(__file__)),
                'script_dir': str(Path(__file__).parent)
            }
        )
        
        # Run the application
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        # Log any runtime exceptions
        log_exception(logger, message_code="SYS_STARTUP_FAILED", reason=str(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
