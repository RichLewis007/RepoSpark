#!/usr/bin/env python3
"""
RepoSpark - A PySide6 application to create GitHub repositories
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import sys
import os
import subprocess
import json
import re
import logging
import shlex
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QTextEdit,
    QGroupBox, QFormLayout, QMessageBox, QProgressBar, QTabWidget,
    QListWidget, QListWidgetItem, QSpinBox, QFileDialog, QDialog,
    QDialogButtonBox, QScrollArea, QSplitter, QFrame, QRadioButton,
    QButtonGroup, QTextBrowser, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor

from .ui_loader import load_ui, register_custom_widget

# Configure logging
logger = logging.getLogger(__name__)


class GitHubAPI:
    """Handles GitHub API operations"""
    
    @staticmethod
    def get_user_info() -> Optional[Dict[str, Any]]:
        """Get current GitHub user information"""
        try:
            result = subprocess.run(
                ['gh', 'api', 'user'],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None
    
    @staticmethod
    def get_gitignore_templates() -> List[str]:
        """Get available gitignore templates"""
        try:
            result = subprocess.run(
                ['gh', 'api', 'gitignore/templates'],
                capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return []
    
    @staticmethod
    def create_repository(
        name: str,
        visibility: str,
        description: str = "",
        gitignore_template: str = "",
        license: str = ""
    ) -> bool:
        """Create a new GitHub repository"""
        cmd = ['gh', 'repo', 'create', name, f'--{visibility}']
        
        if description:
            cmd.extend(['--description', description])
        if gitignore_template:
            cmd.extend(['--gitignore', gitignore_template])
        if license:
            cmd.extend(['--license', license])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            # Log error for debugging (stderr contains error message)
            print(f"Error creating repository: {e.stderr if e.stderr else str(e)}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: GitHub CLI (gh) not found", file=sys.stderr)
            return False
    
    @staticmethod
    def set_topics(username: str, repo_name: str, topics: List[str]) -> bool:
        """
        Set repository topics.
        
        Args:
            username: GitHub username
            repo_name: Repository name
            topics: List of topic strings
            
        Returns:
            True if topics were set successfully, False otherwise
        """
        if not topics:
            return True
        
        # Sanitize inputs
        username_safe = shlex.quote(username)
        repo_name_safe = shlex.quote(repo_name)
        
        try:
            topics_json = json.dumps(topics)
            result = subprocess.run([
                'gh', 'api', '-X', 'PATCH', f'repos/{username}/{repo_name}',
                '-F', f'topics={topics_json}',
                '-H', 'Accept: application/vnd.github.mercy-preview+json'
            ], capture_output=True, text=True, check=True)
            logger.info(f"Successfully set topics for {username}/{repo_name}: {topics}")
            return True
        except subprocess.CalledProcessError as e:
            # Topics setting is not critical, so we just log and continue
            error_msg = e.stderr if e.stderr else str(e)
            logger.warning(f"Failed to set topics for {username}/{repo_name}: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("GitHub CLI (gh) not found in PATH")
            return False


class GitOperations:
    """Handles Git operations"""
    
    @staticmethod
    def init_repository() -> bool:
        """
        Initialize git repository in current directory.
        
        Returns:
            True if repository was initialized successfully, False otherwise
        """
        try:
            subprocess.run(['git', 'init'], capture_output=True, text=True, check=True)
            logger.info("Git repository initialized successfully")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error initializing git repository: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return False
    
    @staticmethod
    def add_and_commit() -> bool:
        """
        Add all files and create initial commit.
        
        Returns:
            True if files were added and committed successfully, False otherwise
        """
        try:
            subprocess.run(['git', 'add', '.'], capture_output=True, text=True, check=True)
            subprocess.run(['git', 'commit', '-m', 'Initial commit'], capture_output=True, text=True, check=True)
            logger.info("Files added and committed successfully")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error adding/committing files: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return False
    
    @staticmethod
    def add_remote(username: str, repo_name: str, remote_type: str = 'https') -> bool:
        """
        Add remote origin to git repository.
        
        Args:
            username: GitHub username
            repo_name: Repository name
            remote_type: 'https' or 'ssh'
            
        Returns:
            True if remote was added successfully, False otherwise
        """
        # Sanitize inputs
        username_safe = shlex.quote(username)
        repo_name_safe = shlex.quote(repo_name)
        
        try:
            if remote_type == 'ssh':
                remote_url = f"git@github.com:{username}/{repo_name}.git"
            else:
                remote_url = f"https://github.com/{username}/{repo_name}.git"
            
            subprocess.run(['git', 'remote', 'add', 'origin', remote_url], capture_output=True, text=True, check=True)
            logger.info(f"Remote origin added: {remote_url}")
            return True
        except subprocess.CalledProcessError as e:
            # Check if remote already exists
            if 'already exists' in (e.stderr or '').lower():
                # Try to update existing remote
                try:
                    subprocess.run(['git', 'remote', 'set-url', 'origin', remote_url], capture_output=True, text=True, check=True)
                    logger.info(f"Remote origin updated: {remote_url}")
                    return True
                except subprocess.CalledProcessError as update_error:
                    error_msg = update_error.stderr if update_error.stderr else str(update_error)
                    logger.error(f"Error updating remote: {error_msg}")
            else:
                error_msg = e.stderr if e.stderr else str(e)
                logger.error(f"Error adding remote: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return False
    
    @staticmethod
    def push_to_remote(branch: str = 'main') -> bool:
        """Push to remote repository"""
        try:
            subprocess.run(['git', 'push', '-u', 'origin', branch], capture_output=True, text=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error pushing to remote: {e.stderr if e.stderr else str(e)}", file=sys.stderr)
            return False
        except FileNotFoundError:
            print("Error: Git not found", file=sys.stderr)
            return False
    
    @staticmethod
    def get_current_branch() -> str:
        """Get current branch name"""
        try:
            result = subprocess.run(
                ['git', 'symbolic-ref', '--short', 'HEAD'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'main'


class ScaffoldGenerator:
    """Generates project scaffold files"""
    
    @staticmethod
    def create_scaffold(repo_name: str, create_editorconfig: bool = True, readme_content: str = None) -> None:
        """Create standard project scaffold"""
        # Create directories
        os.makedirs('src', exist_ok=True)
        os.makedirs('tests', exist_ok=True)
        os.makedirs('docs', exist_ok=True)
        os.makedirs('.github', exist_ok=True)
        
        # README.md
        if readme_content:
            with open('README.md', 'w') as f:
                f.write(readme_content)
        else:
            with open('README.md', 'w') as f:
                f.write(f"# {repo_name}\n\nProject initialized using RepoSpark.\n")
        
        # docs/index.md
        with open('docs/index.md', 'w') as f:
            f.write("# Documentation\n\nProject documentation goes here.\n")
        
        # tests/test_placeholder.txt
        with open('tests/test_placeholder.txt', 'w') as f:
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
        with open('CHANGELOG.md', 'w') as f:
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
        with open('CONTRIBUTING.md', 'w') as f:
            f.write(contributing_content)
        
        # CODE_OF_CONDUCT.md
        coc_content = """# Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

For any issues, please contact the maintainers.
"""
        with open('CODE_OF_CONDUCT.md', 'w') as f:
            f.write(coc_content)
        
        # SECURITY.md
        security_content = """# Security Policy

If you discover a security vulnerability, please report it by contacting the maintainers directly.
Do not file public issues for security problems.
"""
        with open('SECURITY.md', 'w') as f:
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
        with open('.github/ISSUE_TEMPLATE.md', 'w') as f:
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
        with open('.github/PULL_REQUEST_TEMPLATE.md', 'w') as f:
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
            with open('.editorconfig', 'w') as f:
                f.write(editorconfig_content)
        
        # .gitattributes
        gitattributes_content = """# Ensure consistent Git behavior
