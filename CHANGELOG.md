# Changelog

All notable changes to this project will be documented in this file, in reverse chronological order by release.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

### Changed

- Package structure reorganized to follow Python best practices (`src/repospark/` package)
- All imports updated to use proper package structure (`from repospark import ...`)

## [0.2.0] - 2024-12

### Added

- Proper Python package structure with `src/repospark/` directory
- Package `__init__.py` with proper exports and version information
- Support for running via entry point: `uv run repospark` or `python -m repospark`
- Author attribution in all source files

### Changed

- **BREAKING**: Updated Python requirement to 3.13.11+ (from 3.8+)
- **BREAKING**: Pinned PySide6 to version 6.7.3 (from >= 6.4.0)
- **BREAKING**: Migrated from PyQt6 to PySide6 for better licensing and official Qt support
  - All imports changed from `PyQt6` to `PySide6`
  - Signal declarations changed from `pyqtSignal` to `Signal`
  - Updated all test files and documentation
- **BREAKING**: Removed `install.sh` script in favor of `uv sync` workflow
  - Simplified installation process using only `uv`
  - Updated all documentation to reflect uv-only workflow
- Reorganized source code structure:
  - `src/repospark.py` → `src/repospark/app.py`
  - `src/demo.py` → `src/repospark/demo.py`
- Updated entry point in `pyproject.toml` to use proper package structure
- Updated all import statements throughout codebase
- Updated `run_repospark.sh` to check for new package structure and enforce Python 3.13.11+

### Fixed

- Import paths updated to work with new package structure

## [0.1.0] - 2024-11

### Added

- Initial release of RepoSpark GUI application
- Modern PySide6-based graphical user interface
- Tabbed interface with four main sections:
  - **Project Basics Tab**: Repository configuration
    - Repository name (auto-filled from current directory)
    - Description input
    - Visibility selection (Public/Private)
    - Gitignore template selection with preview
    - License selection (MIT, Apache 2.0, GPL 3.0, None)
    - Topics/tags input
    - Project type selection with radio buttons
    - Contextual help pane
  - **README.md Tab**: README generation and preview
    - Project type-based README templates
    - Live markdown preview with GitHub-flavored rendering
    - Customizable project configuration
    - Template selection for different project types
  - **Advanced Settings Tab**: Additional options
    - Remote type selection (HTTPS/SSH)
    - Browser opening options
  - **Project Scaffold Tab**: Project structure generation
    - Scaffold creation toggle
    - EditorConfig generation option
    - Visual preview of directory structure
    - Customizable project structure
- Core functionality classes:
  - `GitHubAPI`: Handles all GitHub API operations via GitHub CLI
  - `GitOperations`: Manages Git repository initialization and remote setup
  - `ScaffoldGenerator`: Creates project directory structure and files
  - `RepoSparkGUI`: Main application window and UI logic
- Background processing with `QThread` for non-blocking operations
- Real-time progress indication with progress bar
- Comprehensive error handling and user feedback
- Input validation before repository creation
- Dependency checking (Git, GitHub CLI)
- Authentication validation
- Demo mode with pre-filled sample data
- Template system for README generation:
  - Support for multiple project types (Python, JavaScript, Go, Rust, etc.)
  - Customizable README templates
  - Project type definitions with specific configurations
- Project scaffold generation:
  - Standard directory structure (src/, tests/, docs/)
  - GitHub templates (.github/ISSUE_TEMPLATE.md, PULL_REQUEST_TEMPLATE.md)
  - Standard files (README.md, CHANGELOG.md, CONTRIBUTING.md, etc.)
  - .gitattributes and .editorconfig support
- Gitignore template support:
  - Integration with GitHub's gitignore templates API
  - Custom templates for common languages
  - Preview functionality for gitignore content
- License file generation support
- Topics/tags management for repositories
- Remote repository setup (HTTPS/SSH)
- Browser integration to open created repositories
- Test suite with multiple test files:
  - `test_repospark.py`: Core functionality tests
  - `test_radio_buttons.py`: UI component tests
  - `test_markdown_preview.py`: Markdown rendering tests
  - `test_templates.py`: Template system tests
- Development tools:
  - `run_repospark.sh`: Launcher script
  - `qt-designer.sh`: Qt Designer launcher for UI development
  - Demo script for showcasing features
- Documentation:
  - Comprehensive README with installation and usage instructions
  - Feature documentation
  - Troubleshooting guide
- Project configuration:
  - `pyproject.toml` with proper metadata and dependencies
  - Development dependencies (pytest, pytest-qt, ruff, pyright)
  - Entry point configuration
  - Build system configuration

### Changed

- Converted from original bash script to modern GUI application
- Improved user experience with visual interface vs command-line prompts
- Enhanced error messages and validation feedback

### Technical Details

- Built with PySide6 (Qt6) for cross-platform GUI
- Uses GitHub CLI (gh) for all GitHub API operations
- Markdown rendering with GitHub-flavored markdown support
- Thread-safe UI updates using Qt signals and slots
- Modular architecture with separated concerns
- Type hints throughout codebase for better maintainability
