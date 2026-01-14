#!/usr/bin/env python3
"""
Test script for radio button functionality and help system
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_radio_button_methods():
    """Test the radio button helper methods"""
    print("Testing radio button helper methods...")
    
    try:
        from src.repospark import RepoSparkGUI
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = RepoSparkGUI()
        
        # Test visibility methods
        print("Testing visibility methods...")
        gui.visibility_public_radio.setChecked(True)
        assert gui._get_selected_visibility() == "public"
        print("✅ Public visibility works")
        
        gui.visibility_private_radio.setChecked(True)
        assert gui._get_selected_visibility() == "private"
        print("✅ Private visibility works")
        
        # Test license methods
        print("Testing license methods...")
        gui.license_mit_radio.setChecked(True)
        assert gui._get_selected_license() == "MIT"
        print("✅ MIT license works")
        
        gui.license_apache_radio.setChecked(True)
        assert gui._get_selected_license() == "Apache 2.0"
        print("✅ Apache license works")
        
        gui.license_gpl_radio.setChecked(True)
        assert gui._get_selected_license() == "GPL 3.0"
        print("✅ GPL license works")
        
        gui.license_none_radio.setChecked(True)
        assert gui._get_selected_license() == "None"
        print("✅ None license works")
        
        # Test project type methods
        print("Testing project type methods...")
        gui.project_type_python_lib_radio.setChecked(True)
        assert gui._get_selected_project_type() == "Python Library"
        print("✅ Python Library works")
        
        gui.project_type_python_cli_radio.setChecked(True)
        assert gui._get_selected_project_type() == "Python CLI Tool"
        print("✅ Python CLI Tool works")
        
        gui.project_type_js_radio.setChecked(True)
        assert gui._get_selected_project_type() == "JavaScript/Node.js Package"
        print("✅ JavaScript Package works")
        
        gui.project_type_web_radio.setChecked(True)
        assert gui._get_selected_project_type() == "Web Application"
        print("✅ Web Application works")
        
        gui.project_type_data_radio.setChecked(True)
        assert gui._get_selected_project_type() == "Data Science Project"
        print("✅ Data Science Project works")
        
        gui.project_type_docs_radio.setChecked(True)
        assert gui._get_selected_project_type() == "Documentation Site"
        print("✅ Documentation Site works")
        
        # Test help content generation
        print("Testing help content generation...")
        help_content = gui._generate_help_content()
        assert "Repository Name" in help_content
        assert "Visibility" in help_content
        assert "License" in help_content
        assert "Project Type" in help_content
        print("✅ Help content generation works")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_config_generation():
    """Test configuration generation with radio buttons"""
    print("\nTesting configuration generation...")
    
    try:
        from src.repospark import RepoSparkGUI
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = RepoSparkGUI()
        
        # Set some test values
        gui.repo_name_edit.setText("test-repo")
        gui.description_edit.setText("A test repository")
        gui.visibility_public_radio.setChecked(True)
        gui.license_mit_radio.setChecked(True)
        gui.project_type_python_lib_radio.setChecked(True)
        gui.topics_edit.setText("python, test, gui")
        
        # Get configuration
        config = gui.get_config()
        
        # Verify values
        assert config['repo_name'] == "test-repo"
        assert config['description'] == "A test repository"
        assert config['visibility'] == "public"
        assert config['license'] == "mit"
        assert config['project_type'] == "Python Library"
        assert "python" in config['topics']
        assert "test" in config['topics']
        assert "gui" in config['topics']
        
        print("✅ Configuration generation works correctly")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Radio Button System\n")
    
    tests = [
        test_radio_button_methods,
        test_config_generation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
