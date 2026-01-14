"""
RepoSpark - A PySide6 application to create GitHub repositories
"""
# Author: Rich Lewis - GitHub: @RichLewis007

from .app import (
    GitHubAPI,
    GitOperations,
    ScaffoldGenerator,
    RepoSparkGUI,
    main,
)

__all__ = [
    'GitHubAPI',
    'GitOperations',
    'ScaffoldGenerator',
    'RepoSparkGUI',
    'main',
]

__version__ = '0.2.0'
