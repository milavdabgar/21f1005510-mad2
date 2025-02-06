#!/bin/bash

# Exit on error
set -e

echo "Setting up development environment..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    echo "You seem to be running this script on Windows."
    echo "Please use setup_dev.bat instead of this script."
    echo "Run: setup_dev.bat"
    exit 1
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

echo "Detected OS: $OS"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed."
    if [[ "$OS" == "macOS" ]]; then
        echo "Please install Python using Homebrew:"
        echo "brew install python3"
    else
        echo "Please install Python using your package manager:"
        echo "sudo apt-get update"
        echo "sudo apt-get install -y python3 python3-venv"
    fi
    exit 1
fi

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install development requirements
echo "Installing development requirements..."
pip install -r requirements.txt

# Install pre-commit hooks if .pre-commit-config.yaml exists
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks..."
    pip install pre-commit
    pre-commit install
fi

echo "Development environment setup complete!"
echo "To activate the virtual environment in the future, run:"
if [[ "$OS" == "macOS" ]] || [[ "$OS" == "Linux" ]]; then
    echo "source .venv/bin/activate"
fi
