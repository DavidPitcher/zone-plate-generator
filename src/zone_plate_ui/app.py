"""Entry point for the zone plate generator application."""

import sys
import os
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from zone_plate_ui import create_app

# Load .env file from project root
project_root = Path(__file__).resolve().parent
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path)

# Create the application instance
try:
    app = create_app()
except Exception as e:
    sys.exit(1)

def main():
    """Main entry point for the application"""
    try:
        port = app.config['PORT']
        debug = app.config.get('DEBUG', False)
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        sys.exit(1)

if __name__ == '__main__':
    main()