* text=auto
"""
        with open('.gitattributes', 'w') as f:
            f.write(gitattributes_content)


class RepositoryWorker(QThread):
    """Background worker for repository creation"""
    
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
    
    def run(self):
        try:
            # Check if we should stop
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            
            # Check if directory is empty and create scaffold if needed
            if self.config.get('create_scaffold', False):
                if self._should_stop:
                    self.finished.emit(False, "Operation cancelled")
                    return
                self.progress.emit("Creating project scaffold...")
                ScaffoldGenerator.create_scaffold(
                    self.config['repo_name'],
                    self.config.get('create_editorconfig', True),
                    self.config.get('readme_content', '')
                )
            
            # Handle custom gitignore templates
            gitignore_template = self.config.get('gitignore_template', '')
            custom_gitignore_templates = [
                "C++", "C#", "Dart", "Go", "Java", "JavaScript", 
                "Kotlin", "PHP", "R", "Ruby", "Rust", "Scala", "Swift", "TypeScript"
            ]
            
            # Create GitHub repository
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            self.progress.emit("Creating GitHub repository...")
            if not GitHubAPI.create_repository(
                self.config['repo_name'],
                self.config['visibility'],
                self.config.get('description', ''),
                gitignore_template if gitignore_template not in custom_gitignore_templates else "",
                self.config.get('license', '')
            ):
                self.finished.emit(False, "Failed to create GitHub repository")
                return
            
            # Create custom gitignore file if needed (before git init)
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            if gitignore_template in custom_gitignore_templates:
                self.progress.emit(f"Creating custom .gitignore for {gitignore_template}...")
                self._create_custom_gitignore(gitignore_template)
            elif gitignore_template and gitignore_template not in custom_gitignore_templates:
                # For GitHub templates, we need to fetch the .gitignore from the created repo
                # or create it locally before git add
                self.progress.emit(f"Fetching .gitignore template for {gitignore_template}...")
                self._fetch_gitignore_template(gitignore_template)
            
            # Initialize git if needed
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            if not os.path.exists('.git'):
                self.progress.emit("Initializing git repository...")
                if not GitOperations.init_repository():
                    self.finished.emit(False, "Failed to initialize git repository")
                    return
            
            # Add and commit files
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            self.progress.emit("Adding and committing files...")
            if not GitOperations.add_and_commit():
                self.finished.emit(False, "Failed to add and commit files")
                return
            
            # Add remote
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            self.progress.emit("Adding remote origin...")
            if not GitOperations.add_remote(
                self.config['username'],
                self.config['repo_name'],
                self.config.get('remote_type', 'https')
            ):
                self.finished.emit(False, "Failed to add remote origin")
                return
            
            # Push to GitHub
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            self.progress.emit("Pushing to GitHub...")
            if not GitOperations.push_to_remote():
                self.finished.emit(False, "Failed to push to GitHub")
                return
            
            # Set topics
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return
            if self.config.get('topics'):
                self.progress.emit("Setting repository topics...")
                if not GitHubAPI.set_topics(
                    self.config['username'],
                    self.config['repo_name'],
                    self.config['topics']
                ):
                    self.progress.emit("Warning: Failed to set topics")
            
            self.finished.emit(True, "Repository created successfully!")
            
        except Exception as e:
            self.finished.emit(False, f"Error: {str(e)}")
    
    def _create_custom_gitignore(self, template_name: str) -> None:
        """Create a custom .gitignore file for languages/frameworks not in GitHub's library"""
        gitignore_content = f"# .gitignore for {template_name} projects\n"
        
        if template_name == "JavaScript":
            gitignore_content += """# No files are ignored for JavaScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
"""
        elif template_name == "TypeScript":
            gitignore_content += """# No files are ignored for TypeScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
# *.tsbuildinfo
"""
        elif template_name == "Java":
            gitignore_content += """# No files are ignored for Java projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# *.class
# *.jar
# *.war
# *.ear
# .gradle/
# build/
# out/
# .idea/
# *.iml
"""
        elif template_name == "C++":
            gitignore_content += """# No files are ignored for C++ projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# bin/
# obj/
# *.o
# *.a
# *.so
# *.dll
# *.exe
# CMakeFiles/
# CMakeCache.txt
# cmake_install.cmake
# Makefile
"""
        elif template_name == "C#":
            gitignore_content += """# No files are ignored for C# projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# obj/
# *.user
# *.suo
# *.cache
# *.dll
# *.exe
# *.pdb
# *.log
# .vs/
# packages/
"""
        elif template_name == "Go":
            gitignore_content += """# No files are ignored for Go projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# pkg/
# *.exe
# *.exe~
# *.dll
# *.so
# *.dylib
# go.work
"""
        elif template_name == "Rust":
            gitignore_content += """# No files are ignored for Rust projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# Cargo.lock
# *.pdb
"""
        elif template_name == "Python":
            gitignore_content += """# No files are ignored for Python projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# __pycache__/
# *.py[cod]
# *$py.class
# *.so
# .Python
# build/
# develop-eggs/
# dist/
# downloads/
# eggs/
# .eggs/
# lib/
# lib64/
# parts/
# sdist/
# var/
# wheels/
# *.egg-info/
# .installed.cfg
# *.egg
# MANIFEST
# .pytest_cache/
# .coverage
# .env
# .venv
# env/
# venv/
# ENV/
# env.bak/
# venv.bak/
"""
        else:
            # Generic template for other languages
            gitignore_content += f"""# No files are ignored for {template_name} projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# dist/
# .env
# *.log
# .cache/
# .tmp/
"""
        
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
    
    def _fetch_gitignore_template(self, template_name: str) -> None:
        """Fetch gitignore template from GitHub API and create local file"""
        try:
            result = subprocess.run(
                ['gh', 'api', f'gitignore/templates/{template_name}'],
                capture_output=True, text=True, check=True
            )
            template_data = json.loads(result.stdout)
            content = template_data.get('source', '')
            
            # Only create if we got content and file doesn't exist
            if content and not os.path.exists('.gitignore'):
                with open('.gitignore', 'w') as f:
                    f.write(content)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            # If we can't fetch it, that's okay - GitHub already created it in the repo
            pass


