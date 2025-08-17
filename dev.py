#!/usr/bin/env python3
"""
Development script for Zone Plate Generator

This script provides common development tasks.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"


def run_command(cmd, **kwargs):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def install_deps():
    """Install dependencies with Poetry"""
    print("Installing dependencies...")
    run_command(["poetry", "install"])


def run_app():
    """Run the Flask application in development mode"""
    print("Starting Flask application...")
    env = os.environ.copy()
    env["FLASK_ENV"] = "development"
    env["DEBUG"] = "true"
    run_command(["poetry", "run", "python", "src/zone_plate_ui/app.py"], env=env)


def run_tests():
    """Run the test suite"""
    print("Running tests...")
    run_command(["poetry", "run", "pytest", "tests/", "-v"])


def format_code():
    """Format code with Black"""
    print("Formatting code...")
    run_command(["poetry", "run", "black", "src/", "tests/"])


def lint_code():
    """Lint code with flake8"""
    print("Linting code...")
    run_command(["poetry", "run", "flake8", "src/", "tests/"])


def type_check():
    """Type check with mypy"""
    print("Type checking...")
    run_command(["poetry", "run", "mypy", "src/"])


def check_all():
    """Run all quality checks"""
    print("Running all quality checks...")
    format_code()
    lint_code()
    type_check()
    run_tests()


def build_docker():
    """Build Docker image"""
    print("Building Docker image...")
    run_command(["docker", "build", "-t", "zone-plate-generator", "."])


def run_docker():
    """Run Docker container"""
    print("Running Docker container...")
    run_command([
        "docker", "run", "-p", "8000:8000", 
        "--rm", "--name", "zone-plate-dev",
        "zone-plate-generator"
    ])


def clean():
    """Clean up generated files"""
    print("Cleaning up...")
    import shutil
    
    # Remove Python cache
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for dir_name in dirs[:]:
            if dir_name == "__pycache__":
                shutil.rmtree(Path(root) / dir_name)
                dirs.remove(dir_name)
    
    # Remove output files
    output_dir = PROJECT_ROOT / "output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    # Remove test artifacts
    for pattern in ["*.pyc", "*.pyo", ".coverage", ".pytest_cache"]:
        for file_path in PROJECT_ROOT.rglob(pattern):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
    
    print("Cleanup complete")


def setup_dev():
    """Set up development environment"""
    print("Setting up development environment...")
    
    # Check if Poetry is installed
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Poetry not found. Please install Poetry first:")
        print("curl -sSL https://install.python-poetry.org | python3 -")
        sys.exit(1)
    
    # Install dependencies
    install_deps()
    
    # Create output directory
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(exist_ok=True)
    
    # Copy environment file
    env_file = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        import shutil
        shutil.copy2(env_example, env_file)
        print("Created .env file from .env.example")
    
    print("Development environment setup complete!")
    print("\nNext steps:")
    print("1. Edit .env file if needed")
    print("2. Run: python dev.py run")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Development script for Zone Plate Generator")
    parser.add_argument("command", choices=[
        "setup", "install", "run", "test", "format", "lint", "typecheck", 
        "check", "docker-build", "docker-run", "clean"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    commands = {
        "setup": setup_dev,
        "install": install_deps,
        "run": run_app,
        "test": run_tests,
        "format": format_code,
        "lint": lint_code,
        "typecheck": type_check,
        "check": check_all,
        "docker-build": build_docker,
        "docker-run": run_docker,
        "clean": clean
    }
    
    command_func = commands.get(args.command)
    if command_func:
        command_func()
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
