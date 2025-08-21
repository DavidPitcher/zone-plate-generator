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

    # Environment Configuration
    FLASK_ENV = os.environ.get('FLASK_ENV', 'local')
    PORT = int(os.environ.get('PORT', 8000))
    GS_TIMEOUT = int(os.environ.get('GS_TIMEOUT', 120))
    MAX_ZONES = int(os.environ.get('MAX_ZONES', 50))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))   # 16MB max file size
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-unsafe-for-production')

    # Zone Plate Default Parameters
    DEFAULT_PARAMS = {
        'focal_length': 210,
        'rings': 7,
        'punch_diameter': 20,
        'padding': 10,
        'magnification': 1,
        'wavelength': 0.00056,
        'sieve_scale': 1.5,
        'sieve_space': 0.04,
        'type': 'PLATE',
        'dup_focal': 180,
        'negative_mode': False,
        'output_format': 'PNG',
        'output_resolution': 300
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
            'focal_length': 85,
            'rings': 10,
            'wavelength': 0.00056,
            'type': 'PLATE',
            'punch_diameter': 15,
            'magnification': 2,
            'output_format': 'TIFF'
        },
        'solar': {
            'focal_length': 500,
            'rings': 15,
            'wavelength': 0.00056,
            'type': 'PLATE',
            'punch_diameter': 50,
            'magnification': 1,
            'output_format': 'PDF'
        },
        'microscopy': {
            'focal_length': 10,
            'rings': 20,
            'wavelength': 0.00045,
            'type': 'SIEVE',
            'punch_diameter': 5,
            'magnification': 5,
            'output_format': 'PNG'
        }
    }

    # Tooltip help messages
    TOOLTIPS = {
        'focal_length': 'The focal length of the zone plate in millimeters',
        'rings': 'Number of opaque rings to generate (1-50)',
        'wavelength': 'Wavelength of light (0.00022 = green, 0.00056 = daylight)',
        'output_format': 'Format for the generated image file',
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
