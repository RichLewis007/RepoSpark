"""
RepoSpark - Scaffold Generator Service
File: src/repospark/core/scaffold_generator.py
Version: 0.3.0
Description: Generates project scaffold files and directory structure.
Created: 2025-01-16
Maintainer: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

# Author: Rich Lewis - GitHub: @RichLewis007

import os
import logging
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


class ScaffoldGenerator:
    """
    Generates project scaffold files and directory structure.
    
    This class creates standard project files and directories that are
    commonly found in professional open source repositories.
    """
    
    @staticmethod
    def create_scaffold(repo_name: str, create_editorconfig: bool = True, readme_content: Optional[str] = None) -> None:
        """
        Create standard project scaffold.
        
        Args:
            repo_name: Name of the repository
            create_editorconfig: Whether to create .editorconfig file
            readme_content: Custom README content (optional)
        """
        # Create directories
        os.makedirs('src', exist_ok=True)
        os.makedirs('tests', exist_ok=True)
        os.makedirs('docs', exist_ok=True)
        os.makedirs('.github', exist_ok=True)
        
        # README.md
        if readme_content:
            with open('README.md', 'w', encoding='utf-8') as f:
                f.write(readme_content)
        else:
            with open('README.md', 'w', encoding='utf-8') as f:
                f.write(f"# {repo_name}\n\nProject initialized using RepoSpark.\n")
        
        # docs/index.md
        with open('docs/index.md', 'w', encoding='utf-8') as f:
            f.write("# Documentation\n\nProject documentation goes here.\n")
        
        # tests/test_placeholder.txt
        with open('tests/test_placeholder.txt', 'w', encoding='utf-8') as f:
            f.write("# Placeholder for tests\n")
        
        # CHANGELOG.md
        changelog_content = """# Changelog

All notable changes to this project will be documented in this file, in reverse chronological order by release.

The format is based on [Keep a Changelog](https://keepachangelog.com),
and this project adheres to [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

## [1.0.0] - YYYY-MM-DD

### Added

### Changed

### Deprecated

### Removed

### Fixed
"""
        with open('CHANGELOG.md', 'w', encoding='utf-8') as f:
            f.write(changelog_content)
        
        # CONTRIBUTING.md
        contributing_content = f"""# Contributing

Thank you for considering contributing to this project!

## How to Contribute
- Fork this repository
- Create a new branch
- Make your changes
- Submit a pull request

Please follow the coding conventions and include tests if applicable.

Coding conventions for this project are located in [STYLEGUIDE.md](docs/STYLEGUIDE.md)
"""
        with open('CONTRIBUTING.md', 'w', encoding='utf-8') as f:
            f.write(contributing_content)
        
        # CODE_OF_CONDUCT.md
        coc_content = """# Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

For any issues, please contact the maintainers.
"""
        with open('CODE_OF_CONDUCT.md', 'w', encoding='utf-8') as f:
            f.write(coc_content)
        
        # SECURITY.md
        security_content = """# Security Policy

If you discover a security vulnerability, please report it by contacting the maintainers directly.
Do not file public issues for security problems.
"""
        with open('SECURITY.md', 'w', encoding='utf-8') as f:
            f.write(security_content)
        
        # .github/ISSUE_TEMPLATE.md
        issue_template = """<!-- Describe the bug or feature request here -->

**Steps to reproduce:**
1.
2.
3.

**Expected behavior:**

**Actual behavior:**
"""
        with open('.github/ISSUE_TEMPLATE.md', 'w', encoding='utf-8') as f:
            f.write(issue_template)
        
        # .github/PULL_REQUEST_TEMPLATE.md
        pr_template = """<!-- Provide a general summary of your changes in the title above -->

## Description

## Related Issue

## Motivation and Context

## Screenshots (if appropriate):

## Types of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Checklist:
- [ ] My code follows the code style of this project
- [ ] My change requires a change to the documentation
- [ ] I have updated the documentation accordingly
"""
        with open('.github/PULL_REQUEST_TEMPLATE.md', 'w', encoding='utf-8') as f:
            f.write(pr_template)
        
        # .editorconfig
        if create_editorconfig:
            editorconfig_content = """# EditorConfig helps maintain consistent coding styles
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 2
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
"""
            with open('.editorconfig', 'w', encoding='utf-8') as f:
                f.write(editorconfig_content)
        
        # .gitattributes
        gitattributes_content = """# Ensure consistent Git behavior
* text=auto
"""
        with open('.gitattributes', 'w', encoding='utf-8') as f:
            f.write(gitattributes_content)
        
        logger.info(f"Project scaffold created for {repo_name}")
