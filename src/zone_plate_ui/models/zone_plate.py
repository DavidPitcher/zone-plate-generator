"""Zone plate generator model."""

import os
import io
import uuid
import subprocess
import logging
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, TextIO, Tuple


class ZonePlateGenerator:
    """Handles zone plate generation using Ghostscript"""
    
    def __init__(self, postscript_file: Path, postscript_args_file: Path, output_dir: Path, valid_types: dict, valid_formats: list, logger=None):
        """Initialize the zone plate generator.
        
        Args:
            postscript_file: Path to the PostScript template file
            postscript_args_file: Path to the PostScript args template file
            output_dir: Directory where generated files will be saved
            valid_types: Dictionary of valid zone plate types (key: type, value: display name)
            valid_formats: List of valid output formats
            logger: Logger instance to use (if None, will create module-specific logger)
        """
        self.postscript_file = postscript_file
        self.postscript_args_file = postscript_args_file
        self.output_dir = output_dir
        self.valid_types = valid_types
        self.valid_formats = valid_formats
        self.logger = logger if logger is not None else logging.getLogger(__name__)
        
    def create_temp_args_file(self, params: Dict[str, Any], session_id: str = None) -> Path:
        """Create a temporary zone_plate_args.ps file from the template using the provided parameters.
        
        Args:
            params: Dictionary of parameters to use for token replacement
            session_id: Optional session ID to include in the temporary filename
            
        Returns:
            Path: Path to the generated temporary file
        """
        # Generate a unique session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())[:8]
        
        # Create a temporary file name with the session ID in the current working directory
        temp_file_name = f"zone_plate_args_{session_id}.ps"
        temp_file = Path.cwd() / "temp" / temp_file_name
        
        # Create temp directory if it doesn't exist
        os.makedirs(temp_file.parent, exist_ok=True)
        
        # Read the template file
        with open(self.postscript_args_file, 'r') as template_file:
            template_content = template_file.read()
        
        # Replace tokens with parameter values
        for key, value in params.items():
            # The token format in the template is {{parameter_key}}
            pattern = re.compile(r'\{\{' + re.escape(key) + r'\}\}')
            template_content = pattern.sub(str(value), template_content)
        
        # Write the processed content to the temporary file
        with open(temp_file, 'w') as output_file:
            output_file.write(template_content)
        
        self.logger.info(f"Created temporary args file: {temp_file}")
        return temp_file
        
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
            
    def generate_image(self, params: Dict[str, Any], session_id: str = None) -> Optional[str]:
        """Generate zone plate image and return the output file path
        
        Args:
            params: Dictionary of parameters for the zone plate
            session_id: Optional session ID to include in temp filename
            
        Returns:
            Optional[str]: Path to the generated file, or None if generation failed
        """
        errors = self.validate_parameters(params)
        if errors:
            self.logger.error(f"Parameter validation failed: {errors}")
            return None
            
        temp_args_file = None
        
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            base_name = f"zone_plate_{params['type'].lower()}_{timestamp}_{unique_id}"
            
            # Generate a temporary args file with the params
            temp_args_file = self.create_temp_args_file(params, session_id or unique_id)
                       
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
            
            # Build Ghostscript arguments with the temp file
            gs_args = [
                "gs",  # The name of the ghostscript interpreter (required)
                "-dNOPAUSE",  # Disable prompt and pause after each page
                "-dBATCH",    # Exit after the last file
                "-dSAFER",    # Run in safer mode
                f"-sDEVICE={device}",  # Set the output device
                f"-r{output_resolution}",  # Set resolution from parameters
                f"-sOutputFile={output_file}",  # Set output file
                f"--permit-file-read={temp_args_file.parent.relative_to(Path.cwd())}/",  # Allow Postscript to read the temp args file
                "-c",
                f"/ARGFILE ({temp_args_file.relative_to(Path.cwd())}) def",  # Use relative path for ARGFILE
                "-f",
                f"{self.postscript_file}"
            ]
                    
            self.logger.info(f"Running Ghostscript with args: {' '.join(map(str, gs_args))}")
             
            # Create default streams
            _stdout = io.StringIO()
            _stderr = io.StringIO()
                
            try:
                self.logger.info("Starting Ghostscript execution using subprocess...")
                
                # Run Ghostscript using subprocess
                process = subprocess.run(
                    gs_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,  # Don't raise exception on non-zero exit
                    shell=False   # Run directly without shell interpretation
                )
                
                # Capture stdout and stderr
                _stdout.write(process.stdout)
                _stderr.write(process.stderr)
                
                # Log the output if using default streams
                if _stdout:
                    stdout_content = _stdout.getvalue()
                    if stdout_content.strip():
                        self.logger.debug(f"Ghostscript stdout: {stdout_content}")
                if _stderr:
                    stderr_content = _stderr.getvalue()
                    if stderr_content.strip():
                        self.logger.debug(f"Ghostscript stderr: {stderr_content}")
                
                # Check process return code
                if process.returncode != 0:
                    self.logger.error(f"Ghostscript process failed with code {process.returncode}")
                    return None
                
                self.logger.info("Ghostscript execution completed successfully")
            
                # Check if output file was created
                if not output_file.exists():
                    self.logger.error("Output file was not created despite successful process exit")
                    return None
                    
                file_size = output_file.stat().st_size
                self.logger.info(f"Successfully generated: {output_file} (size: {file_size} bytes)")
                return str(output_file)
                
            except subprocess.SubprocessError as e:
                self.logger.error(f"Subprocess execution failed: {str(e)}")
                return None
        except Exception as e:
            self.logger.error(f"Error generating image: {str(e)}")
            return None
        finally:
            #Clean up the temporary file
            if temp_args_file and temp_args_file.exists():
                try:
                    os.unlink(temp_args_file)
                    self.logger.info(f"Deleted temporary args file: {temp_args_file}")
                except Exception as e:
                    self.logger.error(f"Error deleting temporary file {temp_args_file}: {str(e)}")
            else:
                self.logger.debug("No temporary args file to clean up")
