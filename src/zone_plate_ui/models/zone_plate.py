"""Zone plate generator model."""

import os
import io
from sys import exception
import uuid
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from zone_plate_ui.utils import log

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

        log.info(log.MDL_ZONEPLATEGEN_INIT,
            postscript_file=postscript_file,
            postscript_args_file=postscript_args_file,
            output_dir=output_dir,
            valid_types=valid_types,
            valid_formats=valid_formats
        )

    def create_temp_args_file(self, params: Dict[str, Any], session_id: str) -> Path:
        """Create a temporary zone_plate_args.ps file from the template using the provided parameters.
        
        Args:
            params: Dictionary of parameters to use for token replacement
            session_id: Session ID to include in the temporary filename
            
        Returns:
            Path: Path to the generated temporary file
            
        Raises:
            ValueError: If session_id is None or empty
            FileNotFoundError: If template file cannot be found
            IOError: If there's an error reading or writing files
            Exception: For any other unexpected errors
        """
        temp_file = None
        try:
            # Validate session_id is provided
            if not session_id:
                raise ValueError("session_id is required for creating temporary argument files")
            
            # Create a temporary file name with the session ID in the current working directory
            temp_file_name = f"zone_plate_args_{session_id}.ps"
            temp_file = Path.cwd() / "temp" / temp_file_name
            
            # Create temp directory if it doesn't exist
            try:
                os.makedirs(temp_file.parent, exist_ok=True)
            except PermissionError as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Permission denied creating postscript arguments temp directory: {temp_file.parent}",
                    detailed_error=str(e),
                    session_id=session_id
                )
                raise
            except Exception as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Failed to create temp directory: {temp_file.parent}",
                    detailed_error=str(e),
                    session_id=session_id
                )
                raise
            
            # Read the template file
            try:
                with open(self.postscript_args_file, 'r') as template_file:
                    template_content = template_file.read()
            except FileNotFoundError as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Postscript arguments template file no found: {self.postscript_args_file}",
                    detailed_error=str(e),
                    session_id=session_id
                )
                raise
            except PermissionError as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Permission denied reading the postscript arguments template file: {str(e)}",
                    detailed_error=str(e),
                    session_id=session_id
                )
                raise
            except Exception as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Failed to read the postscript arguments template file: {str(e)}",
                    session_id=session_id
                )
                raise
            
            # Replace tokens with parameter values
            try:
                for key, value in params.items():
                    # The token format in the template is {{parameter_key}}
                    pattern = re.compile(r'\{\{' + re.escape(key) + r'\}\}')
                    template_content = pattern.sub(str(value), template_content)
            except Exception as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Failed to replace tokens: {str(e)}",
                    session_id=session_id
                )
                raise
            
            # Write the processed content to the temporary file
            try:
                with open(temp_file, 'w') as output_file:
                    output_file.write(template_content)
            except PermissionError as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Permission denied writing temp file: {str(e)}",
                    session_id=session_id
                )
                raise
            except Exception as e:
                log.error(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=f"Failed to write temp file: {str(e)}",
                    session_id=session_id
                )
                raise

            log.info(
                log.MDL_ZONEPLATEGEN_ARGSFILE,
                params=params,
                session_id=session_id,
                temp_file=str(temp_file)
            )

            return temp_file
            
        except Exception as e:
            # Log and re-raise any exceptions not specifically caught above
            if not isinstance(e, (ValueError, FileNotFoundError, PermissionError)):
                log.exception(
                    log.MDL_ZONEPLATEGEN_ARGSFILE_FAILED,
                    error=str(e),
                    session_id=session_id
                )
            raise
        
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Validate input parameters and return errors if any"""
        errors = {}
        
        try:
            focal_length = float(params.get('focal_length', 0))
            if focal_length <= 0:
                errors['focal_length'] = f'Focal length must be positive: {focal_length}'
        except (ValueError, TypeError):
            errors['focal_length'] = f'Focal length must be a valid number: {params.get("focal_length", "unknown")}'

        try:
            rings = int(params.get('rings', 0))
            if rings <= 0 or rings > 50:
                errors['rings'] = f'Number of rings must be between 1 and 50: {rings}'
        except (ValueError, TypeError):
            errors['rings'] = f'Number of rings must be a valid integer: {params.get("rings", "unknown")}'

        try:
            punch_diameter = float(params.get('punch_diameter', 0))
            if punch_diameter <= 0:
                errors['punch_diameter'] = f'Punch diameter must be positive: {punch_diameter}'
        except (ValueError, TypeError):
            errors['punch_diameter'] = f'Punch diameter must be a valid number: {params.get("punch_diameter", "unknown")}'

        try:
            wavelength = float(params.get('wavelength', 0))
            if wavelength <= 0:
                errors['wavelength'] = f'Wavelength must be positive: {wavelength}'
        except (ValueError, TypeError):
            errors['wavelength'] = f'Wavelength must be a valid number: {params.get("wavelength", "unknown")}'

        try:
            output_resolution = int(params.get('output_resolution', 300))
            if output_resolution <= 299 or output_resolution > 9600:
                errors['output_resolution'] = f'Resolution must be between 300 and 9600 DPI: {output_resolution}'
        except (ValueError, TypeError):
            errors['output_resolution'] = f'Resolution must be a valid integer: {params.get("output_resolution", "unknown")}'

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
                log.info(
                    log.MDL_ZONEPLATEGEN_DELETEFILE,
                    deleted_file=file_path
                )
                return True
            else:
                return False
        except Exception as e:
            raise 
            
    def generate_image(self, params: Dict[str, Any], session_id: Optional[str] = None) -> Optional[str]:
        """Generate zone plate image and return the output file path
        
        Args:
            params: Dictionary of parameters for the zone plate
            session_id: Optional session ID to include in temp filename
            
        Returns:
            Optional[str]: Path to the generated file, or None if generation failed
        """
        errors = self.validate_parameters(params)
        if errors:
            return None
            
        temp_args_file = None
        
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            base_name = f"zone_plate_{params['type'].lower()}_{timestamp}_{unique_id}"
            
            # Ensure we have a session ID
            if not session_id:
                session_id = unique_id
            
            # Generate a temporary args file with the params
            temp_args_file = self.create_temp_args_file(params, session_id)
                       
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
                "-dFAILUREONERROR",  # Stop processing on errors
                f"-sDEVICE={device}",  # Set the output device
                f"-r{output_resolution}",  # Set resolution from parameters
                f"-sOutputFile={output_file}",  # Set output file
                f"--permit-file-read={temp_args_file.parent.relative_to(Path.cwd())}/",  # Allow Postscript to read the temp args file
                "-c",
                f"/ARGFILE ({temp_args_file.relative_to(Path.cwd())}) def",  # Use relative path for ARGFILE
                "-f",
                f"{self.postscript_file}"
            ]
             
            # Create default streams
            _stdout = io.StringIO()
            _stderr = io.StringIO()
                
            try:
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
                
                # Get the content from streams for logging and analysis
                stdout_content = _stdout.getvalue()
                stderr_content = _stderr.getvalue()
                
                if process.returncode != 0:
                    log.error(
                        log.MDL_ZONEPLATEGEN_GSPROCESS_FAILED,
                        exit_code=process.returncode,
                        error=stderr_content[:200] if stderr_content else "No error details"
                    )

                if process.returncode == 0:
                    log.info(
                        log.MDL_ZONEPLATEGEN_GSPROCESS_SUCCESS,
                        stdout=stdout_content[:200] if stdout_content else "No output"
                    )

                if not output_file.exists() and output_file.stat().st_size <= 0:
                    log.error(
                        log.MDL_ZONEPLATEGEN_OUTPUT_FAILED,
                        output_file=str(output_file)
                    )
                    return None                

                return str(output_file)
                
            except subprocess.SubprocessError as e:
                return None
            except FileNotFoundError as e:
                return None
            
        except Exception as e:
            return None
        finally:
            #Clean up the temporary file
            self.delete_file(temp_args_file.name) if temp_args_file else None
            