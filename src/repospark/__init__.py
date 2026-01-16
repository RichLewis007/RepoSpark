"""
RepoSpark - A PySide6 application to create GitHub repositories
"""
# Author: Rich Lewis - GitHub: @RichLewis007

# Define version first to avoid circular imports
__version__ = "0.3.0"

# Import from new modular structure
from .core.git_operations import GitOperations
from .core.github_api import GitHubAPI
from .core.scaffold_generator import ScaffoldGenerator
from .main import main
from .ui.main_window import RepoSparkGUI

__all__ = [
    "GitHubAPI",
    "GitOperations",
    "ScaffoldGenerator",
    "RepoSparkGUI",
    "main",
]
