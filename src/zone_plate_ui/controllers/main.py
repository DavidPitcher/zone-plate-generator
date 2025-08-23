"""Main routes for the zone plate generator application."""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename

from ..models.zone_plate import ZonePlateGenerator

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)


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
            filename = Path(output_file).name
            flash('Zone plate generated successfully!', 'success')
            return redirect(url_for('main.download', filename=filename))
        else:
            flash('Failed to generate zone plate. Please check your parameters.', 'error')
            return redirect(url_for('main.index'))
            
    except Exception as e:
        logger.error(f"Error in generate route: {str(e)}")
        flash(f'An unexpected error occurred: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@main_bp.route('/download/<filename>')
def download(filename):
    """Download generated zone plate file and delete it afterwards"""
    try:
        from flask import current_app as app, after_this_request
        from pathlib import Path
        import functools
        
        safe_filename = secure_filename(filename)
        file_path = app.config['OUTPUT_DIR'] / safe_filename
        
        if not file_path.exists():
            flash('File not found', 'error')
            return redirect(url_for('main.index'))
        
        # Set up a callback to delete the file after the response is sent
        @after_this_request
        def delete_after_download(response):
            try:
                # Use the generator's delete_file method to delete the file
                generator = app.zone_plate_generator
                success = generator.delete_file(safe_filename)
                if not success:
                    logger.warning(f"Failed to delete file after download: {safe_filename}")
            except Exception as e:
                logger.error(f"Error deleting file after download: {str(e)}")
            return response
            
        return send_file(
            file_path,
            as_attachment=True,
            download_name=safe_filename
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


@main_bp.route('/health')
def health():
    """Health check endpoint for container monitoring"""
    from datetime import datetime
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'ghostscript_available': True  # TODO: Add actual check
    })
