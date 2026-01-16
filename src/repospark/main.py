"""
RepoSpark - Application Entry Point
File: src/repospark/main.py
Version: 0.3.0
Description: Main application entry point that initializes and runs RepoSpark.
Created: 2025-01-16
Maintainer: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

# Author: Rich Lewis - GitHub: @RichLewis007

import sys

from PySide6.QtWidgets import QApplication

from . import __version__
from .ui.main_window import RepoSparkGUI


def main() -> None:
    """
    Main application entry point.
    
    Initializes the QApplication, sets application metadata, creates the main window,
    and starts the event loop.
    """
    app = QApplication(sys.argv)
    app.setApplicationName("RepoSpark")
    app.setApplicationVersion(__version__)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    window = RepoSparkGUI()
    window.show()
    
    # Run application
    sys.exit(app.exec())
