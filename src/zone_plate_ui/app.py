"""Entry point for the zone plate generator application."""

from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

from zone_plate_ui import create_app

# Create the application instance
app = create_app()


def main():
    """Main entry point for the application"""
    port = app.config['PORT']
    debug = app.config.get('DEBUG', False)
    app.logger.info(f"Port Configuration: {port}")
    app.logger.info(f"Debug Configuration: {debug}")

    app.logger.info(f"Current Working Directory: {Path.cwd()}")
    app.logger.info(f"Module Directory: {Path(__file__)}")
    app.logger.info(f"Script Directory: {Path(__file__).parent}")

    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
