import pytest
import tempfile
import os
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from zone_plate_ui.app import app, ZonePlateGenerator, DEFAULT_PARAMS


@pytest.fixture
def client():
    """Create a test client"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


@pytest.fixture
def generator():
    """Create a zone plate generator instance"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps', delete=False) as f:
        f.write("""
%!PS
/FOCAL 210 def
/RINGS 7 def
/PUNCH_DIAMETER 20 def
/PADDING 10 def
/MAG 1 def
/WAVE_LENGTH 0.00056 def
/SIEVE_SCALE 1.5 def
/SIEVE_SPACE 0.04 def
/TYPE (PLATE) def
/DUP_FOCAL 180 def
/NEGATIVE_MODE false def
showpage
""")
        ps_file = Path(f.name)
    
    # Create a test logger
    test_logger = logging.getLogger('test_zone_plate')
    test_logger.setLevel(logging.DEBUG)
    
    # Create the generator with the test logger
    yield ZonePlateGenerator(
        postscript_file=ps_file,
        output_dir=Path('.'),
        valid_types={'PLATE': 'Zone Plate', 'SIEVE': 'Zone Sieve'},
        valid_formats=['PNG', 'TIFF', 'PDF'],
        logger=test_logger
    )
    
    # Cleanup
    if ps_file.exists():
        ps_file.unlink()