class FolderTreeWidget(QTreeWidget):
    """Custom tree widget that looks like macOS Finder/Windows Explorer"""
    
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(False)
        self.setIndentation(24)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 8px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                color: #24292f;
                selection-background-color: #0969da;
                selection-color: white;
                outline: none;
            }
            QTreeWidget::item {
                padding: 8px 12px;
                border: none;
                background: transparent;
                border-radius: 6px;
                margin: 2px 4px;
                min-height: 20px;
            }
            QTreeWidget::item:hover {
                background-color: #f6f8fa;
                border: 1px solid #e1e4e8;
            }
            QTreeWidget::item:selected {
                background-color: #0969da;
                color: white;
                border: 1px solid #0969da;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuNSA2TDEwIDZMMTAgNUw0LjUgNUw0LjUgNloiIGZpbGw9IiM2NTZkNzYiLz4KPHBhdGggZD0iTTYuNSA0LjVMMTAuNSA2TDYuNSA3LjVMNi41IDQuNVoiIGZpbGw9IiM2NTZkNzYiLz4KPC9zdmc+);
            }
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNC41TDEwIDQuNUwxMCA1LjVMNCA1LjVMNCA0LjVaIiBmaWxsPSIjNjU2ZDc2Ii8+Cjwvc3ZnPg==);
            }
            QTreeWidget::branch:!has-children:!has-siblings,
            QTreeWidget::branch:!has-children:has-siblings {
                image: none;
            }
            QTreeWidget::branch:has-children:!has-siblings:closed:hover,
            QTreeWidget::branch:closed:has-children:has-siblings:hover,
            QTreeWidget::branch:open:has-children:!has-siblings:hover,
            QTreeWidget::branch:open:has-children:has-siblings:hover {
                background-color: #f6f8fa;
                border-radius: 3px;
            }
        """)
    
    def add_folder_item(self, parent: Optional[QTreeWidgetItem], name: str, folder_type: str = "default") -> QTreeWidgetItem:
        """Add a folder item with appropriate icon"""
        if parent is None:
            # Add to the tree widget itself (root level)
            item = QTreeWidgetItem(self)
        else:
            # Add as child of the parent
            item = QTreeWidgetItem(parent)
        
        item.setText(0, name)
        
        # Set appropriate folder icon based on type
        if folder_type == "src":
            item.setIcon(0, self._get_folder_icon("📁", "#0366d6"))  # Blue for source
        elif folder_type == "tests":
            item.setIcon(0, self._get_folder_icon("📁", "#28a745"))  # Green for tests
        elif folder_type == "docs":
            item.setIcon(0, self._get_folder_icon("📁", "#6f42c1"))  # Purple for docs
        elif folder_type == "github":
            item.setIcon(0, self._get_folder_icon("📁", "#24292e"))  # Dark for .github
        elif folder_type == "root":
            item.setIcon(0, self._get_folder_icon("📁", "#f6f8fa"))  # Light for root
        else:
            item.setIcon(0, self._get_folder_icon("📁", "#586069"))  # Default gray
        
        return item
    
    def add_file_item(self, parent: Optional[QTreeWidgetItem], name: str, file_type: str = "default") -> QTreeWidgetItem:
        """Add a file item with appropriate icon"""
        if parent is None:
            # Add to the tree widget itself (root level)
            item = QTreeWidgetItem(self)
        else:
            # Add as child of the parent
            item = QTreeWidgetItem(parent)
        
        item.setText(0, name)
        
        # Set appropriate file icon based on type
        if file_type == "readme":
            item.setIcon(0, self._get_file_icon("📖", "#0366d6"))  # Blue for README
        elif file_type == "changelog":
            item.setIcon(0, self._get_file_icon("📝", "#28a745"))  # Green for changelog
        elif file_type == "contributing":
            item.setIcon(0, self._get_file_icon("🤝", "#6f42c1"))  # Purple for contributing
        elif file_type == "conduct":
            item.setIcon(0, self._get_file_icon("📋", "#d73a49"))  # Red for code of conduct
        elif file_type == "security":
            item.setIcon(0, self._get_file_icon("🔒", "#f6a434"))  # Orange for security
        elif file_type == "config":
            item.setIcon(0, self._get_file_icon("⚙️", "#586069"))  # Gray for config files
        elif file_type == "issue":
            item.setIcon(0, self._get_file_icon("🐛", "#d73a49"))  # Red for issues
        elif file_type == "pr":
            item.setIcon(0, self._get_file_icon("🔀", "#28a745"))  # Green for PRs
        elif file_type == "docs":
            item.setIcon(0, self._get_file_icon("📚", "#6f42c1"))  # Purple for docs
        elif file_type == "test":
            item.setIcon(0, self._get_file_icon("🧪", "#f6a434"))  # Orange for tests
        else:
            item.setIcon(0, self._get_file_icon("📄", "#586069"))  # Default gray
        
        return item
    
    def _get_folder_icon(self, emoji: str, color: str) -> QIcon:
        """Create a custom folder icon with emoji and color"""
        # For now, use the system folder icon but with a simpler approach
        base_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)
        
        # If we want to add color, we can do it later with a more robust approach
        # For now, just return the base icon to avoid mask issues
        return base_icon
    
    def _get_file_icon(self, emoji: str, color: str) -> QIcon:
        """Create a custom file icon with emoji and color"""
        # For now, use the system file icon but with a simpler approach
        base_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        
        # If we want to add color, we can do it later with a more robust approach
        # For now, just return the base icon to avoid mask issues
        return base_icon


class RepoSparkGUI(QMainWindow):
    """Main GUI window for RepoSpark application"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.focus_timer = None
        
        # Register custom widgets for QUiLoader
        register_custom_widget("FolderTreeWidget", FolderTreeWidget)
        
        self.init_ui()
        self.load_defaults()
    
    def _find_widget(self, parent: QWidget, widget_type: type, name: str) -> Optional[QWidget]:
        """
        Helper method to find a widget and raise an error if not found.
        
        Args:
            parent: Parent widget to search in
            widget_type: Type of widget to find
            name: Name of the widget
            
        Returns:
            The found widget
            
        Raises:
            RuntimeError: If widget is not found
        """
        widget = parent.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(f"Required widget '{name}' ({widget_type.__name__}) not found in UI file")
        return widget
    
    def _find_widgets(self, parent: QWidget, widget_specs: List[Tuple[type, str]]) -> Dict[str, QWidget]:
        """
        Find multiple widgets at once and validate they all exist.
        
        This method reduces code duplication and provides consistent error handling
        when validating multiple widgets from a loaded UI file.
        
        Args:
            parent: Parent widget to search in
            widget_specs: List of tuples containing (widget_type, widget_name)
            
        Returns:
            Dictionary mapping widget names to found widgets
            
        Raises:
            RuntimeError: If any widget is not found (includes list of all missing widgets)
            
        Example:
            >>> widgets = self._find_widgets(central_widget, [
            ...     (QTabWidget, "tabs"),
            ...     (QPushButton, "create_button"),
            ...     (QPushButton, "cancel_button"),
            ... ])
            >>> tabs = widgets["tabs"]
            >>> create_btn = widgets["create_button"]
        """
        widgets = {}
        missing = []
        
        for widget_type, name in widget_specs:
            widget = parent.findChild(widget_type, name)
            if widget is None:
                missing.append(f"'{name}' ({widget_type.__name__})")
            else:
                widgets[name] = widget
        
        if missing:
            missing_list = ", ".join(missing)
            raise RuntimeError(
                f"Required widgets not found in UI file: {missing_list}"
            )
        
        return widgets
    
    def _create_fallback_ui(self) -> QWidget:
        """
        Create a minimal fallback UI when .ui files cannot be loaded.
        
        This provides basic functionality even when UI files are missing or corrupted.
        
        Returns:
            QWidget: A minimal central widget with basic controls
        """
        logger.warning("Creating fallback UI due to .ui file loading failure")
        
        fallback_widget = QWidget()
        layout = QVBoxLayout(fallback_widget)
        
        # Add error message
        error_label = QLabel(
            "⚠️ UI Loading Error\n\n"
            "The application is running in fallback mode.\n"
            "Please ensure all .ui files are present in:\n"
            "src/repospark/assets/ui/\n\n"
            "Some features may be limited."
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #d73a49; font-size: 14px; padding: 20px;")
        layout.addWidget(error_label)
        
        # Add basic controls
        self.repo_name_edit = QLineEdit()
        self.repo_name_edit.setPlaceholderText("Repository name")
        layout.addWidget(QLabel("Repository Name:"))
        layout.addWidget(self.repo_name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description (optional)")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_edit)
        
        # Visibility
        visibility_group = QGroupBox("Visibility")
        visibility_layout = QVBoxLayout(visibility_group)
        self.visibility_public_radio = QRadioButton("Public")
        self.visibility_public_radio.setChecked(True)
        self.visibility_private_radio = QRadioButton("Private")
        visibility_layout.addWidget(self.visibility_public_radio)
        visibility_layout.addWidget(self.visibility_private_radio)
        layout.addWidget(visibility_group)
        
        # Create button
        self.create_button = QPushButton("Create Repository")
        self.create_button.clicked.connect(self.create_repository)
        layout.addWidget(self.create_button)
        
        # Status label
        self.status_label = QLabel("Ready to create repository")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)
        
        # Initialize minimal tab widget (empty)
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)  # Hide tabs in fallback mode
        
        # Initialize other required widgets with defaults
        self.gitignore_combo = QComboBox()
        self.gitignore_combo.addItem("None")
        self.topics_edit = QLineEdit()
        self.help_browser = QTextBrowser()
        self.remote_https_radio = self.visibility_public_radio  # Reuse for compatibility
        self.remote_ssh_radio = self.visibility_private_radio
        self.open_browser_check = QCheckBox()
        self.create_scaffold_check = QCheckBox()
        self.create_scaffold_check.setChecked(True)
        self.create_editorconfig_check = QCheckBox()
        self.create_editorconfig_check.setChecked(True)
        self.scaffold_tree = FolderTreeWidget()
        self.template_selector = QComboBox()
        self.readme_editor = QTextEdit()
        self.readme_preview = QTextEdit()
        self.regenerate_readme_btn = QPushButton()
        
        # Initialize radio buttons for license and project type
        self.license_mit_radio = self.visibility_public_radio  # Reuse for compatibility
        self.license_none_radio = self.visibility_private_radio
        self.license_apache_radio = self.visibility_private_radio
        self.license_gpl_radio = self.visibility_private_radio
        self.project_type_other_radio = self.visibility_public_radio
        self.project_type_python_lib_radio = self.visibility_private_radio
        self.project_type_python_cli_radio = self.visibility_private_radio
        self.project_type_js_radio = self.visibility_private_radio
        self.project_type_web_radio = self.visibility_private_radio
        self.project_type_data_radio = self.visibility_private_radio
        self.project_type_docs_radio = self.visibility_private_radio
        
        layout.addStretch()
        
        return fallback_widget
    
    def init_ui(self):
        """Initialize the user interface by loading .ui files"""
        # Get screen size and set window to half width
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        half_width = screen_geometry.width() // 2
        window_height = min(800, screen_geometry.height() - 100)
        
        # Center the window horizontally
        x_position = (screen_geometry.width() - half_width) // 2
        y_position = (screen_geometry.height() - window_height) // 2
        
        self.setGeometry(x_position, y_position, half_width, window_height)
        
        # Load main window UI with fallback
        try:
            central_widget = load_ui("main_window.ui", self)
            self.setCentralWidget(central_widget)
        except RuntimeError as e:
            logger.error(f"Failed to load main window UI: {e}")
            # Show error dialog with fallback option
            reply = QMessageBox.critical(
                self, 
                "UI Loading Error", 
                f"Failed to load main window UI:\n{str(e)}\n\n"
                "Would you like to continue with a minimal fallback interface?\n"
                "(Some features may not be available)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Create fallback UI
                central_widget = self._create_fallback_ui()
                self.setCentralWidget(central_widget)
                QMessageBox.warning(
                    self,
                    "Fallback Mode",
                    "Running in fallback mode. Some features may be limited.\n"
                    "Please check that all .ui files are present in:\n"
                    "src/repospark/assets/ui/"
                )
            else:
                raise
        
        # Find widgets from the loaded UI using batch validation
        try:
            widgets = self._find_widgets(central_widget, [
                (QTabWidget, "tabs"),
                (QProgressBar, "progress_bar"),
                (QLabel, "status_label"),
                (QPushButton, "create_button"),
                (QPushButton, "cancel_button"),
            ])
            self.tabs = widgets["tabs"]
            self.progress_bar = widgets["progress_bar"]
            self.status_label = widgets["status_label"]
            self.create_button = widgets["create_button"]
            self.cancel_button = widgets["cancel_button"]
        except RuntimeError as e:
            QMessageBox.critical(
                None,
                "UI Configuration Error",
                f"Failed to find required widgets:\n{str(e)}\n\nPlease check the .ui files."
            )
            raise
        
        # Set initial state
        self.progress_bar.setVisible(False)
        self.cancel_button.setEnabled(False)
        
        # Wire up signals
        self.create_button.clicked.connect(self.create_repository)
        self.cancel_button.clicked.connect(self.cancel_operation)
        
        # Create menu bar with Help menu
        self._create_menu_bar()
        
        # Load and add tabs
        basic_tab = self.create_basic_tab()
        self.tabs.addTab(basic_tab, "Project Basics")
        
        readme_tab = self.create_readme_tab()
        self.tabs.addTab(readme_tab, "README.md")
        
        advanced_tab = self.create_advanced_tab()
        self.tabs.addTab(advanced_tab, "Advanced Settings")
        
        scaffold_tab = self.create_scaffold_tab()
        self.tabs.addTab(scaffold_tab, "Project Scaffold")
    
    def create_basic_tab(self) -> QWidget:
        """Create the basic settings tab by loading .ui file"""
        widget = load_ui("basic_tab.ui", self)
        
        # Find all widgets from the loaded UI
        self.repo_name_edit = widget.findChild(QLineEdit, "repo_name_edit")
        self.description_edit = widget.findChild(QLineEdit, "description_edit")
        self.visibility_public_radio = widget.findChild(QRadioButton, "visibility_public_radio")
        self.visibility_private_radio = widget.findChild(QRadioButton, "visibility_private_radio")
        self.license_none_radio = widget.findChild(QRadioButton, "license_none_radio")
        self.license_mit_radio = widget.findChild(QRadioButton, "license_mit_radio")
        self.license_apache_radio = widget.findChild(QRadioButton, "license_apache_radio")
        self.license_gpl_radio = widget.findChild(QRadioButton, "license_gpl_radio")
        self.project_type_other_radio = widget.findChild(QRadioButton, "project_type_other_radio")
        self.project_type_python_lib_radio = widget.findChild(QRadioButton, "project_type_python_lib_radio")
        self.project_type_python_cli_radio = widget.findChild(QRadioButton, "project_type_python_cli_radio")
        self.project_type_js_radio = widget.findChild(QRadioButton, "project_type_js_radio")
        self.project_type_web_radio = widget.findChild(QRadioButton, "project_type_web_radio")
        self.project_type_data_radio = widget.findChild(QRadioButton, "project_type_data_radio")
        self.project_type_docs_radio = widget.findChild(QRadioButton, "project_type_docs_radio")
        self.gitignore_combo = widget.findChild(QComboBox, "gitignore_combo")
        self.topics_edit = widget.findChild(QLineEdit, "topics_edit")
        self.help_browser = widget.findChild(QTextBrowser, "help_browser")
        
        # Configure widgets (gitignore_combo already has "None" from .ui file)
        self.gitignore_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Set tab order within groups
        self.setTabOrder(self.visibility_public_radio, self.visibility_private_radio)
        self.setTabOrder(self.license_none_radio, self.license_mit_radio)
        self.setTabOrder(self.license_mit_radio, self.license_apache_radio)
        self.setTabOrder(self.license_apache_radio, self.license_gpl_radio)
        self.setTabOrder(self.project_type_other_radio, self.project_type_python_lib_radio)
        self.setTabOrder(self.project_type_python_lib_radio, self.project_type_python_cli_radio)
        self.setTabOrder(self.project_type_python_cli_radio, self.project_type_js_radio)
        self.setTabOrder(self.project_type_js_radio, self.project_type_web_radio)
        self.setTabOrder(self.project_type_web_radio, self.project_type_data_radio)
        self.setTabOrder(self.project_type_data_radio, self.project_type_docs_radio)
        
        # Wire up signals
        self.repo_name_edit.textChanged.connect(self.update_scaffold_tree)
        self.visibility_public_radio.toggled.connect(self.on_visibility_changed)
        self.visibility_private_radio.toggled.connect(self.on_visibility_changed)
        self.license_none_radio.toggled.connect(self.on_license_changed)
        self.license_mit_radio.toggled.connect(self.on_license_changed)
        self.license_apache_radio.toggled.connect(self.on_license_changed)
        self.license_gpl_radio.toggled.connect(self.on_license_changed)
        self.project_type_other_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_python_lib_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_python_cli_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_js_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_web_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_data_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_docs_radio.toggled.connect(self.on_project_type_changed)
        self.gitignore_combo.currentTextChanged.connect(self.update_help_info)
        self.gitignore_combo.currentTextChanged.connect(self.on_gitignore_changed)
        
        # Initialize focus tracking
        self.current_focus_section = ""
        
        # Set up focus tracking timer
        self.focus_timer = QTimer()
        self.focus_timer.timeout.connect(self.check_focus)
        self.focus_timer.start(100)  # Check every 100ms
        
        # Initialize help content
        self.update_help_info()
        
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab by loading .ui file"""
        widget = load_ui("advanced_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.remote_https_radio = widget.findChild(QRadioButton, "remote_https_radio")
        self.remote_ssh_radio = widget.findChild(QRadioButton, "remote_ssh_radio")
        self.open_browser_check = widget.findChild(QCheckBox, "open_browser_check")
        
        # Create button group for remote type
        self.remote_button_group = QButtonGroup()
        self.remote_button_group.addButton(self.remote_https_radio)
        self.remote_button_group.addButton(self.remote_ssh_radio)
        
        return widget
    
    def create_scaffold_tab(self) -> QWidget:
        """Create the project scaffold tab by loading .ui file"""
        widget = load_ui("scaffold_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.create_scaffold_check = widget.findChild(QCheckBox, "create_scaffold_check")
        self.create_editorconfig_check = widget.findChild(QCheckBox, "create_editorconfig_check")
        
        # Add custom FolderTreeWidget to the preview layout
        preview_group = widget.findChild(QGroupBox, "preview_group")
        if preview_group:
            preview_layout = preview_group.layout()
            if preview_layout:
                self.scaffold_tree = FolderTreeWidget()
                self.scaffold_tree.setMinimumHeight(300)
                preview_layout.addWidget(self.scaffold_tree)
        else:
            # Fallback: create custom widget directly
            self.scaffold_tree = FolderTreeWidget()
            self.scaffold_tree.setMinimumHeight(300)
        
        # Wire up signals
        self.create_scaffold_check.toggled.connect(self.update_scaffold_tree)
        self.create_editorconfig_check.toggled.connect(self.update_scaffold_tree)
        
        # Update the tree initially
        self.update_scaffold_tree()
        
        return widget
    
    def create_readme_tab(self) -> QWidget:
        """Create the README.md customization tab by loading .ui file"""
        widget = load_ui("readme_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.template_selector = widget.findChild(QComboBox, "template_selector")
        self.regenerate_readme_btn = widget.findChild(QPushButton, "regenerate_readme_btn")
        self.readme_editor = widget.findChild(QTextEdit, "readme_editor")
        self.readme_preview = widget.findChild(QTextEdit, "readme_preview")
        splitter = widget.findChild(QSplitter, "splitter")
        
        # Configure widgets
        self.template_selector.addItems([
            "Auto-generate from project type",
            "Custom template",
            "Minimal template"
        ])
        self.readme_editor.setFont(QFont("Monaco", 10))
        self.readme_preview.setMaximumWidth(400)
        
        # Set splitter proportions
        if splitter:
            splitter.setSizes([600, 400])
        
        # Wire up signals
        self.template_selector.currentTextChanged.connect(self.update_readme_preview)
        self.regenerate_readme_btn.clicked.connect(self.update_readme_preview)
        self.readme_editor.textChanged.connect(self.on_readme_editor_changed)
        
        return widget
    
    
    def load_defaults(self) -> None:
        """Load default values"""
        # Set default repository name from current directory
        default_name = os.path.basename(os.getcwd())
        self.repo_name_edit.setText(default_name)
        
        # Load gitignore templates
        templates = GitHubAPI.get_gitignore_templates()
        
        # Add common languages and frameworks that don't have GitHub templates
        # These will be inserted in alphabetical order
        custom_templates = [
            "C++",
            "C#",
            "Dart",
            "Go",
            "Java",
            "JavaScript",
            "Kotlin",
            "PHP",
            "R",
            "Ruby",
            "Rust",
            "Scala",
            "Swift",
            "TypeScript"
        ]
        
        # Combine and sort all templates (skip "None" as it's already in the combo from .ui file)
        all_templates = sorted(templates + custom_templates)
        
        for template in all_templates:
            self.gitignore_combo.addItem(template)
        
        # Initialize README preview
        self.update_readme_preview()
    
    def validate_inputs(self) -> Tuple[bool, str]:
        """
        Validate user inputs including repository name, description, and topics.
        
        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty string.
        """
        repo_name = self.repo_name_edit.text().strip()
        if not repo_name:
            return False, "Repository name is required"
        
        # Validate repository name format (GitHub rules)
        # Repository names can only contain alphanumeric characters, hyphens, underscores, and dots
        # They cannot start with a dot or hyphen, and cannot end with a dot
        if not re.match(r'^[a-zA-Z0-9._-]+$', repo_name):
            return False, "Repository name can only contain alphanumeric characters, hyphens, underscores, and dots"
        
        if repo_name.startswith('.') or repo_name.startswith('-'):
            return False, "Repository name cannot start with a dot or hyphen"
        
        if repo_name.endswith('.'):
            return False, "Repository name cannot end with a dot"
        
        if len(repo_name) > 100:
            return False, "Repository name cannot exceed 100 characters"
        
        # Check for command injection attempts
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')', '<', '>', '\n', '\r']
        if any(char in repo_name for char in dangerous_chars):
            return False, "Repository name contains invalid characters"
        
        # Validate description
        description = self.description_edit.text().strip()
        if len(description) > 160:  # GitHub description limit
            return False, "Description cannot exceed 160 characters"
        
        # Check for dangerous characters in description
        if any(char in description for char in ['\n', '\r', '\x00']):
            return False, "Description contains invalid characters (newlines or null bytes)"
        
        # Validate topics
        topics_text = self.topics_edit.text().strip()
        if topics_text:
            topics = [t.strip() for t in topics_text.split(',') if t.strip()]
            if len(topics) > 20:  # GitHub topics limit
                return False, "Maximum 20 topics allowed"
            
            for topic in topics:
                if len(topic) > 35:  # GitHub topic length limit
                    return False, f"Topic '{topic}' exceeds maximum length of 35 characters"
                if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*$', topic):
                    return False, f"Topic '{topic}' contains invalid characters. Topics can only contain alphanumeric characters and hyphens, and must start with a letter or number"
        
        # Check if gh CLI is available
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "GitHub CLI (gh) is not installed or not available"
        
        # Check if git is available
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Git is not installed or not available"
        
        # Check if user is authenticated
        user_info = GitHubAPI.get_user_info()
        if not user_info:
            return False, "GitHub CLI is not authenticated. Run 'gh auth login' first"
        
        logger.debug(f"Input validation passed for repository: {repo_name}")
        return True, ""
    
    def on_visibility_changed(self) -> None:
        """Handle visibility change"""
        self.update_help_info()
    
    def on_license_changed(self) -> None:
        """Handle license change"""
        self.update_help_info()
    
    def on_project_type_changed(self) -> None:
        """Handle project type change"""
        self.update_help_info()
        self.update_readme_preview()
        self.update_scaffold_tree()
    
    def on_gitignore_changed(self) -> None:
        """Handle gitignore template changes and maintain focus"""
        # Set focus back to the gitignore combo box to keep help context
        self.gitignore_combo.setFocus()
        self.current_focus_section = "gitignore"
        self.update_help_info()
    

    
    def check_focus(self):
        """Check which widget currently has focus and update help accordingly"""
        focused_widget = QApplication.focusWidget()
        
        if focused_widget == self.repo_name_edit:
            if self.current_focus_section != "repo_name":
                self.current_focus_section = "repo_name"
                self.update_help_info()
        elif focused_widget == self.description_edit:
            if self.current_focus_section != "description":
                self.current_focus_section = "description"
                self.update_help_info()
        elif focused_widget in [self.visibility_public_radio, self.visibility_private_radio]:
            if self.current_focus_section != "visibility":
                self.current_focus_section = "visibility"
                self.update_help_info()
        elif focused_widget in [self.license_none_radio, self.license_mit_radio, self.license_apache_radio, self.license_gpl_radio]:
            if self.current_focus_section != "license":
                self.current_focus_section = "license"
                self.update_help_info()
        elif focused_widget in [self.project_type_other_radio, self.project_type_python_lib_radio, self.project_type_python_cli_radio, self.project_type_js_radio, 
                               self.project_type_web_radio, self.project_type_data_radio, self.project_type_docs_radio]:
            if self.current_focus_section != "project_type":
                self.current_focus_section = "project_type"
                self.update_help_info()
        elif focused_widget == self.gitignore_combo:
            if self.current_focus_section != "gitignore":
                self.current_focus_section = "gitignore"
                self.update_help_info()
        elif focused_widget == self.topics_edit:
            if self.current_focus_section != "topics":
                self.current_focus_section = "topics"
                self.update_help_info()
        elif self.current_focus_section != "":
            # No widget has focus, show general help
            self.current_focus_section = ""
            self.update_help_info()
    
    def on_focus_changed(self, section: str):
        """Handle focus changes to show context-aware help"""
        self.current_focus_section = section
        self.update_help_info()
    
    def update_help_info(self) -> None:
        """Update the help information based on current selections"""
        help_content = self._generate_help_content()
        self.help_browser.setHtml(help_content)
    
    def _generate_help_content(self) -> str:
        """Generate context-aware help content"""
        repo_name = self.repo_name_edit.text().strip()
        description = self.description_edit.text().strip()
        visibility = self._get_selected_visibility()
        gitignore = self.gitignore_combo.currentText()
        license_name = self._get_selected_license()
        project_type = self._get_selected_project_type()
        topics = [t.strip() for t in self.topics_edit.text().split(',') if t.strip()]
        
        # If no specific section is focused, show general overview
        if not self.current_focus_section:
            return self._generate_general_help(repo_name, description, visibility, gitignore, license_name, project_type, topics)
        
        # Show context-specific help based on focused section
        if self.current_focus_section == "repo_name":
            return self._generate_repo_name_help(repo_name)
        elif self.current_focus_section == "description":
            return self._generate_description_help(description)
        elif self.current_focus_section == "visibility":
            return self._generate_visibility_help(visibility)
        elif self.current_focus_section == "license":
            return self._generate_license_help(license_name)
        elif self.current_focus_section == "project_type":
            return self._generate_project_type_help(project_type)
        elif self.current_focus_section == "gitignore":
            return self._generate_gitignore_help(gitignore)
        elif self.current_focus_section == "topics":
            return self._generate_topics_help(topics)
        
        return self._generate_general_help(repo_name, description, visibility, gitignore, license_name, project_type, topics)
    
    def _generate_general_help(self, repo_name: str, description: str, visibility: str, gitignore: str, license_name: str, project_type: str, topics: List[str]) -> str:
        """Generate general overview help content"""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                p {{ margin: 8px 0; line-height: 1.4; }}
                ul {{ margin: 8px 0; padding-left: 20px; }}
                li {{ margin: 4px 0; }}
                strong {{ color: #0366d6; }}
            </style>
        </head>
        <body>
            <h3>ℹ️ Project Overview</h3>
            <p>Click on any field or option to see detailed help information.</p>
            
            <h3>📁 Repository: {repo_name or 'Not set'}</h3>
            <p>Click the repository name field for naming guidelines.</p>
            
            <h3>🔓 Visibility: {visibility.title()}</h3>
            <p>Click the visibility options for details about public vs private.</p>
            
            <h3>📄 License: {license_name}</h3>
            <p>Click the license options to understand different license types.</p>
            
            <h3>🐍 Project Type: {project_type}</h3>
            <p>Click the project type options to see what each type includes.</p>
        </body>
        </html>
        """
    
    def _generate_repo_name_help(self, repo_name: str) -> str:
        """Generate help content for repository name"""
        if repo_name:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📁 Repository Name: <strong>{repo_name}</strong></h3>
                <p>This will be the name of your GitHub repository. It should be:</p>
                <ul>
                    <li>Descriptive and memorable</li>
                    <li>Use lowercase letters and hyphens</li>
                    <li>Unique on GitHub</li>
                    <li>Easy to type and remember</li>
                </ul>
                <p><strong>URL:</strong> github.com/username/{repo_name}</p>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📁 Repository Name</h3>
                <p>Enter a name for your repository. This will be used to create the GitHub repository and will appear in the URL.</p>
                <p><strong>Guidelines:</strong></p>
                <ul>
                    <li>Use lowercase letters and hyphens</li>
                    <li>Make it descriptive but concise</li>
                    <li>Avoid special characters</li>
                    <li>Check if the name is available on GitHub</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_description_help(self, description: str) -> str:
        """Generate help content for description"""
        if description:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📝 Description</h3>
                <p><strong>Current:</strong> {description}</p>
                <p>This description will appear on your GitHub repository page and in search results.</p>
                <p><strong>Tips:</strong></p>
                <ul>
                    <li>Keep it concise but informative</li>
                    <li>Explain what the project does</li>
                    <li>Mention key technologies used</li>
                    <li>Include the main benefit or purpose</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📝 Description</h3>
                <p>Add a brief description of what your project does. This helps others understand your project at a glance.</p>
                <p><strong>What to include:</strong></p>
                <ul>
                    <li>What the project does</li>
                    <li>Main features or capabilities</li>
                    <li>Target audience or use case</li>
                    <li>Key technologies or frameworks</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_visibility_help(self, visibility: str) -> str:
        """Generate help content for visibility"""
        if visibility == "public":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔓 Visibility: Public</h3>
                <p><strong>✅ Anyone can see your repository</strong></p>
                <ul>
                    <li>Visible in search results</li>
                    <li>Can be starred and forked by anyone</li>
                    <li>Great for open source projects</li>
                    <li>Free for unlimited public repositories</li>
                    <li>Good for portfolio and collaboration</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔒 Visibility: Private</h3>
                <p><strong>🔐 Only you and collaborators can see it</strong></p>
                <ul>
                    <li>Not visible in search results</li>
                    <li>Perfect for personal projects</li>
                    <li>Good for proprietary code</li>
                    <li>Requires GitHub Pro for unlimited private repos</li>
                    <li>You control who can access it</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_license_help(self, license_name: str) -> str:
        """Generate help content for license"""
        if license_name == "MIT":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: MIT</h3>
                <p><strong>🔄 Very permissive license</strong></p>
                <ul>
                    <li>Anyone can use, modify, and distribute</li>
                    <li>Must include original license and copyright</li>
                    <li>No warranty provided</li>
                    <li>Most popular for open source</li>
                    <li>Great for libraries and tools</li>
                </ul>
            </body>
            </html>
            """
        elif license_name == "Apache 2.0":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: Apache 2.0</h3>
                <p><strong>🛡️ Permissive with patent protection</strong></p>
                <ul>
                    <li>Similar to MIT but with patent protection</li>
                    <li>Good for enterprise use</li>
                    <li>Requires stating changes</li>
                    <li>Popular for business-friendly projects</li>
                    <li>Explicit patent grant</li>
                </ul>
            </body>
            </html>
            """
        elif license_name == "GPL 3.0":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: GPL 3.0</h3>
                <p><strong>🔗 Copyleft license</strong></p>
                <ul>
                    <li>Derivative works must also be GPL</li>
                    <li>Ensures code stays open source</li>
                    <li>More restrictive than MIT/Apache</li>
                    <li>Good for ensuring openness</li>
                    <li>Requires source code sharing</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: None</h3>
                <p><strong>⚠️ No license specified</strong></p>
                <ul>
                    <li>All rights reserved</li>
                    <li>Others cannot legally use your code</li>
                    <li>Not recommended for open source</li>
                    <li>Consider adding a license later</li>
                    <li>You retain full copyright</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_project_type_help(self, project_type: str) -> str:
        """Generate help content for project type"""
        if project_type == "Other":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔧 Project Type: Other</h3>
                <p><strong>📁 Generic project structure</strong></p>
                <ul>
                    <li>Basic project scaffolding</li>
                    <li>Standard documentation files</li>
                    <li>GitHub templates and workflows</li>
                    <li>Flexible for any project type</li>
                    <li>Minimal language-specific setup</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Python Library":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🐍 Project Type: Python Library</h3>
                <p><strong>📦 Standard Python package</strong></p>
                <ul>
                    <li>Installable via pip</li>
                    <li>Includes pytest for testing</li>
                    <li>Uses black, flake8 for linting</li>
                    <li>PyPI badges and documentation</li>
                    <li>setup.py and pyproject.toml</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Python CLI Tool":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🐍 Project Type: Python CLI Tool</h3>
                <p><strong>⚡ Command-line interface</strong></p>
                <ul>
                    <li>Uses Click for CLI framework</li>
                    <li>Installable as command-line tool</li>
                    <li>Includes help documentation</li>
                    <li>Cross-platform compatibility</li>
                    <li>Entry point configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "JavaScript/Node.js Package":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🟨 Project Type: JavaScript/Node.js Package</h3>
                <p><strong>📦 npm package</strong></p>
                <ul>
                    <li>Installable via npm</li>
                    <li>Uses Jest for testing</li>
                    <li>ESLint and Prettier for formatting</li>
                    <li>Modern ES6+ JavaScript</li>
                    <li>package.json configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Web Application":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🌐 Project Type: Web Application</h3>
                <p><strong>🚀 Full-stack web app</strong></p>
                <ul>
                    <li>Frontend and backend setup</li>
                    <li>Docker configuration</li>
                    <li>Deployment workflows</li>
                    <li>Modern web technologies</li>
                    <li>Database configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Data Science Project":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📊 Project Type: Data Science Project</h3>
                <p><strong>🔬 ML/Data analysis</strong></p>
                <ul>
                    <li>Jupyter notebook support</li>
                    <li>Data science dependencies</li>
                    <li>Visualization tools</li>
                    <li>Research-friendly structure</li>
                    <li>Model training setup</li>
                </ul>
            </body>
            </html>
            """
        else:  # Documentation Site
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📚 Project Type: Documentation Site</h3>
                <p><strong>📖 Static documentation</strong></p>
                <ul>
                    <li>Static site generator</li>
                    <li>Search functionality</li>
                    <li>Mobile-responsive design</li>
                    <li>Easy to maintain</li>
                    <li>Version control for docs</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_gitignore_help(self, gitignore: str) -> str:
        """Generate help content for gitignore"""
        custom_templates = [
            "C++", "C#", "Dart", "Go", "Java", "JavaScript", 
            "Kotlin", "PHP", "R", "Ruby", "Rust", "Scala", "Swift", "TypeScript"
        ]
        
        if gitignore == "None":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: None</h3>
                <p>No .gitignore file will be created. You can add one later to exclude files from version control.</p>
                <p><strong>Consider adding a gitignore if you have:</strong></p>
                <ul>
                    <li>Build artifacts or compiled files</li>
                    <li>Dependencies (node_modules, __pycache__)</li>
                    <li>IDE configuration files</li>
                    <li>Temporary or cache files</li>
                    <li>Sensitive configuration files</li>
                </ul>
            </body>
            </html>
            """
        elif gitignore in custom_templates:
            # Get sample content for custom templates
            sample_content = self._get_gitignore_sample(gitignore)
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                    pre {{ 
                        background-color: #f6f8fa; 
                        border: 1px solid #e1e4e8; 
                        border-radius: 6px; 
                        padding: 12px; 
                        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                        font-size: 11px;
                        line-height: 1.4;
                        margin: 12px 0;
                        overflow-x: auto;
                    }}
                    .sample-label {{ 
                        color: #586069; 
                        font-size: 12px; 
                        font-style: italic; 
                        margin-bottom: 8px; 
                    }}
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: {gitignore}</h3>
                <p><strong>🔧 Custom template (not in GitHub's library)</strong></p>
                <p>This will create a custom .gitignore file for {gitignore} projects with:</p>
                <ul>
                    <li>Empty .gitignore file with helpful comments</li>
                    <li>Suggested patterns you can uncomment as needed</li>
                    <li>Language-specific recommendations</li>
                    <li>Common build artifacts and dependencies</li>
                </ul>
                <p><strong>Note:</strong> Since {gitignore} isn't in GitHub's official template library, we create a custom file with commented suggestions that you can customize for your specific project needs.</p>
                
                <div class="sample-label">📋 Sample of the .gitignore file that will be created:</div>
                <pre>{sample_content}</pre>
            </body>
            </html>
            """
        else:
            # Get sample content for official templates
            sample_content = self._get_gitignore_sample(gitignore)
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                    pre {{ 
                        background-color: #f6f8fa; 
                        border: 1px solid #e1e4e8; 
                        border-radius: 6px; 
                        padding: 12px; 
                        font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                        font-size: 11px;
                        line-height: 1.4;
                        margin: 12px 0;
                        overflow-x: auto;
                    }}
                    .sample-label {{ 
                        color: #586069; 
                        font-size: 12px; 
                        font-style: italic; 
                        margin-bottom: 8px; 
                    }}
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: {gitignore}</h3>
                <p>This will create a .gitignore file using GitHub's official template for {gitignore} projects.</p>
                <p><strong>What it excludes:</strong></p>
                <ul>
                    <li>Build artifacts and compiled files</li>
                    <li>Dependencies and package managers</li>
                    <li>Temporary and cache files</li>
                    <li>IDE and editor files</li>
                    <li>OS-specific files</li>
                </ul>
                
                <div class="sample-label">📋 Sample of the .gitignore file that will be created:</div>
                <pre>{sample_content}</pre>
            </body>
            </html>
            """
    
    def _generate_topics_help(self, topics: List[str]) -> str:
        """Generate help content for topics"""
        if topics:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>🏷️ Topics: {', '.join(topics)}</h3>
                <p>These topics will help others discover your repository on GitHub and understand what it's about.</p>
                <p><strong>Benefits:</strong></p>
                <ul>
                    <li>Improves discoverability in searches</li>
                    <li>Shows up in topic-based browsing</li>
                    <li>Helps categorize your project</li>
                    <li>Makes it easier for others to find</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🏷️ Topics</h3>
                <p>Add topics to help others discover your repository. Use comma-separated values like "python, gui, qt".</p>
                <p><strong>Good topic examples:</strong></p>
                <ul>
                    <li>Programming language: python, javascript, rust</li>
                    <li>Framework: react, django, flask</li>
                    <li>Purpose: cli, gui, api, web</li>
                    <li>Domain: machine-learning, web-development</li>
                    <li>Technology: docker, kubernetes, aws</li>
                </ul>
            </body>
            </html>
            """
    
    def _get_gitignore_sample(self, template_name: str) -> str:
        """Get a sample of the gitignore template content (first ~10 lines)"""
        custom_templates = [
            "C++", "C#", "Dart", "Go", "Java", "JavaScript", 
            "Kotlin", "PHP", "R", "Ruby", "Rust", "Scala", "Swift", "TypeScript"
        ]
        
        if template_name in custom_templates:
            # Return sample for custom templates
            if template_name == "JavaScript":
                return """# .gitignore for JavaScript projects
# No files are ignored for JavaScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
..."""
            elif template_name == "TypeScript":
                return """# .gitignore for TypeScript projects
# No files are ignored for TypeScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
# *.tsbuildinfo
..."""
            elif template_name == "Java":
                return """# .gitignore for Java projects
# No files are ignored for Java projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# *.class
# *.jar
# *.war
# *.ear
# .gradle/
# build/
# out/
# .idea/
# *.iml
..."""
            elif template_name == "C++":
                return """# .gitignore for C++ projects
# No files are ignored for C++ projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# bin/
# obj/
# *.o
# *.a
# *.so
# *.dll
# *.exe
# CMakeFiles/
# CMakeCache.txt
..."""
            elif template_name == "C#":
                return """# .gitignore for C# projects
# No files are ignored for C# projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# obj/
# *.user
# *.suo
# *.cache
# *.dll
# *.exe
# *.pdb
# *.log
# .vs/
# packages/
..."""
            elif template_name == "Go":
                return """# .gitignore for Go projects
# No files are ignored for Go projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# pkg/
# *.exe
# *.exe~
# *.dll
# *.so
# *.dylib
# go.work
..."""
            elif template_name == "Rust":
                return """# .gitignore for Rust projects
# No files are ignored for Rust projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# Cargo.lock
# *.pdb
..."""
            elif template_name == "Python":
                return """# .gitignore for Python projects
# No files are ignored for Python projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# __pycache__/
# *.py[cod]
# *$py.class
# *.so
# .Python
# build/
# develop-eggs/
# dist/
# downloads/
# eggs/
# .eggs/
# lib/
# lib64/
# parts/
# sdist/
# var/
# wheels/
# *.egg-info/
# .installed.cfg
# *.egg
# MANIFEST
# .pytest_cache/
# .coverage
# .env
# .venv
# env/
# venv/
# ENV/
# env.bak/
# venv.bak/
..."""
            else:
                # Generic template for other languages
                return f"""# .gitignore for {template_name} projects
# No files are ignored for {template_name} projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# dist/
# .env
# *.log
# .cache/
# .tmp/
..."""
        else:
            # For official GitHub templates, try to get the actual content
            try:
                result = subprocess.run(
                    ['gh', 'api', f'gitignore/templates/{template_name}'],
                    capture_output=True, text=True, check=True
                )
                template_data = json.loads(result.stdout)
                content = template_data.get('source', '')
                
                # Take first ~10 lines and add ellipsis
                lines = content.split('\n')[:10]
                sample = '\n'.join(lines)
                if len(content.split('\n')) > 10:
                    sample += '\n...'
                
                return sample
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                # Fallback if we can't get the actual template
                return f"""# .gitignore for {template_name} projects
# This will use GitHub's official {template_name} template
# The actual content will be fetched from GitHub's template library
# when the repository is created.

# Common patterns typically included:
# Build artifacts and compiled files
# Dependencies and package managers
# Temporary and cache files
# IDE and editor files
# OS-specific files
..."""
    
    def _get_selected_visibility(self) -> str:
        """Get selected visibility from radio buttons"""
        if self.visibility_public_radio.isChecked():
            return "public"
        else:
            return "private"
    
    def _get_selected_license(self) -> str:
        """Get selected license from radio buttons"""
        if self.license_mit_radio.isChecked():
            return "MIT"
        elif self.license_apache_radio.isChecked():
            return "Apache 2.0"
        elif self.license_gpl_radio.isChecked():
            return "GPL 3.0"
        else:
            return "None"
    
    def _get_selected_project_type(self) -> str:
        """Get selected project type from radio buttons"""
        if self.project_type_other_radio.isChecked():
            return "Other"
        elif self.project_type_python_lib_radio.isChecked():
            return "Python Library"
        elif self.project_type_python_cli_radio.isChecked():
            return "Python CLI Tool"
        elif self.project_type_js_radio.isChecked():
            return "JavaScript/Node.js Package"
        elif self.project_type_web_radio.isChecked():
            return "Web Application"
        elif self.project_type_data_radio.isChecked():
            return "Data Science Project"
        elif self.project_type_docs_radio.isChecked():
            return "Documentation Site"
        else:
            return "Other"  # Default
    
    def update_readme_preview(self) -> None:
        """Update the README preview based on current settings"""
        try:
            # Import template system
            from templates import READMETemplate, get_project_type_by_name
            
            # Get current project configuration
            config = self.get_basic_config()
            
            # Get project type from radio buttons
            project_type_name = self._get_selected_project_type()
            project_type = get_project_type_by_name(project_type_name)
            config['project_type'] = project_type
            
            # Generate README content
            template = READMETemplate(config)
            readme_content = template.generate()
            
            # Update editor and preview
            self.readme_editor.setPlainText(readme_content)
            self.update_readme_preview_html(readme_content)
            
        except ImportError:
            # Fallback if template system is not available
            fallback_content = f"""# {self.repo_name_edit.text()}

            {self.description_edit.text() or 'A professional project created with RepoSpark.'}

## Installation

```bash
# Install the project
git clone https://github.com/{config.get('username', 'username')}/{self.repo_name_edit.text()}.git
cd {self.repo_name_edit.text()}
```

## Usage

See the documentation for usage examples.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the {self.license_combo.currentText()} License.
"""
            self.readme_editor.setPlainText(fallback_content)
            self.update_readme_preview_html(fallback_content)
    
    def update_readme_preview_html(self, markdown_content: str):
        """Convert markdown to HTML for preview using GitHub-flavored markdown"""
        try:
            import markdown
            
            # Configure markdown with GitHub-flavored extensions
            md = markdown.Markdown(extensions=[
                'markdown.extensions.fenced_code',  # GitHub-style code blocks
                'markdown.extensions.tables',       # Tables
                'markdown.extensions.nl2br',        # Line breaks
                'markdown.extensions.sane_lists',   # Better list handling
                'markdown.extensions.codehilite',   # Syntax highlighting
                'markdown.extensions.toc',          # Table of contents
                'markdown.extensions.attr_list',    # Attribute lists
                'markdown.extensions.def_list',     # Definition lists
                'markdown.extensions.footnotes',    # Footnotes
                'markdown.extensions.abbr',         # Abbreviations
                'markdown.extensions.md_in_html',   # Markdown in HTML
            ])
            
            # Convert markdown to HTML
            html_content = md.convert(markdown_content)
            
            # Add GitHub-style CSS
            styled_html = f"""
            <html>
            <head>
                <style>
                    /* GitHub-style CSS */
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
                        font-size: 14px;
                        line-height: 1.5;
                        color: #24292f;
                        background-color: #ffffff;
                        padding: 20px;
                        margin: 0;
                    }}
                    
                    /* Headers */
                    h1, h2, h3, h4, h5, h6 {{
                        margin-top: 24px;
                        margin-bottom: 16px;
                        font-weight: 600;
                        line-height: 1.25;
                        color: #24292f;
                    }}
                    
                    h1 {{
                        font-size: 2em;
                        border-bottom: 1px solid #d0d7de;
                        padding-bottom: 0.3em;
                    }}
                    
                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #d0d7de;
                        padding-bottom: 0.3em;
                    }}
                    
                    h3 {{
                        font-size: 1.25em;
                    }}
                    
                    /* Paragraphs and spacing */
                    p {{
                        margin-top: 0;
                        margin-bottom: 16px;
                    }}
                    
                    /* Lists */
                    ul, ol {{
                        margin-top: 0;
                        margin-bottom: 16px;
                        padding-left: 2em;
                    }}
                    
                    li {{
                        margin-top: 0.25em;
                    }}
                    
                    /* Code */
                    code {{
                        padding: 0.2em 0.4em;
                        margin: 0;
                        font-size: 85%;
                        background-color: rgba(175, 184, 193, 0.2);
                        border-radius: 6px;
                        font-family: ui-monospace, SFMono-Regular, 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace;
                    }}
                    
                    /* Code blocks */
                    pre {{
                        padding: 16px;
                        overflow: auto;
                        font-size: 85%;
                        line-height: 1.45;
                        background-color: #f6f8fa;
                        border-radius: 6px;
                        border: 1px solid #d0d7de;
                        margin-top: 0;
                        margin-bottom: 16px;
                    }}
                    
                    pre code {{
                        padding: 0;
                        margin: 0;
                        background-color: transparent;
                        border: 0;
                        font-size: 100%;
                        word-break: normal;
                        white-space: pre;
                    }}
                    
                    /* Links */
                    a {{
                        color: #0969da;
                        text-decoration: none;
                    }}
                    
                    a:hover {{
                        text-decoration: underline;
                    }}
                    
                    /* Blockquotes */
                    blockquote {{
                        padding: 0 1em;
                        color: #656d76;
                        border-left: 0.25em solid #d0d7de;
                        margin: 0 0 16px 0;
                    }}
                    
                    /* Tables */
                    table {{
                        border-spacing: 0;
                        border-collapse: collapse;
                        margin-top: 0;
                        margin-bottom: 16px;
                        width: 100%;
                    }}
                    
                    th, td {{
                        padding: 6px 13px;
                        border: 1px solid #d0d7de;
                    }}
                    
                    th {{
                        font-weight: 600;
                        background-color: #f6f8fa;
                    }}
                    
                    /* Horizontal rules */
                    hr {{
                        height: 0.25em;
                        padding: 0;
                        margin: 24px 0;
                        background-color: #d0d7de;
                        border: 0;
                    }}
                    
                    /* Images */
                    img {{
                        max-width: 100%;
                        height: auto;
                        box-sizing: content-box;
                    }}
                    
                    /* Badges */
                    img[src*="shields.io"] {{
                        display: inline-block;
                        margin: 2px;
                    }}
                    
                    /* Task lists */
                    .task-list-item {{
                        list-style-type: none;
                    }}
                    
                    .task-list-item input {{
                        margin: 0 0.2em 0.25em -1.4em;
                        vertical-align: middle;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.readme_preview.setHtml(styled_html)
            
        except ImportError:
            # Fallback to simple conversion if markdown library is not available
            html_content = markdown_content.replace('\n', '<br>')
            html_content = html_content.replace('```', '<pre><code>')
            html_content = html_content.replace('`', '<code>')
            html_content = html_content.replace('# ', '<h1>')
            html_content = html_content.replace('## ', '<h2>')
            html_content = html_content.replace('### ', '<h3>')
            html_content = html_content.replace('- ', '<li>')
            
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; }}
                    h1 {{ color: #24292e; border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3em; }}
                    h2 {{ color: #24292e; border-bottom: 1px solid #e1e4e8; padding-bottom: 0.3em; }}
                    h3 {{ color: #24292e; }}
                    code {{ background-color: #f6f8fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background-color: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; }}
                    li {{ margin: 4px 0; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.readme_preview.setHtml(styled_html)
    
    def on_readme_editor_changed(self):
        """Handle README editor content changes"""
        content = self.readme_editor.toPlainText()
        self.update_readme_preview_html(content)
    
    def update_scaffold_tree(self) -> None:
        """Update the scaffold tree based on current settings"""
        self.scaffold_tree.clear()
        
        if not self.create_scaffold_check.isChecked():
            # Show empty state
            root_item = QTreeWidgetItem(self.scaffold_tree)
            root_item.setText(0, "project-name/")
            root_item.setIcon(0, self.scaffold_tree.style().standardIcon(self.scaffold_tree.style().StandardPixmap.SP_DirIcon))
            return
        
        # Create root project folder
        project_name = self.repo_name_edit.text().strip() if self.repo_name_edit.text().strip() else "project-name"
        root_item = self.scaffold_tree.add_folder_item(None, f"{project_name}/", "root")
        
        # Add standard directories with specific types
        src_folder = self.scaffold_tree.add_folder_item(root_item, "src/", "src")
        tests_folder = self.scaffold_tree.add_folder_item(root_item, "tests/", "tests")
        docs_folder = self.scaffold_tree.add_folder_item(root_item, "docs/", "docs")
        github_folder = self.scaffold_tree.add_folder_item(root_item, ".github/", "github")
        
        # Add files in root with specific types
        self.scaffold_tree.add_file_item(root_item, "README.md", "readme")
        self.scaffold_tree.add_file_item(root_item, "CHANGELOG.md", "changelog")
        self.scaffold_tree.add_file_item(root_item, "CONTRIBUTING.md", "contributing")
        self.scaffold_tree.add_file_item(root_item, "CODE_OF_CONDUCT.md", "conduct")
        self.scaffold_tree.add_file_item(root_item, "SECURITY.md", "security")
        self.scaffold_tree.add_file_item(root_item, ".gitattributes", "config")
        
        # Add .editorconfig if enabled
        if self.create_editorconfig_check.isChecked():
            self.scaffold_tree.add_file_item(root_item, ".editorconfig", "config")
        
        # Add project-specific files based on project type
        project_type = self._get_selected_project_type()
        self._add_project_specific_files(root_item, src_folder, tests_folder, project_type)
        
        # Add files in .github folder
        self.scaffold_tree.add_file_item(github_folder, "ISSUE_TEMPLATE.md", "issue")
        self.scaffold_tree.add_file_item(github_folder, "PULL_REQUEST_TEMPLATE.md", "pr")
        
        # Add files in docs folder
        self.scaffold_tree.add_file_item(docs_folder, "index.md", "docs")
        
        # Add files in tests folder
        self.scaffold_tree.add_file_item(tests_folder, "test_placeholder.txt", "test")
        
        # Expand the root item
        self.scaffold_tree.expandItem(root_item)
    
    def _add_project_specific_files(self, root_item: QTreeWidgetItem, src_folder: QTreeWidgetItem, tests_folder: QTreeWidgetItem, project_type: str) -> None:
        """Add project-specific files based on the selected project type"""
        if project_type == "Python Library":
            # Python library specific files
            self.scaffold_tree.add_file_item(root_item, "pyproject.toml", "config")
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(root_item, "setup.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_main.py", "test")
            
        elif project_type == "Python CLI Tool":
            # Python CLI specific files
            self.scaffold_tree.add_file_item(root_item, "pyproject.toml", "config")
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(src_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "cli.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_cli.py", "test")
            
        elif project_type == "JavaScript/Node.js Package":
            # JavaScript package specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "package-lock.json", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.js", "config")
            self.scaffold_tree.add_file_item(tests_folder, "index.test.js", "test")
            
        elif project_type == "Web Application":
            # Web application specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "webpack.config.js", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.html", "config")
            self.scaffold_tree.add_file_item(src_folder, "app.js", "config")
            self.scaffold_tree.add_file_item(src_folder, "styles.css", "config")
            self.scaffold_tree.add_file_item(tests_folder, "app.test.js", "test")
            
        elif project_type == "Data Science Project":
            # Data science specific files
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(root_item, "environment.yml", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "main.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "data_analysis.ipynb", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_analysis.py", "test")
            
        elif project_type == "Documentation Site":
            # Documentation site specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "mkdocs.yml", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.html", "config")
            self.scaffold_tree.add_file_item(src_folder, "styles.css", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_docs.py", "test")
    
    def get_basic_config(self) -> Dict[str, Any]:
        """
        Get basic configuration for templates.
        
        Returns:
            Dictionary containing basic repository configuration
        """
        user_info = GitHubAPI.get_user_info()
        
        return {
            'repo_name': self.repo_name_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'license': self._get_selected_license().lower().replace(" ", "-") if self._get_selected_license() != "None" else "",
            'topics': [t.strip() for t in self.topics_edit.text().split(',') if t.strip()],
            'username': user_info['login'] if user_info else "username"
        }
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get complete configuration from UI for repository creation.
        
        Returns:
            Dictionary containing all configuration needed to create repository
        """
        user_info = GitHubAPI.get_user_info()
        
        return {
            'repo_name': self.repo_name_edit.text().strip(),
            'description': self.description_edit.text().strip(),
            'visibility': self._get_selected_visibility(),
            'gitignore_template': self.gitignore_combo.currentText() if self.gitignore_combo.currentText() != "None" else "",
            'license': self._get_selected_license().lower().replace(" ", "-") if self._get_selected_license() != "None" else "",
            'topics': [t.strip() for t in self.topics_edit.text().split(',') if t.strip()],
            'remote_type': "https" if self.remote_https_radio.isChecked() else "ssh",
            'create_scaffold': self.create_scaffold_check.isChecked(),
            'create_editorconfig': self.create_editorconfig_check.isChecked(),
            'open_browser': self.open_browser_check.isChecked(),
            'username': user_info['login'] if user_info else "",
            'project_type': self._get_selected_project_type(),
            'readme_content': self.readme_editor.toPlainText() if hasattr(self, 'readme_editor') else ""
        }
    
    def create_repository(self) -> None:
        """Start repository creation process"""
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", error_msg)
            return
        
        # Get configuration
        config = self.get_config()
        
        # Confirm creation
        msg = f"""Create repository '{config['repo_name']}'?

Repository Details:
• Name: {config['repo_name']}
• Visibility: {config['visibility']}
• Description: {config['description'] or 'None'}
• Gitignore: {config['gitignore_template'] or 'None'}
• License: {config['license'] or 'None'}
• Topics: {', '.join(config['topics']) if config['topics'] else 'None'}
• Remote: {config['remote_type']}
• Scaffold: {'Yes' if config['create_scaffold'] else 'No'}

This will create the repository on GitHub and set up the local git repository."""
        
        reply = QMessageBox.question(
            self, "Confirm Creation", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Start worker
        self.worker = RepositoryWorker(config)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_creation_finished)
        
        # Update UI
        self.create_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Creating repository...")
        
        self.worker.start()
    
    def update_progress(self, message: str) -> None:
        """
        Update progress message in a thread-safe manner.
        
        This method can be called from any thread and will safely update
        the UI using QMetaObject.invokeMethod for explicit thread safety.
        
        Args:
            message: Progress message to display
        """
        # Use QMetaObject.invokeMethod for explicit thread-safe UI updates
        QMetaObject.invokeMethod(
            self.status_label,
            "setText",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, message)
        )
    
    def on_creation_finished(self, success: bool, message: str) -> None:
        """
        Handle repository creation completion in a thread-safe manner.
        
        This method is called from the worker thread and uses thread-safe
        methods to update the UI.
        
        Args:
            success: Whether the operation succeeded
            message: Completion message
        """
        # Use thread-safe UI updates
        QMetaObject.invokeMethod(
            self.progress_bar,
            "setVisible",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(bool, False)
        )
        QMetaObject.invokeMethod(
            self.create_button,
            "setEnabled",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(bool, True)
        )
        QMetaObject.invokeMethod(
            self.cancel_button,
            "setEnabled",
            Qt.ConnectionType.QueuedConnection,
            Q_ARG(bool, False)
        )
        
        if success:
            QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Repository created successfully!")
            )
            # Show message box in main thread
            QMetaObject.invokeMethod(
                self,
                "_show_success_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, message)
            )
            
            # Open in browser if requested
            config = self.get_config()
            if config.get('open_browser', False):
                try:
                    subprocess.run([
                        'gh', 'repo', 'view', 
                        f"{config['username']}/{config['repo_name']}", 
                        '--web'
                    ])
                except subprocess.CalledProcessError:
                    pass
        else:
            QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Repository creation failed")
            )
            # Show error message box in main thread
            QMetaObject.invokeMethod(
                self,
                "_show_error_message",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, message)
            )
    
    def _show_success_message(self, message: str) -> None:
        """Thread-safe helper to show success message box"""
        QMessageBox.information(self, "Success", message)
    
    def _show_error_message(self, message: str) -> None:
        """Thread-safe helper to show error message box"""
        QMessageBox.critical(self, "Error", message)
    
    def cancel_operation(self) -> None:
        """Cancel the current operation"""
        if self.worker and self.worker.isRunning():
            # Use graceful shutdown instead of terminate()
            self.worker._should_stop = True
            self.status_label.setText("Cancelling operation...")
            # Wait for thread to finish gracefully (with timeout)
            if not self.worker.wait(3000):  # 3 second timeout
                # If still running, force termination as last resort
                self.worker.terminate()
                self.worker.wait()
        
        self.progress_bar.setVisible(False)
        self.create_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Operation cancelled")
    
    def _create_menu_bar(self) -> None:
        """
        Create menu bar with Help menu containing About dialog.
        """
        menu_bar = self.menuBar()
        
        # Create Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Add About action
        about_action = help_menu.addAction("&About RepoSpark...")
        about_action.triggered.connect(self.show_about_dialog)
        about_action.setShortcut("F1")  # F1 for help/about
        
        # Add About Qt action (standard Qt action)
        help_menu.addSeparator()
        about_qt_action = help_menu.addAction("About &Qt...")
        about_qt_action.triggered.connect(lambda: QMessageBox.aboutQt(self))
    
    def show_about_dialog(self) -> None:
        """
        Show About dialog with application information and version.
        """
        from . import __version__
        
        about_text = f"""
        <h2>RepoSpark</h2>
        <p><b>Version {__version__}</b></p>
        <p>A PySide6 GUI application for creating GitHub repositories</p>
        <p>Author: Rich Lewis</p>
        <p>GitHub: <a href="https://github.com/RichLewis007">@RichLewis007</a></p>
        <hr>
        <p>RepoSpark helps you create comprehensive GitHub repositories with:</p>
        <ul>
            <li>Customizable project scaffolds</li>
            <li>README.md generation</li>
            <li>License and gitignore templates</li>
            <li>Topic management</li>
            <li>And much more!</li>
        </ul>
        <p>Built with PySide6 6.7.3</p>
        <p>Python {sys.version.split()[0]}</p>
        """
        
        QMessageBox.about(
            self,
            "About RepoSpark",
            about_text
        )
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop focus timer
        if self.focus_timer:
            self.focus_timer.stop()
        
        # Cancel any running operations
        if self.worker and self.worker.isRunning():
            self.worker._should_stop = True
            if not self.worker.wait(2000):  # 2 second timeout
                self.worker.terminate()
                self.worker.wait()
        
        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("RepoSpark")
    from . import __version__
    app.setApplicationVersion(__version__)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = RepoSparkGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
