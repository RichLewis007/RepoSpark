"""
README.md template system for RepoSpark
Generates professional README files with smart defaults based on project type
"""

from typing import Dict, Any, Optional, List
from .project_types import ProjectType


class READMETemplate:
    """Generates professional README.md content based on project configuration"""
    
    def __init__(self, project_config: Dict[str, Any]):
        self.config = project_config
        self.project_type = project_config.get('project_type')
        self.repo_name = project_config.get('repo_name', 'project-name')
        self.description = project_config.get('description', '')
        self.author = project_config.get('author', '')
        self.license = project_config.get('license', 'MIT')
        self.topics = project_config.get('topics', [])
        self.username = project_config.get('username', 'username')
        
    def generate(self) -> str:
        """Generate complete README.md content"""
        sections = [
            self._generate_header(),
            self._generate_description(),
            self._generate_features(),
            self._generate_installation(),
            self._generate_usage(),
            self._generate_api_documentation(),
            self._generate_contributing(),
            self._generate_license(),
            self._generate_support(),
            self._generate_changelog_link()
        ]
        
        # Filter out empty sections
        sections = [section for section in sections if section.strip()]
        
        return '\n\n'.join(sections)
    
    def _generate_header(self) -> str:
        """Generate project header with badges"""
        header_lines = [
            f"# {self.repo_name}",
            ""
        ]
        
        # Add description if provided
        if self.description:
            header_lines.extend([
                self.description,
                ""
            ])
        
        # Add badges
        if self.project_type:
            badges = self._get_badges()
            if badges:
                header_lines.extend([
                    " ".join(badges),
                    ""
                ])
        
        # Add quick links
        quick_links = self._generate_quick_links()
        if quick_links:
            header_lines.extend([
                quick_links,
                ""
            ])
        
        return '\n'.join(header_lines)
    
    def _get_badges(self) -> List[str]:
        """Get badges for the project type"""
        if not self.project_type:
            return []
        
        badges = self.project_type.badges.copy()
        
        # Replace placeholders with actual values
        for i, badge in enumerate(badges):
            badge = badge.replace('{package_name}', self.repo_name)
            badge = badge.replace('{username}', self.username)
            badge = badge.replace('{repo_name}', self.repo_name)
            badge = badge.replace('{license}', self.license.upper())
            badges[i] = badge
        
        return badges
    
    def _generate_quick_links(self) -> str:
        """Generate quick links section"""
        links = [
            f"[📖 Documentation](https://github.com/{self.username}/{self.repo_name}#readme)",
            f"[🐛 Report Bug](https://github.com/{self.username}/{self.repo_name}/issues)",
            f"[💡 Request Feature](https://github.com/{self.username}/{self.repo_name}/issues)",
            f"[📝 Changelog](https://github.com/{self.username}/{self.repo_name}/blob/main/CHANGELOG.md)"
        ]
        
        return " | ".join(links)
    
    def _generate_description(self) -> str:
        """Generate project description section"""
        if not self.description:
            return ""
        
        return f"""## 📖 About

{self.description}

This project aims to provide a solution for [brief description of what it solves]."""
    
    def _generate_features(self) -> str:
        """Generate features section"""
        if not self.project_type:
            return ""
        
        features = self._get_default_features()
        
        if not features:
            return ""
        
        feature_lines = ["## ✨ Features", ""]
        
        for feature in features:
            feature_lines.append(f"- {feature}")
        
        return '\n'.join(feature_lines)
    
    def _get_default_features(self) -> List[str]:
        """Get default features based on project type"""
        if not self.project_type:
            return []
        
        feature_map = {
            "python-library": [
                "Easy to use and well-documented API",
                "Comprehensive test coverage",
                "Type hints for better IDE support",
                "Cross-platform compatibility"
            ],
            "python-cli": [
                "Simple and intuitive command-line interface",
                "Comprehensive help and documentation",
                "Configurable options and settings",
                "Cross-platform compatibility"
            ],
            "javascript-package": [
                "Modern ES6+ JavaScript",
                "Comprehensive test coverage",
                "TypeScript support",
                "Tree-shaking friendly"
            ],
            "web-application": [
                "Modern web technologies",
                "Responsive design",
                "Fast and optimized performance",
                "Easy deployment options"
            ],
            "data-science": [
                "Jupyter notebook support",
                "Comprehensive data analysis tools",
                "Machine learning capabilities",
                "Visualization and reporting"
            ],
            "documentation": [
                "Clean and professional design",
                "Search functionality",
                "Mobile-responsive layout",
                "Easy to maintain and update"
            ]
        }
        
        return feature_map.get(self.project_type.id, [])
    
    def _generate_installation(self) -> str:
        """Generate installation section"""
        if not self.project_type:
            return ""
        
        install_cmd = self.project_type.installation_cmd.replace('{package_name}', self.repo_name)
        
        return f"""## 🚀 Installation

### Prerequisites

- {self.project_type.language} {self._get_language_version()}
- {self.project_type.package_manager}

### Install

```bash
{install_cmd}
```

### Development Setup

```bash
# Clone the repository
git clone https://github.com/{self.username}/{self.repo_name}.git
cd {self.repo_name}

# Install development dependencies
{self._get_dev_install_cmd()}

# Run tests
{self._get_test_cmd()}
```"""
    
    def _get_language_version(self) -> str:
        """Get language version requirement"""
        version_map = {
            "Python": "3.8+",
            "JavaScript": "16+",
            "JavaScript/Python": "Python 3.8+ / Node.js 16+",
            "Markdown/HTML": "Any"
        }
        return version_map.get(self.project_type.language, "Latest")
    
    def _get_dev_install_cmd(self) -> str:
        """Get development installation command"""
        if self.project_type.package_manager == "pip":
            return "pip install -e .[dev]"
        elif self.project_type.package_manager == "npm":
            return "npm install"
        else:
            return "pip install -r requirements-dev.txt"
    
    def _get_test_cmd(self) -> str:
        """Get test command"""
        if self.project_type.test_framework == "pytest":
            return "pytest"
        elif self.project_type.test_framework == "jest":
            return "npm test"
        else:
            return "python -m pytest"
    
    def _generate_usage(self) -> str:
        """Generate usage section"""
        if not self.project_type:
            return ""
        
        usage_example = self.project_type.usage_example.replace('{package_name}', self.repo_name)
        
        return f"""## 📖 Usage

{usage_example}

### Configuration

```python
# Example configuration
config = {{
    'setting1': 'value1',
    'setting2': 'value2'
}}
```

### Examples

See the [examples/](examples/) directory for more detailed usage examples."""
    
    def _generate_api_documentation(self) -> str:
        """Generate API documentation section"""
        if not self.project_type or self.project_type.id in ["web-application", "documentation"]:
            return ""
        
        return f"""## 🔧 API Reference

### Main Functions

#### `main_function()`

The main function that does the primary work.

**Parameters:**
- `param1` (str): Description of parameter 1
- `param2` (int): Description of parameter 2

**Returns:**
- `result` (Any): Description of return value

**Example:**
```python
from {self.repo_name} import main_function

result = main_function("example", 42)
print(result)
```

### Classes

#### `MainClass`

The main class for advanced usage.

**Methods:**
- `method1()`: Description of method 1
- `method2(param)`: Description of method 2

For complete API documentation, see the [docs/](docs/) directory."""
    
    def _generate_contributing(self) -> str:
        """Generate contributing section"""
        return f"""## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `{self._get_test_cmd()}`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

We use {', '.join(self.project_type.linting_tools) if self.project_type else 'standard'} for code formatting and linting.

### Testing

Please ensure all tests pass before submitting a pull request."""
    
    def _generate_license(self) -> str:
        """Generate license section"""
        license_text = self.license.upper() if self.license else "MIT"
        
        return f"""## 📄 License

This project is licensed under the {license_text} License - see the [LICENSE](LICENSE) file for details.

Copyright (c) {self._get_current_year()} {self.author or self.username}"""
    
    def _get_current_year(self) -> int:
        """Get current year"""
        from datetime import datetime
        return datetime.now().year
    
    def _generate_support(self) -> str:
        """Generate support section"""
        return f"""## 💬 Support

### Getting Help

- 📖 [Documentation](https://github.com/{self.username}/{self.repo_name}#readme)
- 🐛 [Bug Reports](https://github.com/{self.username}/{self.repo_name}/issues)
- 💡 [Feature Requests](https://github.com/{self.username}/{self.repo_name}/issues)
- 📧 [Email Support](mailto:{self.username}@example.com)

### Community

- 💬 [Discussions](https://github.com/{self.username}/{self.repo_name}/discussions)
- 📢 [Releases](https://github.com/{self.username}/{self.repo_name}/releases)

If you find this project helpful, please consider giving it a ⭐️ star on GitHub!"""
    
    def _generate_changelog_link(self) -> str:
        """Generate changelog link"""
        return f"""## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history."""
