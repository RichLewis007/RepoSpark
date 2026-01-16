"""
RepoSpark - GitHub API Service
File: src/repospark/core/github_api.py
Version: 0.3.0
Description: Handles all GitHub API operations via GitHub CLI (gh).
Created: 2025-01-16
Author: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

import json
import logging
import subprocess
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)


class GitHubAPI:
    """
    Handles GitHub API operations via GitHub CLI.

    This class provides static methods for interacting with GitHub through
    the GitHub CLI (gh) tool. All operations use subprocess calls to gh commands.
    """
    
    # Cache for gitignore templates list (class-level cache)
    _gitignore_templates_cache: list[str] | None = None

    @staticmethod
    def get_user_info() -> dict[str, Any] | None:
        """
        Get current GitHub user information.

        Returns:
            Dictionary containing user information (login, name, email, etc.)
            or None if the request fails or user is not authenticated.
        """
        try:
            result = subprocess.run(
                ["gh", "api", "user"], capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            return None

    @staticmethod
    def get_gitignore_templates() -> list[str]:
        """
        Get available gitignore templates from GitHub.
        
        Templates are cached after the first fetch to avoid repeated API calls.
        The cache persists for the lifetime of the application.
        
        If a fetch fails but a cached list exists, the cached list is returned.
        This ensures the application continues to work even if GitHub is temporarily
        unavailable after the initial successful fetch.

        Returns:
            List of available gitignore template names.
            Returns empty list only if the request fails and no cache exists.
        """
        # Return cached templates if available (even if fetch fails)
        if GitHubAPI._gitignore_templates_cache is not None:
            return GitHubAPI._gitignore_templates_cache
        
        # Fetch templates from GitHub (only if no cache exists)
        try:
            result = subprocess.run(
                ["gh", "api", "gitignore/templates"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,  # 5 second timeout to prevent hanging
            )
            templates = json.loads(result.stdout)
            # Cache the result
            GitHubAPI._gitignore_templates_cache = templates
            logger.info(f"Loaded {len(templates)} gitignore templates from GitHub")
            return templates
        except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Failed to fetch gitignore templates: {e}")
            # If we have a cached list from a previous successful fetch, use it
            if GitHubAPI._gitignore_templates_cache is not None:
                logger.info("Using cached gitignore templates due to fetch failure")
                return GitHubAPI._gitignore_templates_cache
            # Only return empty list if we have no cache at all
            logger.error("No cached templates available and fetch failed")
            return []

    @staticmethod
    def create_repository(
        name: str,
        visibility: str,
        description: str = "",
        gitignore_template: str = "",
        license: str = "",
    ) -> bool:
        """
        Create a new GitHub repository.

        Args:
            name: Repository name
            visibility: 'public' or 'private'
            description: Repository description (optional)
            gitignore_template: Gitignore template name (optional)
            license: License identifier (optional)

        Returns:
            True if repository was created successfully, False otherwise
        """
        cmd = ["gh", "repo", "create", name, f"--{visibility}"]

        if description:
            cmd.extend(["--description", description])
        if gitignore_template:
            cmd.extend(["--gitignore", gitignore_template])
        if license:
            cmd.extend(["--license", license])

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Successfully created repository: {name}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error creating repository: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("GitHub CLI (gh) not found in PATH")
            return False

    @staticmethod
    def set_topics(username: str, repo_name: str, topics: list[str]) -> bool:
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

        try:
            topics_json = json.dumps(topics)
            subprocess.run(
                [
                    "gh",
                    "api",
                    "-X",
                    "PATCH",
                    f"repos/{username}/{repo_name}",
                    "-F",
                    f"topics={topics_json}",
                    "-H",
                    "Accept: application/vnd.github.mercy-preview+json",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
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