class TestZonePlateGenerator:
    """Test the ZonePlateGenerator class"""
    
    def test_validate_parameters_valid(self, generator):
        """Test parameter validation with valid parameters"""
        params = DEFAULT_PARAMS.copy()
        errors = generator.validate_parameters(params)
        assert errors == {}
    
    def test_validate_parameters_invalid_focal_length(self, generator):
        """Test parameter validation with invalid focal length"""
        params = DEFAULT_PARAMS.copy()
        params['focal_length'] = -10
        errors = generator.validate_parameters(params)
        assert 'focal_length' in errors
    
    def test_validate_parameters_invalid_rings(self, generator):
        """Test parameter validation with invalid rings"""
        params = DEFAULT_PARAMS.copy()
        params['rings'] = 100
        errors = generator.validate_parameters(params)
        assert 'rings' in errors
    
    def test_validate_parameters_invalid_type(self, generator):
        """Test parameter validation with invalid type"""
        params = DEFAULT_PARAMS.copy()
        params['type'] = 'INVALID'
        errors = generator.validate_parameters(params)
        assert 'type' in errors
    
    def test_create_postscript_content(self, generator):
        """Test PostScript content creation"""
        params = DEFAULT_PARAMS.copy()
        params['focal_length'] = 300
        params['rings'] = 10
        
        content = generator.create_postscript_content(params)
        assert '/FOCAL 300 def' in content
        assert '/RINGS 10 def' in content
    
    @patch('subprocess.run')
    @patch('tempfile.NamedTemporaryFile')
    def test_generate_image_success(self, mock_tempfile, mock_subprocess, generator):
        """Test successful image generation"""
        # Mock temporary file
        mock_temp = MagicMock()
        mock_temp.name = '/tmp/test.ps'
        mock_tempfile.return_value.__enter__.return_value = mock_temp
        
        # Mock subprocess success
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result
        
        # Mock output file existence
        with patch('pathlib.Path.exists', return_value=True):
            params = DEFAULT_PARAMS.copy()
            result = generator.generate_image(params)
            assert result is not None
            assert isinstance(result, str)
    
    @patch('subprocess.run')
    def test_generate_image_ghostscript_failure(self, mock_subprocess, generator):
        """Test image generation with Ghostscript failure"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Ghostscript error"
        mock_subprocess.return_value = mock_result
        
        params = DEFAULT_PARAMS.copy()
        result = generator.generate_image(params)
        assert result is None
        
    def test_delete_file(self, generator):
        """Test file deletion functionality"""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.png', delete=False) as f:
            test_file = Path(f.name)
            filename = test_file.name
        
        # Test successful deletion
        with patch('pathlib.Path.exists', return_value=True), \
             patch('os.unlink') as mock_unlink:
            success = generator.delete_file(filename)
            assert success is True
            mock_unlink.assert_called_once()
            
        # Test file not found
        with patch('pathlib.Path.exists', return_value=False), \
             patch('os.unlink') as mock_unlink:
            success = generator.delete_file(filename)
            assert success is False
            mock_unlink.assert_not_called()
            
        # Test exception during deletion
        with patch('pathlib.Path.exists', return_value=True), \
             patch('os.unlink', side_effect=OSError("Test error")):
            success = generator.delete_file(filename)
            assert success is False


class TestFlaskApp:
    """Test the Flask application"""
    
    def test_index_page(self, client):
        """Test the main index page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Zone Plate Generator' in response.data
        assert b'Generate Zone Plate' in response.data
    
    @patch('ghostscript.Ghostscript')
    def test_health_endpoint_gs_available(self, mock_gs, client):
        """Test the health check endpoint when Ghostscript is available"""
        # Mock successful Ghostscript instantiation
        mock_gs_instance = MagicMock()
        mock_gs.return_value = mock_gs_instance
        
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['ghostscript_available'] == True
        assert 'timestamp' in data
        assert 'app_version' in data
        
    @patch('ghostscript.Ghostscript', side_effect=Exception("Ghostscript not available"))
    def test_health_endpoint_gs_unavailable(self, mock_gs, client):
        """Test the health check endpoint when Ghostscript is unavailable"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'degraded'
        assert data['ghostscript_available'] == False
        assert 'timestamp' in data
    
    def test_set_theme(self, client):
        """Test theme setting endpoint"""
        response = client.post('/set_theme', 
                             json={'theme': 'dark'},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['theme'] == 'dark'
    
    def test_set_invalid_theme(self, client):
        """Test setting invalid theme"""
        response = client.post('/set_theme', 
                             json={'theme': 'invalid'},
                             content_type='application/json')
        assert response.status_code == 200
        data = response.get_json()
        assert data['theme'] == 'light'  # Should default to light
    
    @patch('src.zone_plate_ui.app.generator.generate_image')
    def test_generate_success(self, mock_generate, client):
        """Test successful zone plate generation"""
        mock_generate.return_value = '/path/to/output.png'
        
        response = client.post('/generate', data=DEFAULT_PARAMS)
        assert response.status_code == 302  # Redirect status code
        
        # Should redirect to download URL with token
        assert '/download/' in response.location  
        
        # URL format should be /download/<token>/<filename>
        url_parts = response.location.split('/')
        assert len(url_parts) >= 4  # At least 4 parts: '', 'download', 'token', 'filename'
        
        # Check that a download token was stored in session
        with client.session_transaction() as session:
            assert 'download_tokens' in session
            # The token from the URL should be in the session
            token = url_parts[-2]  # Second to last part of URL
            assert token in session['download_tokens']
    
    @patch('src.zone_plate_ui.app.generator.validate_parameters')
    def test_generate_validation_error(self, mock_validate, client):
        """Test generation with validation errors"""
        # We'll keep validation errors as JSON responses for better form handling
        mock_validate.return_value = {'focal_length': 'Invalid value'}
        
        response = client.post('/generate', data=DEFAULT_PARAMS)
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] == False
        assert 'errors' in data
    
    @patch('src.zone_plate_ui.app.generator.generate_image')
    def test_generate_generation_failure(self, mock_generate, client):
        """Test generation failure"""
        mock_generate.return_value = None
        
        response = client.post('/generate', data=DEFAULT_PARAMS)
        assert response.status_code == 302  # Redirect to index
        assert response.location == 'http://localhost/'  # Default test URL redirects to root
    
    def test_download_without_token(self, client):
        """Test downloading without a valid token"""
        response = client.get('/download/fake_token/nonexistent.png')
        assert response.status_code == 403  # Forbidden status
    
    def test_download_nonexistent_file(self, client):
        """Test download of nonexistent file with valid token"""
        # Create a valid token for a nonexistent file
        with client.session_transaction() as session:
            import time
            session['download_tokens'] = {
                'valid_token': {
                    'filename': 'nonexistent.png',
                    'expires': time.time() + 300  # 5 minutes from now
                }
            }
        
        # Mock file not existing
        with patch('pathlib.Path.exists', return_value=False):
            response = client.get('/download/valid_token/nonexistent.png')
            assert response.status_code == 404  # Not Found
    
    @patch('src.zone_plate_ui.app.zone_plate_generator.delete_file')
    def test_download_with_valid_token(self, mock_delete_file, client):
        """Test that download route with valid token works"""
        mock_delete_file.return_value = True
        
        # Create a valid token in the session
        with client.session_transaction() as session:
            import time
            session['download_tokens'] = {
                'valid_token': {
                    'filename': 'test_file.png',
                    'expires': time.time() + 300  # 5 minutes from now
                }
            }
        
        # Mock the send_file to avoid actual file operations
        with patch('flask.send_file', return_value='mocked_response'), \
             patch('pathlib.Path.exists', return_value=True):
            response = client.get('/download/valid_token/test_file.png')
            # Check that delete_file was called with the correct filename
            mock_delete_file.assert_called_once_with('test_file.png')
            # Token should be removed from session
            with client.session_transaction() as session:
                assert 'valid_token' not in session.get('download_tokens', {})
    
    @patch('src.zone_plate_ui.app.zone_plate_generator.delete_file')
    def test_download_with_expired_token(self, mock_delete_file, client):
        """Test that download route with expired token fails"""
        # Create an expired token in the session
        with client.session_transaction() as session:
            import time
            session['download_tokens'] = {
                'expired_token': {
                    'filename': 'test_file.png',
                    'expires': time.time() - 10  # 10 seconds ago
                }
            }
        
        response = client.get('/download/expired_token/test_file.png')
        assert response.status_code == 403  # Forbidden status code
        # Should not call delete_file for expired tokens
        mock_delete_file.assert_not_called()
        
        # Verify expired token was removed from session
        with client.session_transaction() as session:
            assert 'expired_token' not in session.get('download_tokens', {})
    
    def test_404_page(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        assert b'Page Not Found' in response.data
        
    def test_cleanup_expired_tokens_middleware(self, client):
        """Test that middleware cleans up expired tokens"""
        # Create both valid and expired tokens
        with client.session_transaction() as session:
            import time
            session['download_tokens'] = {
                'valid_token': {
                    'filename': 'valid.png',
                    'expires': time.time() + 300  # 5 minutes from now
                },
                'expired_token1': {
                    'filename': 'expired1.png',
                    'expires': time.time() - 10  # 10 seconds ago
                },
                'expired_token2': {
                    'filename': 'expired2.png',
                    'expires': time.time() - 20  # 20 seconds ago
                }
            }
        
        # Make any request to trigger the middleware
        client.get('/')
        
        # Check session - expired tokens should be removed
        with client.session_transaction() as session:
            tokens = session.get('download_tokens', {})
            assert 'valid_token' in tokens
            assert 'expired_token1' not in tokens
            assert 'expired_token2' not in tokens


if __name__ == '__main__':
    pytest.main([__file__])
