"""
RepoSpark - Repository Worker
File: src/repospark/workers/repository_worker.py
Version: 0.3.0
Description: Background worker thread for repository creation operations.
Created: 2025-01-16
Author: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

import json
import logging
import os
import subprocess
from typing import Any

from PySide6.QtCore import QThread, Signal

from ..core.git_operations import GitOperations
from ..core.github_api import GitHubAPI
from ..core.scaffold_generator import ScaffoldGenerator

# Configure logging
logger = logging.getLogger(__name__)


class RepositoryWorker(QThread):
    """
    Background worker for repository creation operations.

    This worker runs repository creation tasks in a separate thread to avoid
    blocking the UI. It emits progress signals and a finished signal when complete.

    Attributes:
        progress: Signal emitted with progress messages (str)
        finished: Signal emitted when operation completes (bool, str)
        config: Configuration dictionary for repository creation
        _should_stop: Flag to indicate cancellation request
    """

    progress = Signal(str)
    finished = Signal(bool, str)

    def __init__(self, config: dict[str, Any]):
        """
        Initialize the repository worker.

        Args:
            config: Dictionary containing repository configuration:
                - repo_name: Name of the repository
                - repo_location: Directory where repository will be created
                - visibility: 'public' or 'private'
                - description: Repository description
                - gitignore_template: Gitignore template name
                - license: License identifier
                - topics: List of topic strings
                - username: GitHub username
                - remote_type: 'https' or 'ssh'
                - create_scaffold: Whether to create project scaffold
                - create_editorconfig: Whether to create .editorconfig
                - readme_content: Custom README content
        """
        super().__init__()
        self.config = config
        self._should_stop = False

    def cancel(self) -> None:
        """
        Request cancellation of the current operation.

        Sets the cancellation flag which is checked at various points
        during the repository creation process.
        """
        self._should_stop = True
        logger.info("Repository worker cancellation requested")

    def run(self) -> None:
        """
        Execute the repository creation workflow.

        This method performs the following steps:
        1. Create project scaffold (if requested)
        2. Create GitHub repository
        3. Handle gitignore templates
        4. Initialize git repository
        5. Add and commit files
        6. Add remote origin
        7. Push to GitHub
        8. Set repository topics

        Emits progress signals throughout and a finished signal at the end.
        """
        try:
            # Check if we should stop
            if self._should_stop:
                self.finished.emit(False, "Operation cancelled")
                return

            # Change to repository location directory
            repo_location = self.config.get("repo_location", os.getcwd())
            if not os.path.exists(repo_location):
                os.makedirs(repo_location, exist_ok=True)

            # Store original directory to restore later
            original_cwd = os.getcwd()
            os.chdir(repo_location)

            try:
                # Check if directory is empty and create scaffold if needed
                if self.config.get("create_scaffold", False):
                    if self._should_stop:
                        self.finished.emit(False, "Operation cancelled")
                        return
                    self.progress.emit("Creating project scaffold...")
                    ScaffoldGenerator.create_scaffold(
                        self.config["repo_name"],
                        self.config.get("create_editorconfig", True),
                        self.config.get("readme_content", ""),
                    )

                # Handle custom gitignore templates
                gitignore_template = self.config.get("gitignore_template", "")
                custom_gitignore_templates = [
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
                    "TypeScript",
                ]

                # Create GitHub repository
                if self._should_stop:
                    self.finished.emit(False, "Operation cancelled")
                    return
                self.progress.emit("Creating GitHub repository...")
                if not GitHubAPI.create_repository(
                    self.config["repo_name"],
                    self.config["visibility"],
                    self.config.get("description", ""),
                    gitignore_template
                    if gitignore_template not in custom_gitignore_templates
                    else "",
                    self.config.get("license", ""),
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
                if not os.path.exists(".git"):
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
                    self.config["username"],
                    self.config["repo_name"],
                    self.config.get("remote_type", "https"),
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
                if self.config.get("topics"):
                    self.progress.emit("Setting repository topics...")
                    if not GitHubAPI.set_topics(
                        self.config["username"], self.config["repo_name"], self.config["topics"]
                    ):
                        self.progress.emit("Warning: Failed to set topics")

                self.finished.emit(
                    True, f"Repository '{self.config['repo_name']}' created successfully!"
                )
            except Exception as e:
                logger.error(f"Error creating repository: {str(e)}")
                self.finished.emit(False, f"Error: {str(e)}")
            finally:
                # Restore original directory
                os.chdir(original_cwd)
        except Exception as e:
            logger.error(f"Error in repository creation: {str(e)}")
            self.finished.emit(False, f"Error: {str(e)}")

    def _create_custom_gitignore(self, template_name: str) -> None:
        """
        Create a custom .gitignore file for languages/frameworks not in GitHub's library.

        Args:
            template_name: Name of the template (e.g., "JavaScript", "Python")
        """
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

        with open(".gitignore", "w", encoding="utf-8") as f:
            f.write(gitignore_content)

    def _fetch_gitignore_template(self, template_name: str) -> None:
        """
        Fetch gitignore template from GitHub API and create local file.

        Args:
            template_name: Name of the gitignore template to fetch
        """
        try:
            result = subprocess.run(
                ["gh", "api", f"gitignore/templates/{template_name}"],
                capture_output=True,
                text=True,
                check=True,
            )
            template_data = json.loads(result.stdout)
            content = template_data.get("source", "")

            # Only create if we got content and file doesn't exist
            if content and not os.path.exists(".gitignore"):
                with open(".gitignore", "w", encoding="utf-8") as f:
                    f.write(content)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            # If we can't fetch it, that's okay - GitHub already created it in the repo
            pass
