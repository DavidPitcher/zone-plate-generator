"""Zone plate generator model."""

import os
import tempfile
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import ghostscript


class ZonePlateGenerator:
    """Handles zone plate generation using Ghostscript"""
    
    def __init__(self, postscript_file: Path, output_dir: Path, valid_types: dict, valid_formats: list, logger=None):
        """Initialize the zone plate generator.
        
        Args:
            postscript_file: Path to the PostScript template file
            output_dir: Directory where generated files will be saved
            valid_types: Dictionary of valid zone plate types (key: type, value: display name)
            valid_formats: List of valid output formats
            logger: Logger instance to use (if None, will create module-specific logger)
        """
        self.postscript_file = postscript_file
        self.output_dir = output_dir
        self.valid_types = valid_types
        self.valid_formats = valid_formats
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        
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
            
        try:
            output_resolution = int(params.get('output_resolution', 300))
            if output_resolution <= 299 or output_resolution > 9600:
                errors['output_resolution'] = 'Resolution must be between 300 and 9600 DPI'
        except (ValueError, TypeError):
            errors['output_resolution'] = 'Resolution must be a valid integer'
            
        if params.get('type') not in self.valid_types.keys():
            errors['type'] = f'Type must be one of: {", ".join(self.valid_types.keys())}'
            
        if params.get('output_format') not in self.valid_formats:
            errors['output_format'] = f'Output format must be one of: {", ".join(self.valid_formats)}'
            
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
    
    def delete_file(self, filename: str) -> bool:
        """Delete a generated zone plate file.
        
        Args:
            filename: The name of the file to delete (without path)
            
        Returns:
            bool: True if the file was deleted successfully, False otherwise
        """
        try:
            file_path = self.output_dir / filename
            if file_path.exists():
                os.unlink(file_path)
                self.logger.info(f"Deleted file: {file_path}")
                return True
            else:
                self.logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            self.logger.error(f"Error deleting file {filename}: {str(e)}")
            return False
            
    def generate_image(self, params: Dict[str, Any]) -> Optional[str]:
        """Generate zone plate image and return the output file path"""
        errors = self.validate_parameters(params)
        if errors:
            self.logger.error(f"Parameter validation failed: {errors}")
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
            
            # Determine output format and Ghostscript device using dictionary dispatch
            output_format = params['output_format'].upper()
            format_config = {
                'PNG': {'device': 'png16m', 'extension': '.png'},
                'TIFF': {'device': 'tiff24nc', 'extension': '.tiff'},
                'PDF': {'device': 'pdfwrite', 'extension': '.pdf'}
            }
            
            if output_format not in format_config:
                raise ValueError(f"Unsupported output format: {output_format}")
                
            device = format_config[output_format]['device']
            extension = format_config[output_format]['extension']
            
            output_file = self.output_dir / f"{base_name}{extension}"
            
            # Get output resolution from params or default to 300 DPI
            output_resolution = int(params['output_resolution'])
            
            # Build Ghostscript arguments
            gs_args = [
                "gs",  # The name of the ghostscript interpreter (required)
                "-dNOPAUSE",  # Disable prompt and pause after each page
                "-dBATCH",    # Exit after the last file
                "-dSAFER",    # Run in safer mode
                f"-sDEVICE={device}",  # Set the output device
                f"-r{output_resolution}",  # Set resolution from parameters
                f"-sOutputFile={output_file}",  # Set output file
                temp_ps_path  # Input file
            ]
            
            self.logger.info(f"Running Ghostscript with args: {' '.join(gs_args)}")
            
            # Run Ghostscript using the Python ghostscript module
            try:
                # The ghostscript Python API requires a list of bytes objects (not str)
                encoding = 'utf-8'
                gs_args_bytes = [arg.encode(encoding) for arg in gs_args]
                
                # Initialize and run Ghostscript
                instance = ghostscript.Ghostscript(*gs_args_bytes)
                instance.exit()
                
                # Check if output file was created
                if not output_file.exists():
                    self.logger.error("Output file was not created")
                    return None
                    
                self.logger.info(f"Successfully generated: {output_file}")
                return str(output_file)
                
            except ghostscript.GhostscriptError as gs_error:
                self.logger.error(f"Ghostscript failed: {str(gs_error)}")
                return None
            finally:
                # Clean up temporary file
                os.unlink(temp_ps_path)
                
        except Exception as e:
            self.logger.error(f"Error generating image: {str(e)}")
            return None
