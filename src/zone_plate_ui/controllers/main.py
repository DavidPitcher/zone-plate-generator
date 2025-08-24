"""Main routes for the zone plate generator application."""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.before_request
def cleanup_expired_tokens_middleware():
    """Clean up expired download tokens before each request"""
    cleanup_expired_tokens()


@main_bp.route('/')
def index():
    """Main page with zone plate generator form"""
    from flask import current_app as app
    
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


@main_bp.route('/generate', methods=['POST'])
def generate():
    """Generate zone plate based on form parameters"""
    from flask import current_app as app
    
    try:
        # Extract parameters from form
        params = {}
        for key, default_value in app.config['DEFAULT_PARAMS'].items():
            form_value = request.form.get(key)
            if form_value is not None:
                param_type_map = {
                    # Float parameters
                    'punch_diameter': float,
                    'padding': float, 
                    'wavelength': float,
                    'sieve_scale': float,
                    'sieve_space': float,
                    
                    # Integer parameters
                    'rings': int,
                    'focal_length': int,
                    'magnification': int,
                    'dup_focal': int,
                    'output_resolution': int,
                    
                    # Boolean parameters
                    'negative_mode': lambda x: 'true' if x.lower() in ('true', 'on', 'yes', '1') else default_value
                }
                
                # Get the converter function for this parameter, or use identity function (no conversion)
                converter = param_type_map.get(key, lambda x: x)
                
                # Apply the converter to the form value
                params[key] = converter(form_value)
            else:
                params[key] = default_value
        
        # Get generator from app
        generator = app.zone_plate_generator
        
        # Validate parameters
        errors = generator.validate_parameters(params)
        if errors:
            # Return JSON error response for form validation errors
            return jsonify({'success': False, 'errors': errors}), 400
        
        # Generate image
        output_file = generator.generate_image(params)
        if output_file:
            from pathlib import Path
            import secrets
            import time
            from flask import session
            
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
            
            flash('Zone plate generated successfully!', 'success')
            return redirect(url_for('main.download', token=token))
        else:
            flash('Failed to generate zone plate. Please check your parameters.', 'error')
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"Error in generate route: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/download/<token>')
def download(token):
    """Download generated zone plate file and delete it afterwards"""
    try:
        from flask import current_app as app, after_this_request, session, abort
        import time
        
        # Verify the download token from the session
        valid_tokens = session.get('download_tokens', {})
        
        # Check if token exists and is not expired
        if token not in valid_tokens:
            logger.warning(f"Invalid download token attempted: {token}")
            flash('Access denied: Invalid download token', 'error')
            return abort(403)  # Return Forbidden status code
            
        # Check if token is expired    
        if time.time() > valid_tokens[token]['expires']:
            logger.warning(f"Expired download token attempted: {token}")
            flash('Access denied: Download link has expired', 'error')
            # Remove expired token
            valid_tokens.pop(token, None)
            session.modified = True
            return abort(403)  # Return Forbidden status code
            
        # Token is valid, remove it from session to prevent reuse
        filename = valid_tokens[token]['filename']
        session.modified = True
        valid_tokens.pop(token, None)

        file_path = app.config['OUTPUT_DIR'] / filename
        
        if not file_path.exists():
            logger.error(f"File not found for download: {file_path}")
            flash('File not found', 'error')
            return abort(404)  # Return Not Found status code
        
        # Set up a callback to delete the file after the response is sent
        @after_this_request
        def delete_after_download(response):
            try:
                # Use the generator's delete_file method to delete the file
                generator = app.zone_plate_generator
                success = generator.delete_file(filename)
                if not success:
                    logger.warning(f"Failed to delete file after download: {filename}")
            except Exception as e:
                logger.error(f"Error deleting file after download: {str(e)}")
            return response
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/set_theme', methods=['POST'])
def set_theme():
    """Set user's theme preference"""
    from flask import current_app as app
    
    if request.method == 'POST':
        
        theme = request.form.get('theme', 'light')
        
        if theme not in app.config['THEMES']:
            theme = 'light'
        
        # For form submissions, redirect back to the referring page
        response = redirect(request.referrer or url_for('main.index'))
        response.set_cookie('theme', theme, max_age=365*24*60*60)  # 1 year
        return response


def cleanup_expired_tokens():
    """Clean up expired download tokens from the session"""
    from flask import session
    import time
    
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


@main_bp.route('/health')
def health():
    """Health check endpoint for container monitoring"""
    from datetime import datetime
    import subprocess
    from flask import current_app as app
    
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
                logger.debug(f"Ghostscript version: {ghostscript_version}")
        else:
            logger.warning(f"Ghostscript check failed with return code {process.returncode}")
            if process.stderr:
                logger.warning(f"Error output: {process.stderr}")
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning(f"Ghostscript health check failed: {str(e)}")
    
    return jsonify({
        'status': 'healthy' if ghostscript_available else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'ghostscript_available': ghostscript_available,
        'ghostscript_version': ghostscript_version,
        'app_version': app.config.get('VERSION', 'unknown'),
    })
