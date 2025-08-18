````markdown
# Zone Plate Generator

A modern Python web application for generating Fresnel zone plates, zone sieves, and photon sieves using PostScript and Ghostscript. Features a responsive HTML5/CSS interface with theme support and containerized deployment for Azure Container Apps.

![Zone Plate Generator](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)
![Azure](https://img.shields.io/badge/Azure%20Container%20Apps-Ready-orange.svg)

## Features

- **Modern Web Interface**: Responsive HTML5/CSS design with Bootstrap 5
- **Theme Support**: Multiple color themes (Light, Dark, Ocean Blue, Purple Haze)
- **Zone Plate Types**: Support for Zone Plates, Zone Sieves, Photon Sieves, and Grid layouts
- **Multiple Output Formats**: PNG, TIFF, and PDF generation
- **Real-time Validation**: Client-side form validation with helpful tooltips
- **Containerized**: Docker support with multi-stage builds
- **Azure Ready**: Optimized for Azure Container Apps deployment
- **Poetry Management**: Modern Python dependency management
- **Accessibility**: WCAG compliant with keyboard navigation support

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Ghostscript
- Docker (for containerized deployment)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/DavidPitcher/zone-plate-generator.git
   cd zone-plate-generator
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**:
   ```bash
   poetry run python src/zone_plate_ui/run.py
   ```

5. **Open your browser**:
   Navigate to `http://localhost:8000`

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t zone-plate-generator .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 zone-plate-generator
   ```

### Azure Container Apps Deployment

#### Using PowerShell (Windows)

1. **Run the deployment script**:
   ```powershell
   .\deploy-azure.ps1
   ```

#### Using Bash (Linux/Mac)

1. **Make the deployment script executable**:
   ```bash
   chmod +x deploy-azure.sh
   ```

2. **Run the deployment**:
   ```bash
   ./deploy-azure.sh
   ```

## PostScript Generator

The underlying PostScript engine generates three types of diffractive optical elements:

1. **Zone Plates**: Concentric rings of alternating transparent and opaque zones that focus light
2. **Zone Sieves**: Similar to zone plates but with rings formed by discrete holes
3. **Photon Sieves**: A variant with holes in the transparent zones

## Web Interface Features

### Parameters

The web interface supports the following parameters:

#### Basic Parameters
- **Focal Length** (mm): The focal length of the zone plate (1-10000)
- **Number of Rings**: Number of opaque rings to generate (1-50)
- **Wavelength** (mm): Wavelength of light (0.00022 for green, 0.00056 for daylight)
- **Zone Plate Type**: GRID (all types), PLATE (zone plate), SIEVE (zone sieve), PHOTON (photon sieve)

#### Physical Parameters
- **Punch Diameter** (mm): Diameter of the punch outline to cut the zone plate
- **Magnification**: Magnification factor for the printed zone plate
- **Padding** (mm): Padding around the zone plate
- **Output Format**: PNG, TIFF, or PDF

#### Advanced Parameters
- **Sieve Scale Factor**: Scale factor for sieve holes on a ring
- **Sieve Spacing** (mm): Space between sieve holes
- **Camera Focal Length** (mm): Duplicating camera focal length
- **Negative Mode**: Invert colors for negative film processing

### Quick Presets

The interface includes preset configurations for common use cases:

- **Photography**: Standard settings for photographic applications
- **Solar Observation**: Optimized for solar photography
- **Microscopy**: Settings for microscopy applications

### Output Formats

- **PNG**: Best for digital viewing and web display
- **TIFF**: High quality for printing and professional use
- **PDF**: Vector format, infinitely scalable

## Development

### Setting Up Development Environment

1. **Install Poetry**:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. **Setup development environment**:
   ```bash
   python dev.py setup
   ```

3. **Run the application**:
   ```bash
   python dev.py run
   ```

4. **Run tests**:
   ```bash
   python dev.py test
   ```

### Available Commands

- `python dev.py setup` - Setup development environment
- `python dev.py run` - Run the Flask application
- `python dev.py test` - Run test suite
- `python dev.py format` - Format code with Black
- `python dev.py lint` - Lint code with flake8
- `python dev.py typecheck` - Type check with mypy
- `python dev.py check` - Run all quality checks
- `python dev.py docker-build` - Build Docker image
- `python dev.py docker-run` - Run Docker container
- `python dev.py clean` - Clean up generated files

## Original PostScript Parameters

The underlying PostScript generator has these configurable parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| FOCAL | 210 | Focal length in millimeters |
| RINGS | 7 | Number of zones (total rings will be RINGS × 2) |
| PUNCH_DIAMETER | 20 | Diameter of the punch outline in mm to cut out the zone plate |
| MAG | 1 | Magnification factor for the printed zone plate |
| WAVE_LENGTH | 0.00056 | Design wavelength in mm (0.00056 = daylight, 0.00022 = green light) |
| SIEVE_SCALE | 1.5 | Scale factor for the sieve holes on a ring |
| SIEVE_SPACE | 0.04 | Space between sieve holes in mm |
| TYPE | PLATE | Type of zone plate to generate (valid values: GRID, PLATE, SIEVE, PHOTON) |
| DUP_FOCAL | 180 | Duplicating camera focal length in millimeters |

## Optical Principles

Zone plates work by diffraction and interference. The radius of each zone follows the formula:

```
r_n = sqrt(n * λ * f + (n² * λ²) / 4) * MAG
```

Where:
- r_n = radius of zone n
- n = zone number
- λ = wavelength of light
- f = focal length
- MAG = magnification factor

The effective f-stop is calculated based on the diameter and focal length.

## Architecture

### Project Structure

```
zone-plate-generator/
├── src/
│   └── zone_plate_ui/
│       ├── __init__.py         # Application factory
│       ├── run.py              # Entry point for running the app
│       ├── config/             # Configuration module
│       │   ├── __init__.py
│       │   └── config.py       # Configuration classes
│       ├── models/             # Business logic
│       │   ├── __init__.py
│       │   └── zone_plate.py   # Zone plate generator model
│       ├── controllers/        # Route handlers
│       │   ├── __init__.py
│       │   ├── main.py         # Main routes
│       │   └── errors.py       # Error handlers
│       ├── templates/          # Jinja2 templates
│       │   ├── base.html       # Base template with theming
│       │   ├── index.html      # Main interface
│       │   └── error.html      # Error pages
│       └── static/             # Static web assets
│           └── css/
│               └── style.css   # Pure CSS styles and themes
├── postscript/
│   └── zone_plate_gen.ps       # Original PostScript generator
├── output/                     # Generated files (created at runtime)
├── Dockerfile                  # Multi-stage Docker build
├── pyproject.toml              # Poetry configuration
├── azure-container-app.yaml    # Azure Container Apps config
├── deploy-azure.sh             # Linux/Mac deployment script
├── deploy-azure.ps1            # Windows deployment script
└── README.md
```

### Technology Stack

- **Backend**: Python 3.11, Flask 3.0
- **Frontend**: HTML5, CSS3 (Pure CSS implementation, no JavaScript)
- **Image Processing**: Ghostscript
- **Dependency Management**: Poetry
- **Containerization**: Docker with multi-stage builds
- **Deployment**: Azure Container Apps
- **Security**: CSP headers, input validation, secure file handling

### Application Structure

The application follows the MVC (Model-View-Controller) pattern and uses the Flask factory pattern:

- **Models**: Business logic and data handling in `models/zone_plate.py`
- **Views**: HTML templates in `templates/` directory
- **Controllers**: Route handlers in `controllers/main.py` and `controllers/errors.py`
- **Configuration**: Configuration classes in `config/config.py`
- **Application Factory**: Flask application factory in `__init__.py`
- **Entry Point**: Application entry point in `run.py`

## Tips for Best Results

- Use high-resolution film printing (3600 DPI or higher)
- Print on clear, stable transparent film
- For photography: use with a camera body cap with a hole, or mount to the front of a lens
- For testing: use a laser pointer or bright point light source to observe focusing
- Experiment with different focal lengths to find the best for your needs
- When duplicating, use the camera positioning information for precise results

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and add tests
4. Run the test suite: `python dev.py test`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original PostScript zone plate generator by David Pitcher
- PostScript concepts inspired by the work of Guillermo Peñate
- Bootstrap team for the UI framework
- Ghostscript developers for image processing capabilities
- Flask community for the web framework

For additional details and background on zone plates and sieves, see:
- [Zone Plate and Sieves by Guillermo Peñate](https://pinholeday.org/docs/Zone_Plate_and_Sieves/)
````
