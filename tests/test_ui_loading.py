#!/usr/bin/env python3
"""
Unit tests for UI loading functionality
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import pytest
from PySide6.QtWidgets import QApplication, QWidget, QTabWidget, QPushButton, QLabel, QProgressBar
from PySide6.QtCore import Qt

from repospark.ui_loader import load_ui, register_custom_widget
from repospark.app import FolderTreeWidget, RepoSparkGUI


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestUILoader:
    """Test UI loading functionality"""
    
    def test_load_main_window_ui(self, qapp):
        """Test that main_window.ui loads successfully"""
        widget = load_ui("main_window.ui")
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_main_window_has_required_widgets(self, qapp):
        """Test that main window has all required widgets"""
        widget = load_ui("main_window.ui")
        
        tabs = widget.findChild(QTabWidget, "tabs")
        assert tabs is not None, "tabs widget not found"
        
        progress_bar = widget.findChild(QProgressBar, "progress_bar")
        assert progress_bar is not None, "progress_bar widget not found"
        
        status_label = widget.findChild(QLabel, "status_label")
        assert status_label is not None, "status_label widget not found"
        
        create_button = widget.findChild(QPushButton, "create_button")
        assert create_button is not None, "create_button widget not found"
        
        cancel_button = widget.findChild(QPushButton, "cancel_button")
        assert cancel_button is not None, "cancel_button widget not found"
    
    def test_load_basic_tab_ui(self, qapp):
        """Test that basic_tab.ui loads successfully"""
        widget = load_ui("basic_tab.ui")
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_load_readme_tab_ui(self, qapp):
        """Test that readme_tab.ui loads successfully"""
        widget = load_ui("readme_tab.ui")
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_load_advanced_tab_ui(self, qapp):
        """Test that advanced_tab.ui loads successfully"""
        widget = load_ui("advanced_tab.ui")
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_load_scaffold_tab_ui(self, qapp):
        """Test that scaffold_tab.ui loads successfully"""
        widget = load_ui("scaffold_tab.ui")
        assert widget is not None
        assert isinstance(widget, QWidget)
    
    def test_custom_widget_registration(self, qapp):
        """Test that custom widgets can be registered"""
        register_custom_widget("FolderTreeWidget", FolderTreeWidget)
        # Registration should not raise an error
        assert True
    
    def test_load_nonexistent_ui_raises_error(self, qapp):
        """Test that loading a non-existent UI file raises RuntimeError"""
        with pytest.raises(RuntimeError):
            load_ui("nonexistent.ui")


class TestRepoSparkGUIWidgets:
    """Test that RepoSparkGUI can find all required widgets"""
    
    def test_gui_initialization(self, qapp):
        """Test that GUI initializes and finds all widgets"""
        try:
            gui = RepoSparkGUI()
            
            # Check main window widgets
            assert gui.tabs is not None
            assert gui.progress_bar is not None
            assert gui.status_label is not None
            assert gui.create_button is not None
            assert gui.cancel_button is not None
            
            # Check basic tab widgets
            assert gui.repo_name_edit is not None
            assert gui.description_edit is not None
            assert gui.visibility_public_radio is not None
            assert gui.visibility_private_radio is not None
            assert gui.gitignore_combo is not None
            assert gui.topics_edit is not None
            
            # Check advanced tab widgets
            assert gui.remote_https_radio is not None
            assert gui.remote_ssh_radio is not None
            assert gui.open_browser_check is not None
            
            # Check scaffold tab widgets
            assert gui.create_scaffold_check is not None
            assert gui.create_editorconfig_check is not None
            assert gui.scaffold_tree is not None
            
            # Check readme tab widgets
            assert gui.template_selector is not None
            assert gui.readme_editor is not None
            assert gui.readme_preview is not None
            
            gui.close()
        except RuntimeError as e:
            pytest.fail(f"GUI initialization failed: {e}")
