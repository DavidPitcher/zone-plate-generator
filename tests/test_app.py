import pytest
import tempfile
import os
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
    
    yield ZonePlateGenerator(ps_file)
    
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


class TestFlaskApp:
    """Test the Flask application"""
    
    def test_index_page(self, client):
        """Test the main index page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Zone Plate Generator' in response.data
        assert b'Generate Zone Plate' in response.data
    
    def test_health_endpoint(self, client):
        """Test the health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
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
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'download_url' in data
    
    @patch('src.zone_plate_ui.app.generator.validate_parameters')
    def test_generate_validation_error(self, mock_validate, client):
        """Test generation with validation errors"""
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
        assert response.status_code == 500
        data = response.get_json()
        assert data['success'] == False
    
    def test_download_nonexistent_file(self, client):
        """Test downloading non-existent file"""
        response = client.get('/download/nonexistent.png')
        assert response.status_code == 302  # Redirect to index
    
    def test_404_page(self, client):
        """Test 404 error page"""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        assert b'Page Not Found' in response.data


if __name__ == '__main__':
    pytest.main([__file__])
