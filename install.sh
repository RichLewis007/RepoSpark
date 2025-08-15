#!/usr/bin/env bash
# RepoSpark Installation Script

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        elif command_exists dnf; then
            echo "fedora"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

print_header "RepoSpark Installation"
echo "This script will install the RepoSpark application and its dependencies."
echo ""

# Detect OS
OS=$(detect_os)
print_status "Detected OS: $OS"

# Check if running as root (not recommended for Python installations)
if [[ $EUID -eq 0 ]]; then
    print_warning "Running as root is not recommended for Python installations"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python installation
print_header "Checking Python Installation"

if ! command_exists python3; then
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8 or higher:"
    case $OS in
        "macos")
            echo "  brew install python3"
            echo "  or download from https://www.python.org/downloads/"
            ;;
        "ubuntu")
            echo "  sudo apt-get update"
            echo "  sudo apt-get install python3 python3-pip"
            ;;
        "centos"|"fedora")
            echo "  sudo yum install python3 python3-pip"
            echo "  or sudo dnf install python3 python3-pip"
            ;;
        *)
            echo "  Please install Python 3.8+ from https://www.python.org/downloads/"
            ;;
    esac
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

# Check pip installation
if ! command_exists pip3; then
    print_error "pip3 is not installed"
    echo "Please install pip3:"
    case $OS in
        "macos")
            echo "  brew install python3"
            ;;
        "ubuntu"|"centos"|"fedora")
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            ;;
        *)
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            ;;
    esac
    echo "uv is recommended for faster dependency management"
    echo "Alternatively, you can use pip3 if uv is not available"
fi

# Check if uv is available, otherwise fall back to pip3
if command_exists uv; then
    print_status "uv is available"
    PACKAGE_MANAGER="uv"
elif command_exists pip3; then
    print_status "pip3 is available (fallback)"
    PACKAGE_MANAGER="pip3"
else
    print_error "Neither uv nor pip3 is available"
    echo "Please install either uv (recommended) or pip3"
    exit 1
fi

# Install Python dependencies
print_header "Installing Python Dependencies"

if [ "$PACKAGE_MANAGER" = "uv" ]; then
    print_status "Using uv for dependency management..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment with uv..."
        uv venv
    fi
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        print_status "Installing dependencies from requirements.txt..."
        uv pip install -r requirements.txt
    else
        print_status "Installing PyQt6..."
        uv pip install PyQt6>=6.4.0
    fi
    
    print_status "Dependencies installed in virtual environment"
    print_status "To activate: source .venv/bin/activate"
else
    print_status "Using pip3 for dependency management..."
    
    if [ -f "requirements.txt" ]; then
        print_status "Installing dependencies from requirements.txt..."
        pip3 install -r requirements.txt
    else
        print_status "Installing PyQt6..."
        pip3 install PyQt6>=6.4.0
    fi
    
    print_status "Python dependencies installed successfully"
fi

# Check system dependencies
print_header "Checking System Dependencies"

# Check Git
if ! command_exists git; then
    print_warning "Git is not installed"
    echo "Please install Git:"
    case $OS in
        "macos")
            echo "  brew install git"
            ;;
        "ubuntu")
            echo "  sudo apt-get install git"
            ;;
        "centos"|"fedora")
            echo "  sudo yum install git"
            echo "  or sudo dnf install git"
            ;;
        *)
            echo "  Download from https://git-scm.com/downloads"
            ;;
    esac
    echo "Git is required for repository operations"
else
    print_status "Git is installed: $(git --version)"
fi

# Check GitHub CLI
if ! command_exists gh; then
    print_warning "GitHub CLI (gh) is not installed"
    echo "Please install GitHub CLI:"
    case $OS in
        "macos")
            echo "  brew install gh"
            ;;
        "ubuntu")
            echo "  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
            echo "  echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null"
            echo "  sudo apt-get update"
            echo "  sudo apt-get install gh"
            ;;
        "centos"|"fedora")
            echo "  sudo yum install gh"
            echo "  or sudo dnf install gh"
            ;;
        *)
            echo "  Download from https://cli.github.com/"
            ;;
    esac
    echo "GitHub CLI is required for repository creation"
else
    print_status "GitHub CLI is installed: $(gh --version | head -n1)"
fi

# Make launcher script executable
if [ -f "run_repospark.sh" ]; then
    chmod +x run_repospark.sh
    print_status "Made launcher script executable"
fi

# Test installation
print_header "Testing Installation"

# Test Python imports
if [ "$PACKAGE_MANAGER" = "uv" ]; then
    # Test with uv virtual environment
    if uv run python3 -c "import PyQt6" 2>/dev/null; then
        print_status "PyQt6 import test passed (uv environment)"
    else
        print_error "PyQt6 import test failed in uv environment"
        exit 1
    fi
    
    # Test GUI creation (without showing window)
    if uv run python3 -c "
import sys
from PyQt6.QtWidgets import QApplication
from src.repospark import RepoSparkGUI
app = QApplication(sys.argv)
gui = RepoSparkGUI()
app.quit()
" 2>/dev/null; then
        print_status "GUI creation test passed (uv environment)"
    else
        print_error "GUI creation test failed in uv environment"
        exit 1
    fi
else
    # Test with system Python
    if python3 -c "import PyQt6" 2>/dev/null; then
        print_status "PyQt6 import test passed"
    else
        print_error "PyQt6 import test failed"
        exit 1
    fi
    
    # Test GUI creation (without showing window)
    if python3 -c "
import sys
from PyQt6.QtWidgets import QApplication
from src.repospark import RepoSparkGUI
app = QApplication(sys.argv)
gui = RepoSparkGUI()
app.quit()
" 2>/dev/null; then
        print_status "GUI creation test passed"
    else
        print_error "GUI creation test failed"
        exit 1
    fi
fi

print_header "Installation Complete!"

echo "🎉 RepoSpark has been successfully installed!"
echo ""
echo "To use the application:"
echo "1. Navigate to your project directory"
if [ "$PACKAGE_MANAGER" = "uv" ]; then
    echo "2. Run: ./run_repospark.sh"
    echo "   or: uv run python3 repospark.py"
    echo "   or: source .venv/bin/activate && python3 repospark.py"
else
    echo "2. Run: ./run_repospark.sh"
    echo "   or: python3 repospark.py"
fi
echo ""
echo "Before creating repositories, make sure to:"
echo "1. Install Git (if not already installed)"
echo "2. Install GitHub CLI (if not already installed)"
echo "3. Authenticate with GitHub: gh auth login"
echo ""
echo "For more information, see README.md"
