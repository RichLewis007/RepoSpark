"""
RepoSpark - GitHub API Service
File: src/repospark/core/github_api.py
Version: 0.3.0
Description: Handles all GitHub API operations via GitHub CLI (gh).
Created: 2025-01-16
Maintainer: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

# Author: Rich Lewis - GitHub: @RichLewis007

import json
import logging
import shlex
import subprocess
from typing import List, Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


class GitHubAPI:
    """
    Handles GitHub API operations via GitHub CLI.
    
    This class provides static methods for interacting with GitHub through
    the GitHub CLI (gh) tool. All operations use subprocess calls to gh commands.
    """
    
    @staticmethod
    def get_user_info() -> Optional[Dict[str, Any]]:
        """
        Get current GitHub user information.
        
        Returns:
            Dictionary containing user information (login, name, email, etc.)
            or None if the request fails or user is not authenticated.
        """
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
        """
        Get available gitignore templates from GitHub.
        
        Returns:
            List of available gitignore template names.
            Returns empty list if the request fails.
        """
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
        cmd = ['gh', 'repo', 'create', name, f'--{visibility}']
        
        if description:
            cmd.extend(['--description', description])
        if gitignore_template:
            cmd.extend(['--gitignore', gitignore_template])
        if license:
            cmd.extend(['--license', license])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
