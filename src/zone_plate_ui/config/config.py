"""Configuration settings for the zone plate generator application."""

import os
from pathlib import Path


class Config:
    """Base configuration class."""

    # Path Configuration
    APP_DIR = Path(__file__).parent.parent
    BASE_DIR = APP_DIR.parent.parent
    OUTPUT_DIR = BASE_DIR / "output"
    POSTSCRIPT_DIR = APP_DIR.parent / "postscript"
    POSTSCRIPT_FILE = POSTSCRIPT_DIR / "zone_plate_gen.ps"
    POSTSCRIPT_ARGS_FILE = POSTSCRIPT_DIR / "zone_plate_args.ps"

    # Environment Configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'local')
    PORT = int(os.environ.get('PORT', 8000))
    GS_TIMEOUT = int(os.environ.get('GS_TIMEOUT', 120))
    MAX_ZONES = int(os.environ.get('MAX_ZONES', 50))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))   # 16MB max file size
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-unsafe-for-production')

    # Zone Plate Default Parameters
    DEFAULT_PARAMS = {
        'focal_length': int(210),  # mm
        'rings': int(7),  # count
        'punch_diameter': float(20.0),  # mm
        'padding': float(10.0),  # mm
        'magnification': float(1.0),  # scale factor
        'wavelength': float(0.00056),  # mm (daylight)
        'sieve_scale': float(1.5),  # scale factor
        'sieve_space': float(0.04),  # mm
        'type': str('PLATE'),  # zone plate type
        'dup_focal': int(180),  # mm (camera focal length)
        'negative_mode': bool(False),  # invert colors
        'output_format': str('PNG'),  # file format
        'output_resolution': int(600)  # DPI
    }

    # Valid options
    VALID_TYPES = {
        'PLATE': 'Zone Plate',
        'SIEVE': 'Zone Sieve',
        'PHOTON': 'Photon Sieve',
        'GRID': 'Grid Pattern'
    }
    VALID_OUTPUT_FORMATS = ['PNG', 'TIFF', 'PDF']

    # Preset configurations for common use cases
    PRESETS = {
        'photography': {
            'focal_length': int(85),
            'rings': int(10),
            'wavelength': float(0.00056),
            'type': str('PLATE'),
            'punch_diameter': float(15.0),
            'magnification': float(2.0),
            'output_format': str('TIFF')
        },
        'solar': {
            'focal_length': int(500),
            'rings': int(15),
            'wavelength': float(0.00056),
            'type': str('PLATE'),
            'punch_diameter': float(50.0),
            'magnification': float(1.0),
            'output_format': str('PDF')
        },
        'microscopy': {
            'focal_length': int(10),
            'rings': int(20),
            'wavelength': float(0.00045),
            'type': str('SIEVE'),
            'punch_diameter': float(5.0),
            'magnification': float(5.0),
            'output_format': str('PNG')
        }
    }

    # Tooltip help messages
    TOOLTIPS = {
        'focal_length': 'The focal length of the zone plate in millimeters',
        'rings': 'Number of opaque rings to generate (1-50)',
        'wavelength': 'Wavelength of light (0.00022 = green, 0.00056 = daylight)',
        'output_format': 'Format for the generated image file',
        'output_resolution': 'Output image resolution in dots per inch (DPI), usually dependent on output device',
        'punch_diameter': 'Diameter of the punch outline to cut the zone plate',
        'magnification': 'Magnification factor for the printed zone plate',
        'padding': 'Padding around the zone plate',
        'negative_mode': 'Invert colors for negative film processing',
        'sieve_scale': 'Scale factor for sieve holes on a ring',
        'sieve_space': 'Space between sieve holes in millimeters',
        'dup_focal': 'Duplicating camera focal length used'
    }
    
    # Color themes
    THEMES = {
        'light': {
            'name': 'Light',
            'primary': '#007bff',
            'secondary': '#6c757d',
            'success': '#28a745',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#17a2b8',
            'background': '#ffffff',
            'surface': '#f8f9fa',
            'text': '#212529'
        },
        'dark': {
            'name': 'Dark',
            'primary': '#0d6efd',
            'secondary': '#6c757d',
            'success': '#198754',
            'danger': '#dc3545',
            'warning': '#ffc107',
            'info': '#0dcaf0',
            'background': '#121212',
            'surface': '#1e1e1e',
            'text': '#ffffff'
        },
        'blue': {
            'name': 'Ocean Blue',
            'primary': '#0077be',
            'secondary': '#4a90a4',
            'success': '#52b788',
            'danger': '#d62d20',
            'warning': '#f2cc8f',
            'info': '#81b29a',
            'background': '#f0f8ff',
            'surface': '#e6f3ff',
            'text': '#003366'
        },
        'purple': {
            'name': 'Purple Haze',
            'primary': '#6f42c1',
            'secondary': '#8e44ad',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#3498db',
            'background': '#faf5ff',
            'surface': '#f3e8ff',
            'text': '#2d1b69'
        }
    }

    # Ensure directories exist
    @classmethod
    def init_app(cls):
        """Initialize the application environment."""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

class LocalConfig(Config):
    """Local configuration."""
    
    DEBUG = True
    TESTING = True

class DevConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False


class ProdConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False

    @classmethod
    def init_app(cls):
        """Initialize the application environment."""
        super().init_app()
        # Additional production setup can go here
        # For example, configuring logging
