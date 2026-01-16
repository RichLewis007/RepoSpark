"""
RepoSpark - Git Operations Service
File: src/repospark/core/git_operations.py
Version: 0.3.0
Description: Handles Git repository operations (init, commit, remote, push).
Created: 2025-01-16
Maintainer: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

# Author: Rich Lewis - GitHub: @RichLewis007

import logging
import shlex
import subprocess
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


class GitOperations:
    """
    Handles Git operations for repository initialization and management.
    
    This class provides static methods for common Git operations needed
    when creating and setting up a new repository.
    """
    
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
        """
        Push to remote repository.
        
        Args:
            branch: Branch name to push (default: 'main')
            
        Returns:
            True if push was successful, False otherwise
        """
        try:
            subprocess.run(['git', 'push', '-u', 'origin', branch], capture_output=True, text=True, check=True)
            logger.info(f"Successfully pushed to remote branch: {branch}")
            return True
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            logger.error(f"Error pushing to remote: {error_msg}")
            return False
        except FileNotFoundError:
            logger.error("Git not found in PATH")
            return False
    
    @staticmethod
    def get_current_branch() -> str:
        """
        Get current branch name.
        
        Returns:
            Current branch name, or 'main' if unable to determine
        """
        try:
            result = subprocess.run(
                ['git', 'symbolic-ref', '--short', 'HEAD'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'main'
