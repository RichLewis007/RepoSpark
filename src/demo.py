#!/usr/bin/env python3
"""
Demo script for RepoSpark
This script launches the application with sample data pre-filled for demonstration
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.repospark import RepoSparkGUI as RepoSpark


class DemoWindow(RepoSpark):
    """Demo version of RepoSpark with pre-filled sample data"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RepoSpark - Demo Mode")
        self.load_demo_data()
    
    def load_demo_data(self):
        """Load demo data into the application fields"""
        # Set sample repository data
        self.repo_name_edit.setText("demo-project")
        self.description_edit.setText("A sample project created with RepoSpark")
        
        # Set visibility to public
        self.visibility_combo.setCurrentText("Public")
        
        # Set gitignore template to Python
        python_index = self.gitignore_combo.findText("Python")
        if python_index >= 0:
            self.gitignore_combo.setCurrentIndex(python_index)
        
        # Set license to MIT
        self.license_combo.setCurrentText("MIT")
        
        # Set sample topics
        self.topics_edit.setText("python, demo, pyside6")
        
        # Set remote type to HTTPS
        self.remote_https_radio.setChecked(True)
        
        # Enable scaffold creation
        self.create_scaffold_check.setChecked(True)
        self.create_editorconfig_check.setChecked(True)
        
        # Enable browser opening
        self.open_browser_check.setChecked(True)
        
        # Update status
        self.status_label.setText("Demo mode - Sample data loaded")
    
    def create_repository(self):
        """Override to show demo message instead of creating actual repository"""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.information(
            self,
            "Demo Mode",
            "This is a demo of RepoSpark!\n\n"
            "In a real scenario, this would create a GitHub repository with the following settings:\n\n"
            f"• Repository: {self.repo_name_edit.text()}\n"
            f"• Description: {self.description_edit.text()}\n"
            f"• Visibility: {self.visibility_combo.currentText()}\n"
            f"• Gitignore: {self.gitignore_combo.currentText()}\n"
            f"• License: {self.license_combo.currentText()}\n"
            f"• Topics: {self.topics_edit.text()}\n"
            f"• Remote: {self.remote_combo.currentText()}\n"
            f"• Scaffold: {'Yes' if self.create_scaffold_check.isChecked() else 'No'}\n\n"
            "To create actual repositories, run the main application with proper GitHub authentication."
        )


def main():
    """Main demo function"""
    app = QApplication(sys.argv)
    app.setApplicationName("RepoSpark Demo")
    app.setApplicationVersion("1.0.0")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show demo window
    window = DemoWindow()
    window.show()
    
    # Show welcome message after a short delay
    def show_welcome():
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            window,
                    "Welcome to RepoSpark Demo!",
        "Welcome to the RepoSpark demonstration!\n\n"
            "This demo shows the interface with sample data pre-filled.\n"
            "You can explore all the tabs and options.\n\n"
            "Note: This is a demo mode - no actual repositories will be created.\n\n"
            "To use the real application:\n"
            "1. Install dependencies: uv sync\n"
            "2. Authenticate with GitHub: gh auth login\n"
            "3. Run: uv run repospark or ./run_repospark.sh"
        )
    
    QTimer.singleShot(500, show_welcome)
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
