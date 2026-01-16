"""
RepoSpark - Core Services Module
File: src/repospark/core/__init__.py
Version: 0.3.0
Description: Core business logic services for GitHub API, Git operations, and scaffold generation.
Created: 2025-01-16
Author: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

from .git_operations import GitOperations
from .github_api import GitHubAPI
from .scaffold_generator import ScaffoldGenerator

__all__ = [
    "GitHubAPI",
    "GitOperations",
    "ScaffoldGenerator",
]
