#!/usr/bin/env python3
"""
Test script for RepoSpark components
This script tests the application without requiring actual GitHub operations
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from repospark import GitHubAPI, GitOperations, ScaffoldGenerator, RepoSparkGUI
from PySide6.QtWidgets import QApplication


def test_github_api_mock():
    """Test GitHub API with mocked responses"""
    print("Testing GitHub API with mocked responses...")
    
    # Mock successful user info response
    mock_user_info = {
        "login": "testuser",
        "id": 12345,
        "name": "Test User"
    }
    
    with patch('subprocess.run') as mock_run:
        # Mock successful API call
        mock_result = MagicMock()
        mock_result.stdout = '{"login": "testuser", "id": 12345, "name": "Test User"}'
        mock_run.return_value = mock_result
        
        user_info = GitHubAPI.get_user_info()
        assert user_info == mock_user_info
        print("✅ GitHub API user info test passed")
    
    # Mock gitignore templates
    mock_templates = ["Python", "Node", "Java", "C++"]
    
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.stdout = '["Python", "Node", "Java", "C++"]'
        mock_run.return_value = mock_result
        
        templates = GitHubAPI.get_gitignore_templates()
        assert templates == mock_templates
        print("✅ GitHub API gitignore templates test passed")


def test_scaffold_generator():
    """Test scaffold generation"""
    print("Testing scaffold generation...")
    
    # Create a temporary directory for testing
    import tempfile
    import shutil
    
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Test scaffold creation
            ScaffoldGenerator.create_scaffold("test-repo", create_editorconfig=True)
            
            # Check if files were created
            expected_files = [
                'README.md',
                'CHANGELOG.md',
                'CONTRIBUTING.md',
                'CODE_OF_CONDUCT.md',
                'SECURITY.md',
                '.gitattributes',
                '.editorconfig'
            ]
            
            expected_dirs = ['src', 'tests', 'docs', '.github']
            
            for file in expected_files:
                assert os.path.exists(file), f"File {file} was not created"
            
            for dir_name in expected_dirs:
                assert os.path.isdir(dir_name), f"Directory {dir_name} was not created"
            
            # Check README content
            with open('README.md', 'r') as f:
                content = f.read()
                assert "test-repo" in content
                assert "RepoSpark" in content
            
            print("✅ Scaffold generation test passed")
            
        finally:
            os.chdir(original_cwd)


def test_gui_creation():
    """Test GUI creation and basic functionality"""
    print("Testing GUI creation...")
    
    app = QApplication(sys.argv)
    
    # Mock GitHub API responses
    with patch('repospark.GitHubAPI.get_user_info') as mock_user_info, \
         patch('repospark.GitHubAPI.get_gitignore_templates') as mock_templates:
        
        mock_user_info.return_value = {"login": "testuser"}
        mock_templates.return_value = ["Python", "Node", "Java"]
        
        # Create GUI
        gui = RepoSparkGUI()
        
        # Test basic UI elements
        assert gui.repo_name_edit is not None
        assert gui.description_edit is not None
        assert gui.visibility_combo is not None
        assert gui.gitignore_combo is not None
        assert gui.license_combo is not None
        assert gui.topics_edit is not None
        
        # Test default values
        assert gui.repo_name_edit.text() == os.path.basename(os.getcwd())
        assert gui.visibility_combo.currentText() == "Public"
        assert gui.remote_combo.currentText() == "HTTPS"
        
        print("✅ GUI creation test passed")
    
    app.quit()


def main():
    """Run all tests"""
    print("🧪 Running RepoSpark Tests...\n")
    
    try:
        test_github_api_mock()
        test_scaffold_generator()
        test_gui_creation()
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
