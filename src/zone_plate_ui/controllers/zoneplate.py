import secrets
import subprocess
import time
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint, 
    after_this_request,
    jsonify,
    render_template, 
    request, 
    redirect, 
    url_for, 
    send_file, 
    session, 
    url_for, 
    current_app as app
)

from zone_plate_ui.controllers.errors import (
    ValidationError, 
    GenerationError, 
    FileNotFoundError, 
    AccessDeniedError
)

from zone_plate_ui.utils import log

# Create blueprint
zoneplate_bp = Blueprint('zoneplate', __name__)

@zoneplate_bp.before_request
def cleanup_expired_tokens_middleware():
    """Clean up expired download tokens before each request"""
    cleanup_expired_tokens()

@zoneplate_bp.route('/')
def index():
    """Main page with zone plate generator form"""

    theme = request.cookies.get('theme', 'light')
    return render_template('index.html', 
                          default_params=app.config['DEFAULT_PARAMS'],
                          valid_types=app.config['VALID_TYPES'],
                          valid_formats=app.config['VALID_OUTPUT_FORMATS'],
                          presets=app.config['PRESETS'],
                          themes=app.config['THEMES'],
                          current_theme=theme,
                          theme_config=app.config['THEMES'][theme],
                          tooltips=app.config['TOOLTIPS'])


@zoneplate_bp.route('/generate', methods=['POST'])
def generate():
    """Generate zone plate based on form parameters"""
    
    try:
        # Extract parameters from form
        params = {}
        for key, default_value in app.config['DEFAULT_PARAMS'].items():
            form_value = request.form.get(key)
            if form_value is not None:
                param_type_map = {
                    'punch_diameter': float,
                    'padding': float, 
                    'wavelength': float,
                    'sieve_scale': float,
                    'sieve_space': float,
                    'rings': int,
                    'focal_length': int,
                    'magnification': int,
                    'dup_focal': int,
                    'output_resolution': int,
                    'negative_mode': lambda x: 'true' if x.lower() in ('true', 'on', 'yes', '1') else default_value
                }
                converter = param_type_map.get(key, lambda x: x)
                params[key] = converter(form_value)
            else:
                params[key] = default_value
        log.info(log.WEB_GENERATE_POST_PARAMS, params=params)
        
        generator = app.zone_plate_generator
        errors = generator.validate_parameters(params)
        if errors:
            # Raise validation error to be handled by error handler
            raise ValidationError("Invalid input parameters provided", errors)
        
        output_file = generator.generate_image(params)
        if output_file:
            
            # Create a secure download token
            filename = Path(output_file).name
            token = secrets.token_urlsafe(32)  # 32 bytes of randomness
            
            # Store token in session with expiration (5 minutes)
            expiration = time.time() + 300  # Current time + 5 minutes
            if 'download_tokens' not in session:
                session['download_tokens'] = {}
                
            session['download_tokens'][token] = {
                'filename': filename,
                'expires': expiration
            }
            session.modified = True
                
            return redirect(url_for('zoneplate.download', token=token))
        else:
            raise GenerationError("Failed to generate zone plate. Please check your parameters.")
            
    except ValidationError:
        # Re-raise validation errors to be handled by error handler
        raise
    except Exception as e:
        raise GenerationError(f"An unexpected error occurred: {str(e)}")


@zoneplate_bp.route('/download/<token>')
def download(token):
    """Download generated zone plate file and delete it afterwards"""
    try:
        
        # Verify the download token from the session
        valid_tokens = session.get('download_tokens', {})
        
        # Check if token exists and is not expired
        if token not in valid_tokens:
            raise AccessDeniedError("Invalid download token", "The download link is invalid or has been used")
            
        # Check if token is expired    
        if time.time() > valid_tokens[token]['expires']:
            # Remove expired token
            valid_tokens.pop(token, None)
            session.modified = True
            raise AccessDeniedError("Download link has expired", "Please generate a new zone plate to get a fresh download link")
            
        # Token is valid, remove it from session to prevent reuse
        filename = valid_tokens[token]['filename']
        session.modified = True
        valid_tokens.pop(token, None)

        file_path = app.config['OUTPUT_DIR'] / filename
        
        if not file_path.exists():
            raise FileNotFoundError("File not found", filename)
        
        # Set up a callback to delete the file after the response is sent
        @after_this_request
        def delete_after_download(response):
            try:
                # Use the generator's delete_file method to delete the file
                generator = app.zone_plate_generator
                success = generator.delete_file(filename)
            except Exception as e:
                raise GenerationError("Error deleting file after download", str(e))
            
            return response
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except (AccessDeniedError, FileNotFoundError):
        # Re-raise custom errors to be handled by error handlers
        raise

    except Exception as e:
        raise GenerationError("Error downloading file", str(e))


@zoneplate_bp.route('/set_theme', methods=['POST'])
def set_theme():
    """Set user's theme preference"""
    
    if request.method == 'POST':
        
        theme = request.form.get('theme', 'light')
        
        if theme not in app.config['THEMES']:
            theme = 'light'
        
        # For form submissions, redirect back to the referring page
        response = redirect(request.referrer or url_for('zoneplate.index'))
        response.set_cookie('theme', theme, max_age=365*24*60*60)  # 1 year
        return response


def cleanup_expired_tokens():
    """Clean up expired download tokens from the session"""
    
    if 'download_tokens' in session:
        # Find expired tokens
        current_time = time.time()
        expired_tokens = [token for token, data in session['download_tokens'].items() 
                         if current_time > data['expires']]
        
        # Remove expired tokens
        if expired_tokens:
            for token in expired_tokens:
                session['download_tokens'].pop(token, None)
            session.modified = True


@zoneplate_bp.route('/health')
def health():
    """Health check endpoint for container monitoring"""
    
    # Clean up expired tokens on health checks
    cleanup_expired_tokens()
    
    # Check if Ghostscript is available
    ghostscript_available = False
    ghostscript_version = "Unknown"
    try:
        # Try to run Ghostscript version check as a subprocess
        process = subprocess.run(
            ["gs", "-v"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Don't raise an exception on non-zero exit
            timeout=5     # Timeout after 5 seconds
        )
        
        # Check if process was successful
        if process.returncode == 0:
            ghostscript_available = True
            # Extract version information from stdout
            output = process.stdout
            if output:
                # Usually the first line contains version info
                first_line = output.splitlines()[0] if output.splitlines() else "Unknown"
                ghostscript_version = first_line.strip()
        else:
            # Log the failure
            raise Exception(f"Ghostscript returned non-zero exit code {process.returncode}")

    except (subprocess.SubprocessError, OSError) as e:
        raise
    
    return jsonify({
        'status': 'healthy' if ghostscript_available else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'ghostscript_available': ghostscript_available,
        'ghostscript_version': ghostscript_version,
        'app_version': app.config.get('VERSION', 'unknown'),
    })
