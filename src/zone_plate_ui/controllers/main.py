"""Main routes for the zone plate generator application."""

from flask import Blueprint, render_template, request, redirect, url_for, send_file, current_app

from .errors import ValidationError, GenerationError, FileNotFoundError, AccessDeniedError
from ..utils.logging_utils import get_logger, Component, log_exception

# Create blueprint
main_bp = Blueprint('main', __name__)

# Initialize logger with component type
logger = get_logger(__name__, Component.CONTROLLER)

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
        
        generator = app.zone_plate_generator
        
        errors = generator.validate_parameters(params)
        if errors:
            # Raise validation error to be handled by error handler
            raise ValidationError("Invalid input parameters provided", errors)
        
        # Generate image
        logger.info_with_code(
            "Generating zone plate image",
            extra={'params': {k: v for k, v in params.items() if k not in ('negative_mode')}}
        )
        
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
            
            logger.info_with_code(
                "Zone plate generated successfully",
                extra={
                    'filename': filename,
                    'token': token[:8] + '...',  # Log only part of the token for security
                    'expiration': expiration
                }
            )
            
            return redirect(url_for('main.download', token=token))
        else:
            logger.error_with_code(
                "Failed to generate zone plate image", 
                message_code="GENERATION_FAILED",
                params_summary=str(params.get('type')) + " " + str(params.get('output_format'))
            )
            raise GenerationError("Failed to generate zone plate. Please check your parameters.")
            
    except ValidationError:
        # Re-raise validation errors to be handled by error handler
        raise
    except Exception as e:
        log_exception(
            logger, 
            message_code="GENERATION_FAILED", 
            reason=str(e),
            params_summary=str(params.get('type', 'unknown')) if 'params' in locals() else 'unknown'
        )
        raise GenerationError(f"An unexpected error occurred: {str(e)}")


@main_bp.route('/download/<token>')
def download(token):
    """Download generated zone plate file and delete it afterwards"""
    try:
        from flask import current_app as app, after_this_request, session
        import time
        
        # Verify the download token from the session
        valid_tokens = session.get('download_tokens', {})
        
        # Check if token exists and is not expired
        if token not in valid_tokens:
            logger.warning_with_code(
                "Invalid download token attempted", 
                message_code="INVALID_TOKEN",
                token=token[:8] + '...' if len(token) > 8 else token  # Partial token for security
            )
            raise AccessDeniedError("Invalid download token", "The download link is invalid or has been used")
            
        # Check if token is expired    
        if time.time() > valid_tokens[token]['expires']:
            logger.warning_with_code(
                "Expired download token attempted", 
                message_code="TOKEN_EXPIRED",
                token=token[:8] + '...' if len(token) > 8 else token,  # Partial token for security
                expiry_time=valid_tokens[token]['expires']
            )
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
            logger.error_with_code(
                "File not found for download", 
                message_code="FILE_NOT_FOUND",
                filename=filename,
                file_path=str(file_path)
            )
            raise FileNotFoundError("File not found", filename)
        
        # Set up a callback to delete the file after the response is sent
        @after_this_request
        def delete_after_download(response):
            try:
                # Use the generator's delete_file method to delete the file
                generator = app.zone_plate_generator
                success = generator.delete_file(filename)
                if not success:
                    logger.warning_with_code(
                        "Failed to delete file after download", 
                        message_code="FILE_DELETE_FAILED",
                        filename=filename
                    )
                else:
                    logger.info_with_code(
                        "File deleted after download",
                        extra={'filename': filename}
                    )
            except Exception as e:
                log_exception(
                    logger, 
                    message_code="CTRL_FILE_DELETE_FAILED",
                    filename=filename
                )
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
        log_exception(
            logger, 
            message_code="CTRL_UNHANDLED_ERROR",
            context="download_route", 
            token=token[:8] + '...' if 'token' in locals() and len(token) > 8 else 'unknown'
        )
        raise GenerationError("Error downloading file", str(e))


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
    from flask import current_app as app, jsonify
    
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
                logger.debug_with_code(
                    "Ghostscript version detected",
                    extra={'version': ghostscript_version}
                )
        else:
            logger.warning_with_code(
                "Ghostscript check failed", 
                message_code="RESOURCE_UNAVAILABLE",
                resource="ghostscript",
                return_code=process.returncode,
                stderr=process.stderr[:100] if process.stderr else "None"  # Limit stderr log
            )
    except (subprocess.SubprocessError, OSError) as e:
        logger.warning_with_code(
            "Ghostscript health check failed", 
            message_code="RESOURCE_UNAVAILABLE",
            resource="ghostscript",
            reason=str(e)
        )
    
    return jsonify({
        'status': 'healthy' if ghostscript_available else 'degraded',
        'timestamp': datetime.now().isoformat(),
        'ghostscript_available': ghostscript_available,
        'ghostscript_version': ghostscript_version,
        'app_version': app.config.get('VERSION', 'unknown'),
    })
