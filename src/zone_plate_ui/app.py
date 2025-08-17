import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the directory where this file is located
app_dir = Path(__file__).parent

app = Flask(__name__, 
           static_folder=app_dir / 'static',
           template_folder=app_dir / 'templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent.parent / "output"
POSTSCRIPT_DIR = Path(__file__).parent.parent.parent / "postscript"
POSTSCRIPT_FILE = POSTSCRIPT_DIR / "zone_plate_gen.ps"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)

# Default parameters based on PostScript file
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
    'output_format': 'PNG'
}

# Valid types and formats
VALID_TYPES = ['GRID', 'PLATE', 'SIEVE', 'PHOTON']
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


class ZonePlateGenerator:
    """Handles zone plate generation using Ghostscript"""
    
    def __init__(self, postscript_file: Path):
        self.postscript_file = postscript_file
        
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Validate input parameters and return errors if any"""
        errors = {}
        
        try:
            focal_length = float(params.get('focal_length', 0))
            if focal_length <= 0:
                errors['focal_length'] = 'Focal length must be positive'
        except (ValueError, TypeError):
            errors['focal_length'] = 'Focal length must be a valid number'
            
        try:
            rings = int(params.get('rings', 0))
            if rings <= 0 or rings > 50:
                errors['rings'] = 'Number of rings must be between 1 and 50'
        except (ValueError, TypeError):
            errors['rings'] = 'Number of rings must be a valid integer'
            
        try:
            punch_diameter = float(params.get('punch_diameter', 0))
            if punch_diameter <= 0:
                errors['punch_diameter'] = 'Punch diameter must be positive'
        except (ValueError, TypeError):
            errors['punch_diameter'] = 'Punch diameter must be a valid number'
            
        try:
            wavelength = float(params.get('wavelength', 0))
            if wavelength <= 0:
                errors['wavelength'] = 'Wavelength must be positive'
        except (ValueError, TypeError):
            errors['wavelength'] = 'Wavelength must be a valid number'
            
        if params.get('type') not in VALID_TYPES:
            errors['type'] = f'Type must be one of: {", ".join(VALID_TYPES)}'
            
        if params.get('output_format') not in VALID_OUTPUT_FORMATS:
            errors['output_format'] = f'Output format must be one of: {", ".join(VALID_OUTPUT_FORMATS)}'
            
        return errors
    
    def create_postscript_content(self, params: Dict[str, Any]) -> str:
        """Create PostScript content with user parameters"""
        with open(self.postscript_file, 'r') as f:
            content = f.read()
        
        # Replace parameter values in the PostScript content
        replacements = {
            '/FOCAL 210 def': f'/FOCAL {params["focal_length"]} def',
            '/RINGS 7 def': f'/RINGS {params["rings"]} def',
            '/PUNCH_DIAMETER 20 def': f'/PUNCH_DIAMETER {params["punch_diameter"]} def',
            '/PADDING 10 def': f'/PADDING {params["padding"]} def',
            '/MAG 1 def': f'/MAG {params["magnification"]} def',
            '/WAVE_LENGTH 0.00056 def': f'/WAVE_LENGTH {params["wavelength"]} def',
            '/SIEVE_SCALE 1.5 def': f'/SIEVE_SCALE {params["sieve_scale"]} def',
            '/SIEVE_SPACE 0.04 def': f'/SIEVE_SPACE {params["sieve_space"]} def',
            '/TYPE (PLATE) def': f'/TYPE ({params["type"]}) def',
            '/DUP_FOCAL 180 def': f'/DUP_FOCAL {params["dup_focal"]} def',
            '/NEGATIVE_MODE false def': f'/NEGATIVE_MODE {str(params["negative_mode"]).lower()} def'
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
            
        return content
    
    def generate_image(self, params: Dict[str, Any]) -> Optional[str]:
        """Generate zone plate image and return the output file path"""
        errors = self.validate_parameters(params)
        if errors:
            logger.error(f"Parameter validation failed: {errors}")
            return None
            
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            base_name = f"zone_plate_{params['type'].lower()}_{timestamp}_{unique_id}"
            
            # Create temporary PostScript file with user parameters
            ps_content = self.create_postscript_content(params)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ps', delete=False) as temp_ps:
                temp_ps.write(ps_content)
                temp_ps_path = temp_ps.name
            
            # Determine output format and Ghostscript device
            output_format = params['output_format'].upper()
            if output_format == 'PNG':
                device = 'png16m'
                extension = '.png'
            elif output_format == 'TIFF':
                device = 'tiff24nc'
                extension = '.tiff'
            elif output_format == 'PDF':
                device = 'pdfwrite'
                extension = '.pdf'
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            output_file = OUTPUT_DIR / f"{base_name}{extension}"
            
            # Build Ghostscript command
            gs_cmd = [
                'gs',
                '-dNOPAUSE',
                '-dBATCH',
                '-dSAFER',
                f'-sDEVICE={device}',
                '-r300',  # 300 DPI
                f'-sOutputFile={output_file}',
                temp_ps_path
            ]
            
            logger.info(f"Running Ghostscript command: {' '.join(gs_cmd)}")
            
            # Run Ghostscript
            result = subprocess.run(
                gs_cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            # Clean up temporary file
            os.unlink(temp_ps_path)
            
            if result.returncode != 0:
                logger.error(f"Ghostscript failed: {result.stderr}")
                return None
                
            if not output_file.exists():
                logger.error("Output file was not created")
                return None
                
            logger.info(f"Successfully generated: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return None


# Initialize generator
generator = ZonePlateGenerator(POSTSCRIPT_FILE)


@app.route('/')
def index():
    """Main page with zone plate generator form"""
    theme = request.cookies.get('theme', 'light')
    return render_template('index.html', 
                         default_params=DEFAULT_PARAMS,
                         valid_types=VALID_TYPES,
                         valid_formats=VALID_OUTPUT_FORMATS,
                         presets=PRESETS,
                         themes=THEMES,
                         current_theme=theme,
                         theme_config=THEMES[theme])


@app.route('/generate', methods=['POST'])
def generate():
    """Generate zone plate based on form parameters"""
    try:
        # Extract parameters from form
        params = {}
        for key, default_value in DEFAULT_PARAMS.items():
            form_value = request.form.get(key)
            if form_value is not None:
                if key in ['focal_length', 'punch_diameter', 'padding', 'magnification', 
                          'wavelength', 'sieve_scale', 'sieve_space', 'dup_focal']:
                    params[key] = float(form_value)
                elif key in ['rings']:
                    params[key] = int(form_value)
                elif key in ['negative_mode']:
                    params[key] = form_value.lower() == 'true'
                else:
                    params[key] = form_value
            else:
                params[key] = default_value
        
        # Validate parameters
        errors = generator.validate_parameters(params)
        if errors:
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate image
        output_file = generator.generate_image(params)
        if output_file:
            filename = Path(output_file).name
            return jsonify({
                'success': True, 
                'message': 'Zone plate generated successfully!',
                'download_url': url_for('download', filename=filename)
            })
        else:
            return jsonify({
                'success': False, 
                'errors': {'general': 'Failed to generate zone plate. Please check your parameters.'}
            }), 500
            
    except Exception as e:
        logger.error(f"Error in generate route: {str(e)}")
        return jsonify({
            'success': False, 
            'errors': {'general': f'An unexpected error occurred: {str(e)}'}
        }), 500


@app.route('/download/<filename>')
def download(filename):
    """Download generated zone plate file"""
    try:
        safe_filename = secure_filename(filename)
        file_path = OUTPUT_DIR / safe_filename
        
        if not file_path.exists():
            flash('File not found', 'error')
            return redirect(url_for('index'))
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('index'))


@app.route('/set_theme', methods=['POST'])
def set_theme():
    """Set user's theme preference"""
    if request.method == 'POST':
        # Handle both JSON and form data
        if request.is_json:
            theme = request.json.get('theme', 'light')
        else:
            theme = request.form.get('theme', 'light')
        
        if theme not in THEMES:
            theme = 'light'
        
        # For form submissions, redirect back to the referring page
        if not request.is_json:
            response = redirect(request.referrer or url_for('index'))
            response.set_cookie('theme', theme, max_age=365*24*60*60)  # 1 year
            return response
        
        # For AJAX requests, return JSON
        response = jsonify({'success': True, 'theme': theme})
        response.set_cookie('theme', theme, max_age=365*24*60*60)  # 1 year
        return response


@app.route('/health')
def health():
    """Health check endpoint for container monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ghostscript_available': True  # TODO: Add actual check
    })


@app.errorhandler(404)
def not_found(error):
    """Custom 404 page"""
    theme = request.cookies.get('theme', 'light')
    return render_template('error.html', 
                         error_code=404,
                         error_message="Page not found",
                         theme_config=THEMES[theme]), 404


@app.errorhandler(500)
def internal_error(error):
    """Custom 500 page"""
    theme = request.cookies.get('theme', 'light')
    return render_template('error.html', 
                         error_code=500,
                         error_message="Internal server error",
                         theme_config=THEMES[theme]), 500


def main():
    """Main entry point for the application"""
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_ENV') == 'local'
    
    if debug:
        app.run(host='0.0.0.0', port=port, debug=True)
    else:
        # In production, this should be run via gunicorn
        app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    main()
