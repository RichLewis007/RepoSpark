#!/usr/bin/env bash
# RepoSpark Launcher Script
# Author: Rich Lewis - GitHub: @RichLewis007

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

print_status "Python version: $python_version"

# Check if uv is available
if command -v uv &> /dev/null; then
    print_status "Using uv for Python environment management"
    USE_UV=true
elif command -v pip3 &> /dev/null; then
    print_status "Using pip3 (fallback)"
    USE_UV=false
else
    print_error "Neither uv nor pip3 is available. Please install uv (recommended) or pip3."
    exit 1
fi

# Check if PySide6 is installed
if [ "$USE_UV" = true ]; then
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one with uv..."
        uv venv
    fi
    
    # Check if PySide6 is installed in uv environment
    if ! uv run python3 -c "import PySide6" &> /dev/null; then
        print_warning "PySide6 is not installed. Installing dependencies..."
        
        # Install dependencies
        if [ -f "pyproject.toml" ]; then
            uv sync
        elif [ -f "requirements.txt" ]; then
            uv pip install -r requirements.txt
        else
            uv pip install PySide6>=6.4.0
        fi
        
        print_status "Dependencies installed successfully in virtual environment"
    fi
else
    # Check if PySide6 is installed in system Python
    if ! python3 -c "import PySide6" &> /dev/null; then
        print_warning "PySide6 is not installed. Installing dependencies..."
        
        # Install dependencies
        if [ -f "requirements.txt" ]; then
            pip3 install -r requirements.txt
        else
            pip3 install PySide6>=6.4.0
        fi
        
        print_status "Dependencies installed successfully"
    fi
fi

# Check if repospark.py exists
if [ ! -f "src/repospark.py" ]; then
    print_error "repospark.py not found in src directory"
    exit 1
fi

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    print_warning "GitHub CLI (gh) is not installed"
    print_warning "Please install it from: https://cli.github.com/"
    print_warning "The application will still work but repository creation will fail"
fi

# Check if git is available
if ! command -v git &> /dev/null; then
    print_warning "Git is not installed"
    print_warning "Please install Git to use this application"
    print_warning "The application will still work but repository creation will fail"
fi

print_status "Starting RepoSpark..."
print_status "Current directory: $(pwd)"

# Run the application
if [ "$USE_UV" = true ]; then
    print_status "Running with uv virtual environment..."
    uv run python3 -m src.repospark
else
    print_status "Running with system Python..."
    python3 -m src.repospark
fi
