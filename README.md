# ⚡ RepoSpark

A Python GUI for creating the most comprehensive scaffold for new GitHub repositories.

## Features

- **Modern Interface**: Clean, intuitive PySide6-based interface with tabbed organization
- **All Original Functionality**: Complete feature parity with the original bash script
- **Smart Defaults**: Automatically suggests repository name from current directory
- **Real-time Validation**: Validates inputs and dependencies before proceeding
- **Progress Tracking**: Visual progress indication during repository creation
- **Background Processing**: Non-blocking UI during repository operations
- **Error Handling**: Comprehensive error messages and recovery options

## Requirements

### System Requirements

- Python 3.13.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git installed and configured
- GitHub CLI (gh) installed and authenticated

### Python Dependencies

- PySide6 == 6.7.3

## Installation

1. **Ensure prerequisites are installed:**

   - uv, Git, and GitHub CLI (gh) must be installed on your system

2. **Install dependencies and the package:**

   ```bash
   uv sync
   uv pip install -e .
   ```

   Note: The `-e` flag installs the package in editable mode so it can be imported.

3. **Authenticate with GitHub:**
   ```bash
   gh auth login
   ```

## Usage

1. **Navigate to your project directory:**

   ```bash
   cd /path/to/your/project
   ```

2. **Run the application:**

   ```bash
   # Recommended: Use the launcher script
   ./run_repospark.sh

   # Or run directly with uv (add src to PYTHONPATH)
   PYTHONPATH=src uv run python -m repospark
   ```

3. **Configure your repository:**

   - **Basic Settings Tab**: Set repository name, description, visibility, gitignore template, license, and topics
   - **Advanced Settings Tab**: Choose remote type (HTTPS/SSH) and browser options
   - **Project Scaffold Tab**: Configure project structure generation

4. **Create Repository**: Click "Create Repository" to start the process

## Features

### Basic Settings Tab

- **Repository Name**: Auto-filled with current directory name
- **Description**: Optional repository description
- **Visibility**: Choose between Public and Private
- **Gitignore Template**: Select from available GitHub templates
- **License**: Choose from MIT, Apache 2.0, GPL 3.0, or None
- **Topics**: Comma-separated list of repository topics

### Advanced Settings Tab

- **Remote Type**: Choose between HTTPS (default) and SSH
- **Browser Options**: Option to open repository in browser after creation

### Project Scaffold Tab

- **Create Scaffold**: Generate standard project structure
- **EditorConfig**: Create .editorconfig file for consistent coding style
- **Scaffold Preview**: Shows what files and directories will be created

## Customizing the UI

The application uses Qt Designer `.ui` files for the interface, which means you can customize the appearance and layout using Qt Designer:

1. **Locate UI files**: All `.ui` files are in `src/repospark/assets/ui/`

   - `main_window.ui` - Main window layout
   - `basic_tab.ui` - Project Basics tab
   - `readme_tab.ui` - README.md tab
   - `advanced_tab.ui` - Advanced Settings tab
   - `scaffold_tab.ui` - Project Scaffold tab

2. **Edit with Qt Designer**:

   ```bash
   # Use the provided script to launch Qt Designer
   ./qt-designer.sh
   ```

   Or manually:

   ```bash
   uv run designer
   ```

3. **Important**: When editing `.ui` files:
   - Keep widget object names (objectName) unchanged - the code uses these to find widgets
   - Don't remove required widgets - the application expects all widgets to be present
   - Test after making changes to ensure the application still loads correctly

## Generated Project Structure

When scaffold is enabled, the following structure is created:

```
project/
├── src/                    # Source code directory
├── tests/                  # Test files directory
├── docs/                   # Documentation directory
│   └── index.md           # Main documentation
├── .github/               # GitHub templates
│   ├── ISSUE_TEMPLATE.md  # Issue template
│   └── PULL_REQUEST_TEMPLATE.md  # PR template
├── README.md              # Project readme
├── CHANGELOG.md           # Change log
├── CONTRIBUTING.md        # Contribution guidelines
├── CODE_OF_CONDUCT.md     # Code of conduct
├── SECURITY.md            # Security policy
├── .gitattributes         # Git attributes
└── .editorconfig          # Editor configuration (optional)
```

## Error Handling

The application provides comprehensive error handling:

- **Dependency Validation**: Checks for Git and GitHub CLI availability
- **Authentication Validation**: Verifies GitHub CLI authentication
- **Input Validation**: Validates required fields and format
- **Operation Feedback**: Real-time progress updates and error messages
- **Recovery Options**: Ability to cancel operations and retry

## Comparison with Original Script

| Feature               | Bash Script          | Application         |
| --------------------- | -------------------- | ------------------- |
| Repository Creation   | ✅                   | ✅                  |
| Visibility Selection  | ✅                   | ✅                  |
| Gitignore Templates   | ✅                   | ✅                  |
| License Selection     | ✅                   | ✅                  |
| Topics Setting        | ✅                   | ✅                  |
| Remote Type Selection | ✅                   | ✅                  |
| Project Scaffold      | ✅                   | ✅                  |
| Progress Indication   | Text-based           | Visual progress bar |
| Error Handling        | Basic                | Comprehensive       |
| User Interface        | Command-line prompts | Modern UI           |
| Background Processing | No                   | Yes                 |
| Validation            | Basic                | Real-time           |

## Troubleshooting

### Common Issues

1. **"GitHub CLI is not authenticated"**

   - Run `gh auth login` in terminal
   - Follow the authentication prompts

2. **"Git is not installed" or "uv is not installed"**

   - Ensure Git and uv are installed and available in your PATH

3. **"PySide6 not found"**

   - Run `uv sync` to install dependencies
   - Ensure you're using Python 3.13.11+

4. **Repository creation fails**
   - Check your internet connection
   - Verify GitHub CLI authentication
   - Ensure repository name is unique

### Using uv Scripts

If you're using uv, you can also use the predefined scripts:

```bash
# Run the demo
uv run demo

# Run tests
uv run test

# Run the main application
uv run repospark
```

### Debug Mode

For troubleshooting, you can run the application with debug output:

```bash
python -u repospark.py 2>&1 | tee repospark.log
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT license.

## Acknowledgments

- PySide6 team for the excellent GUI framework
- GitHub CLI team for the powerful command-line interface
