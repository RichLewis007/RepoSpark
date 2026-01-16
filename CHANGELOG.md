# Changelog

All notable changes to this project will be documented in this file, in reverse chronological order by release.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

- **Custom Confirmation Dialog**: New confirmation dialog for repository creation
  - Created `confirm_dialog.ui` file for Qt Designer editing
  - Larger dialog size (700x600 pixels) for better readability
  - HTML-formatted repository details display
  - Centered on screen automatically
  - "No" button set as default (Enter key cancels operation)
  - Fallback to QMessageBox if custom dialog fails to load

### Changed

- **Advanced Settings Defaults**: Updated default values for better user experience
  - SSH is now the default remote type (moved to top of list)
  - "Open repository in browser after creation" checkbox defaults to checked
- **Error Handling**: Improved error message display and thread safety
  - All error messages now shown in modal dialogs with clear titles
  - Error dialog title changed to "Repository Creation Failed" for clarity
  - Fixed thread-safety issues with error/success message display
  - Replaced `QMetaObject.invokeMethod` with `QTimer.singleShot` for more reliable thread-safe UI updates

### Fixed

- **Critical**: Fixed "repo_name is not defined" error when opening repository in browser
  - Config is now stored when worker starts instead of being retrieved from UI in worker thread
  - Added `_open_repo_in_browser()` method for thread-safe browser opening
- **Critical**: Fixed `QMetaObject::invokeMethod: No such method` error for error messages
  - Replaced `QMetaObject.invokeMethod` calls with `QTimer.singleShot` for message boxes
  - More reliable thread-safe method invocation

## [0.3.1] - 2025-01-16

### Changed

- **Major Code Refactoring**: Completely restructured codebase following modern Python and PySide6 best practices
  - Split monolithic `app.py` (3168 lines) into logical, maintainable modules
  - Created `core/` module for business logic (GitHub API, Git operations, scaffold generation)
  - Created `workers/` module for background thread operations
  - Created `widgets/` module for custom Qt widgets
  - Created `ui/` module for UI components (main window)
  - Separated application entry point into `main.py`
  - All modules now follow single responsibility principle

### Added

- **Comprehensive File Headers**: All Python files now include detailed headers with:
  - File path and version information
  - Description and purpose
  - Creation date and maintainer information
  - License information
- **Modular Architecture**:
  - `core/github_api.py`: GitHub API operations (145 lines)
  - `core/git_operations.py`: Git repository operations (154 lines)
  - `core/scaffold_generator.py`: Project scaffold generation (196 lines)
  - `workers/repository_worker.py`: Background worker for repository creation (419 lines)
  - `widgets/folder_tree_widget.py`: Custom tree widget for project preview (216 lines)
  - `ui/main_window.py`: Main GUI window class (2309 lines)
  - `main.py`: Application entry point (40 lines)

### Improved

- **Code Organization**: Files are now logically grouped by responsibility
- **Maintainability**: Smaller, focused files are easier to understand and modify
- **Testability**: Modular structure makes unit testing easier
- **Import Structure**: Clean import hierarchy with proper `__init__.py` exports
- **Documentation**: All modules have comprehensive docstrings and file headers

### Technical Details

- Fixed circular import issues by defining `__version__` before imports
- Maintained backward compatibility through `__init__.py` exports
- All imports verified and working correctly
- File naming follows Python conventions (snake_case)
- Module structure follows PySide6 best practices for desktop applications

## [0.3.0] - 2024-12

### Added

- **About Dialog**: Added Help menu with About dialog showing version information
  - Accessible via Help > About RepoSpark... or F1 key
  - Displays version number (0.3.0), author, and application details
  - Includes About Qt dialog for Qt framework information
- **UI File System**: Complete conversion to Qt Designer .ui files for all GUI components
  - All windows and tabs now use .ui files located in `src/repospark/assets/ui/`
  - `ui_loader.py` module with `load_ui()` function for runtime UI loading
  - Support for custom widget registration (e.g., `FolderTreeWidget`)
  - UI files can be edited in Qt Designer for easy customization
- **Logging System**: Comprehensive logging throughout the application
  - Replaced all `print()` statements with proper logging
  - Configurable log levels (debug, info, warning, error)
  - Logging configuration in `main()` function
  - Enhanced debugging capabilities
- **Error Recovery**: Fallback UI system for graceful degradation
  - `_create_fallback_ui()` method creates minimal functional UI when .ui files fail to load
  - User option to continue with fallback interface
  - Essential controls available even in fallback mode
- **Widget Validation**: Batch widget validation helper
  - `_find_widgets()` method for validating multiple widgets at once
  - Comprehensive error messages listing all missing widgets
  - Reduces code duplication in widget initialization
- **Thread Safety**: Explicit thread-safe UI updates
  - `QMetaObject.invokeMethod()` for all UI updates from worker threads
  - `QueuedConnection` for explicit thread safety guarantees
  - Thread-safe message box helpers
- **Input Validation**: Enhanced validation for all user inputs
  - Description validation (160 character limit, invalid character checks)
  - Topics validation (20 topic limit, 35 character per topic, format validation)
  - Comprehensive repository name validation
- **Security Improvements**: Enhanced subprocess security
  - `shlex.quote()` for subprocess command construction
  - Improved input sanitization
- **Unit Tests**: Comprehensive UI loading tests
  - `tests/test_ui_loading.py` with tests for all .ui files
  - Widget discovery and validation tests
  - Error handling tests

### Changed

- Package structure reorganized to follow Python best practices (`src/repospark/` package)
- All imports updated to use proper package structure (`from repospark import ...`)
- **UI Architecture**: Complete refactoring from programmatic UI to .ui file-based system
  - Main window, all tabs, and dialogs now load from .ui files
  - Widget discovery uses `findChild()` with proper validation
  - Signal connections established after UI loading
- **Error Handling**: Standardized error messages
  - User-facing errors use `QMessageBox` dialogs
  - Technical errors use logging system
  - Consistent error handling throughout codebase
- **Thread Management**: Improved worker thread cancellation
  - Graceful shutdown using `_should_stop` flag instead of `terminate()`
  - Timeout-based fallback to `terminate()` only if needed
  - Cancellation checks throughout worker thread operations

### Fixed

- **Critical**: Missing null checks after `findChild()` calls
  - Added `_find_widget()` helper method with validation
  - Added `_find_widgets()` for batch validation
  - Proper error handling for missing widgets
- **Critical**: Unsafe thread termination
  - Implemented graceful shutdown mechanism
  - Added timeout-based fallback
- **Critical**: Import statement inside function (moved `import re` to module level)
- **Critical**: No error handling for UI loading failures
  - Added try/except blocks with user-friendly error dialogs
  - Fallback UI option for recovery
- **Critical**: Resource cleanup issues
  - Added `closeEvent()` method to stop timers and cancel workers
  - Explicit buffer closing in UI loader
- **Critical**: Missing thread cancellation checks
  - Added `_should_stop` checks throughout worker thread
- **Code Quality**: Missing type hints (added throughout)
- **Code Quality**: Missing docstrings (added comprehensive documentation)
- **Code Quality**: Inconsistent error messages (standardized)

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
