"""
RepoSpark - Main Window
File: src/repospark/ui/main_window.py
Version: 0.3.0
Description: Main GUI window for RepoSpark application.
Created: 2025-01-16
Author: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

import contextlib
import html
import json
import logging
import os
import re
import subprocess
import sys
from typing import Any, TypeVar, cast

from PySide6.QtCore import Q_ARG, QMetaObject, QSettings, Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextBrowser,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

T = TypeVar("T", bound=QWidget)

from ..core.github_api import GitHubAPI
from ..ui_loader import load_ui, register_custom_widget
from ..widgets.folder_tree_widget import FolderTreeWidget
from ..workers.repository_worker import RepositoryWorker

# Configure logging
logger = logging.getLogger(__name__)


class RepoSparkGUI(QMainWindow):
    """Main GUI window for RepoSpark application"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.focus_timer = None
        self.location_validation_timer = None
        self.current_config = None  # Store config for use after worker completes
        self.gitignore_template_cache = {}  # Cache for gitignore template samples
        
        # Register custom widgets for QUiLoader
        register_custom_widget("FolderTreeWidget", FolderTreeWidget)
        
        self.init_ui()
        self.load_defaults()
    
    def _find_widget(self, parent: QWidget, widget_type: type[T], name: str) -> T:
        """
        Helper method to find a widget and raise an error if not found.
        
        Args:
            parent: Parent widget to search in
            widget_type: Type of widget to find
            name: Name of the widget
            
        Returns:
            The found widget (never None)
            
        Raises:
            RuntimeError: If widget is not found
        """
        widget = parent.findChild(widget_type, name)
        if widget is None:
            raise RuntimeError(
                f"Required widget '{name}' ({widget_type.__name__}) not found in UI file"
            )
        return cast(T, widget)

    def _find_widgets(
        self, parent: QWidget, widget_specs: list[tuple[type[QWidget], str]]
    ) -> dict[str, QWidget]:
        """
        Find multiple widgets at once and validate they all exist.
        
        This method reduces code duplication and provides consistent error handling
        when validating multiple widgets from a loaded UI file.
        
        Args:
            parent: Parent widget to search in
            widget_specs: List of tuples containing (widget_type, widget_name)
            
        Returns:
            Dictionary mapping widget names to found widgets
            
        Raises:
            RuntimeError: If any widget is not found (includes list of all missing widgets)
            
        Example:
            >>> widgets = self._find_widgets(central_widget, [
            ...     (QTabWidget, "tabs"),
            ...     (QPushButton, "create_button"),
            ...     (QPushButton, "cancel_button"),
            ... ])
            >>> tabs = widgets["tabs"]
            >>> create_btn = widgets["create_button"]
        """
        widgets = {}
        missing = []
        
        for widget_type, name in widget_specs:
            widget = parent.findChild(widget_type, name)
            if widget is None:
                missing.append(f"'{name}' ({widget_type.__name__})")
            else:
                widgets[name] = widget
        
        if missing:
            missing_list = ", ".join(missing)
            raise RuntimeError(f"Required widgets not found in UI file: {missing_list}")
        
        return widgets
    
    def _create_fallback_ui(self) -> QWidget:
        """
        Create a minimal fallback UI when .ui files cannot be loaded.
        
        This provides basic functionality even when UI files are missing or corrupted.
        
        Returns:
            QWidget: A minimal central widget with basic controls
        """
        logger.warning("Creating fallback UI due to .ui file loading failure")
        
        fallback_widget = QWidget()
        layout = QVBoxLayout(fallback_widget)
        
        # Add error message
        error_label = QLabel(
            "⚠️ UI Loading Error\n\n"
            "The application is running in fallback mode.\n"
            "Please ensure all .ui files are present in:\n"
            "src/repospark/assets/ui/\n\n"
            "Some features may be limited."
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: #d73a49; font-size: 14px; padding: 20px;")
        layout.addWidget(error_label)
        
        # Add basic controls
        self.repo_name_edit = QLineEdit()
        self.repo_name_edit.setPlaceholderText("Repository name")
        layout.addWidget(QLabel("Repository Name:"))
        layout.addWidget(self.repo_name_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Description (optional)")
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(self.description_edit)
        
        # Visibility
        visibility_group = QGroupBox("Visibility")
        visibility_layout = QVBoxLayout(visibility_group)
        self.visibility_public_radio = QRadioButton("Public")
        self.visibility_public_radio.setChecked(True)
        self.visibility_private_radio = QRadioButton("Private")
        visibility_layout.addWidget(self.visibility_public_radio)
        visibility_layout.addWidget(self.visibility_private_radio)
        layout.addWidget(visibility_group)
        
        # Create button
        self.create_button = QPushButton("Create Repository")
        self.create_button.clicked.connect(self.create_repository)
        layout.addWidget(self.create_button)
        
        # Status label
        self.status_label = QLabel("Ready to create repository")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        layout.addWidget(self.cancel_button)
        
        # Initialize minimal tab widget (empty)
        self.tabs = QTabWidget()
        self.tabs.setVisible(False)  # Hide tabs in fallback mode
        
        # Initialize other required widgets with defaults
        self.gitignore_combo = QComboBox()
        self.gitignore_combo.addItem("None (empty)")
        self.topics_edit = QLineEdit()
        self.help_browser = QTextBrowser()
        self.remote_https_radio = self.visibility_public_radio  # Reuse for compatibility
        self.remote_ssh_radio = self.visibility_private_radio
        self.open_browser_check = QCheckBox()
        self.create_scaffold_check = QCheckBox()
        self.create_scaffold_check.setChecked(True)
        self.create_editorconfig_check = QCheckBox()
        self.create_editorconfig_check.setChecked(True)
        self.scaffold_tree = FolderTreeWidget()
        self.template_selector = QComboBox()
        self.readme_editor = QTextEdit()
        self.readme_preview = QTextEdit()
        self.regenerate_readme_btn = QPushButton()
        
        # Initialize radio buttons for license and project type
        self.license_mit_radio = self.visibility_public_radio  # Reuse for compatibility
        self.license_none_radio = self.visibility_private_radio
        self.license_apache_radio = self.visibility_private_radio
        self.license_gpl_radio = self.visibility_private_radio
        self.project_type_other_radio = self.visibility_public_radio
        self.project_type_python_lib_radio = self.visibility_private_radio
        self.project_type_python_cli_radio = self.visibility_private_radio
        self.project_type_js_radio = self.visibility_private_radio
        self.project_type_web_radio = self.visibility_private_radio
        self.project_type_data_radio = self.visibility_private_radio
        self.project_type_docs_radio = self.visibility_private_radio
        
        layout.addStretch()
        
        return fallback_widget
    
    def init_ui(self):
        """Initialize the user interface by loading .ui files"""
        # Set window title with program name and version
        from repospark import __version__
        self.setWindowTitle(f"RepoSpark v{__version__}")

        # Restore window geometry from settings or center on screen
        settings = QSettings("RepoSpark", "RepoSpark")
        settings.beginGroup("MainWindow")
        
        # Try to restore saved geometry
        saved_geometry = settings.value("geometry")
        if saved_geometry:
            self.restoreGeometry(saved_geometry)
        else:
            # First run - center window on screen
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            half_width = screen_geometry.width() // 2
            window_height = min(800, screen_geometry.height() - 100)
            
            # Center the window
            x_position = (screen_geometry.width() - half_width) // 2
            y_position = (screen_geometry.height() - window_height) // 2
            
            self.setGeometry(x_position, y_position, half_width, window_height)
        
        settings.endGroup()
        
        # Load main window UI with fallback
        try:
            central_widget = load_ui("main_window.ui", self)
            self.setCentralWidget(central_widget)
        except RuntimeError as e:
            logger.error(f"Failed to load main window UI: {e}")
            # Show error dialog with fallback option
            reply = QMessageBox.critical(
                self, 
                "UI Loading Error", 
                f"Failed to load main window UI:\n{str(e)}\n\n"
                "Would you like to continue with a minimal fallback interface?\n"
                "(Some features may not be available)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Create fallback UI
                central_widget = self._create_fallback_ui()
                self.setCentralWidget(central_widget)
                QMessageBox.warning(
                    self,
                    "Fallback Mode",
                    "Running in fallback mode. Some features may be limited.\n"
                    "Please check that all .ui files are present in:\n"
                    "src/repospark/assets/ui/",
                )
            else:
                raise
        
        # Find widgets from the loaded UI using batch validation
        try:
            widgets = self._find_widgets(
                central_widget,
                [
                (QTabWidget, "tabs"),
                (QProgressBar, "progress_bar"),
                (QLabel, "status_label"),
                (QPushButton, "create_button"),
                (QPushButton, "cancel_button"),
                    (QCheckBox, "open_browser_check"),
                ],
            )
            self.tabs = cast(QTabWidget, widgets["tabs"])
            self.progress_bar = cast(QProgressBar, widgets["progress_bar"])
            self.status_label = cast(QLabel, widgets["status_label"])
            self.create_button = cast(QPushButton, widgets["create_button"])
            self.cancel_button = cast(QPushButton, widgets["cancel_button"])
            self.open_browser_check = cast(QCheckBox, widgets["open_browser_check"])
            
            # Ensure default is set (checked)
            self.open_browser_check.setChecked(True)
        except RuntimeError as e:
            QMessageBox.critical(
                self,
                "UI Configuration Error",
                f"Failed to find required widgets:\n{str(e)}\n\nPlease check the .ui files.",
            )
            raise
        
        # Set initial state
        self.progress_bar.setVisible(False)
        self.cancel_button.setEnabled(False)
        
        # Wire up signals
        self.create_button.clicked.connect(self.create_repository)
        self.cancel_button.clicked.connect(self.cancel_operation)
        
        # Create menu bar with Help menu
        self._create_menu_bar()
        
        # Load and add tabs
        basic_tab = self.create_basic_tab()
        self.tabs.addTab(basic_tab, "Repo Settings")

        project_tab = self.create_project_tab()
        self.tabs.insertTab(1, project_tab, "Project")
        
        readme_tab = self.create_readme_tab()
        self.tabs.addTab(readme_tab, "README.md")
        
        advanced_tab = self.create_advanced_tab()
        self.tabs.addTab(advanced_tab, "GitHub Connection")
        
        scaffold_tab = self.create_scaffold_tab()
        self.tabs.addTab(scaffold_tab, "Project Scaffold")
    
    def create_basic_tab(self) -> QWidget:
        """Create the basic settings tab by loading .ui file"""
        widget = load_ui("basic_tab.ui", self)
        
        # Find all widgets from the loaded UI using type-safe helper
        self.repo_location_edit = self._find_widget(widget, QLineEdit, "repo_location_edit")
        self.browse_location_btn = self._find_widget(widget, QPushButton, "browse_location_btn")
        self.folder_name_edit = self._find_widget(widget, QLineEdit, "folder_name_edit")
        self.repo_name_edit = self._find_widget(widget, QLineEdit, "repo_name_edit")
        self.description_edit = self._find_widget(widget, QLineEdit, "description_edit")
        self.visibility_public_radio = self._find_widget(widget, QRadioButton, "visibility_public_radio")
        self.visibility_private_radio = self._find_widget(widget, QRadioButton, "visibility_private_radio")
        self.license_none_radio = self._find_widget(widget, QRadioButton, "license_none_radio")
        self.license_mit_radio = self._find_widget(widget, QRadioButton, "license_mit_radio")
        self.license_apache_radio = self._find_widget(widget, QRadioButton, "license_apache_radio")
        self.license_gpl_radio = self._find_widget(widget, QRadioButton, "license_gpl_radio")
        # Note: help_browser is in basic_tab for now, but will be moved to project_tab
        # We'll keep a reference here for backward compatibility during transition
        try:
            self.help_browser = self._find_widget(widget, QTextBrowser, "help_browser")
        except RuntimeError:
            # help_browser not in basic_tab, will be set in project_tab
            pass
        
        # Set tab order within groups
        self.setTabOrder(self.visibility_public_radio, self.visibility_private_radio)
        self.setTabOrder(self.license_none_radio, self.license_mit_radio)
        self.setTabOrder(self.license_mit_radio, self.license_apache_radio)
        self.setTabOrder(self.license_apache_radio, self.license_gpl_radio)
        
        # Wire up signals
        self.browse_location_btn.clicked.connect(self.browse_repository_location)
        self.repo_location_edit.textChanged.connect(self.validate_repository_location)
        self.folder_name_edit.textChanged.connect(self.update_help_info)
        self.repo_name_edit.textChanged.connect(self.update_scaffold_tree)
        self.repo_name_edit.textChanged.connect(self.update_help_info)
        self.description_edit.textChanged.connect(self.update_help_info)
        self.visibility_public_radio.toggled.connect(self.on_visibility_changed)
        self.visibility_private_radio.toggled.connect(self.on_visibility_changed)
        self.license_none_radio.toggled.connect(self.on_license_changed)
        self.license_mit_radio.toggled.connect(self.on_license_changed)
        self.license_apache_radio.toggled.connect(self.on_license_changed)
        self.license_gpl_radio.toggled.connect(self.on_license_changed)

        return widget

    def create_project_tab(self) -> QWidget:
        """Create the project settings tab by loading .ui file"""
        widget = load_ui("project_tab.ui", self)

        # Find all widgets from the loaded UI using type-safe helper
        self.project_type_other_radio = self._find_widget(widget, QPushButton, "project_type_other_radio")
        self.project_type_python_lib_radio = self._find_widget(
            widget, QPushButton, "project_type_python_lib_radio"
        )
        self.project_type_python_cli_radio = self._find_widget(
            widget, QPushButton, "project_type_python_cli_radio"
        )
        self.project_type_js_radio = self._find_widget(widget, QPushButton, "project_type_js_radio")
        self.project_type_web_radio = self._find_widget(widget, QPushButton, "project_type_web_radio")
        self.project_type_data_radio = self._find_widget(widget, QPushButton, "project_type_data_radio")
        self.project_type_docs_radio = self._find_widget(widget, QPushButton, "project_type_docs_radio")
        
        # Find popular languages quick-select buttons
        self.popular_typescript_btn = self._find_widget(widget, QPushButton, "popular_typescript_btn")
        self.popular_python_btn = self._find_widget(widget, QPushButton, "popular_python_btn")
        self.popular_javascript_btn = self._find_widget(widget, QPushButton, "popular_javascript_btn")
        self.popular_java_btn = self._find_widget(widget, QPushButton, "popular_java_btn")
        self.popular_csharp_btn = self._find_widget(widget, QPushButton, "popular_csharp_btn")
        self.popular_rust_btn = self._find_widget(widget, QPushButton, "popular_rust_btn")
        self.popular_go_btn = self._find_widget(widget, QPushButton, "popular_go_btn")
        
        # Connect popular language buttons to selection handler
        self.popular_typescript_btn.clicked.connect(lambda: self._select_gitignore_template("TypeScript"))
        self.popular_python_btn.clicked.connect(lambda: self._select_gitignore_template("Python"))
        self.popular_javascript_btn.clicked.connect(lambda: self._select_gitignore_template("JavaScript"))
        self.popular_java_btn.clicked.connect(lambda: self._select_gitignore_template("Java"))
        self.popular_csharp_btn.clicked.connect(lambda: self._select_gitignore_template("C#"))
        self.popular_rust_btn.clicked.connect(lambda: self._select_gitignore_template("Rust"))
        self.popular_go_btn.clicked.connect(lambda: self._select_gitignore_template("Go"))
        
        # Find gitignore search field
        self.gitignore_search_edit = self._find_widget(widget, QLineEdit, "gitignore_search_edit")
        
        # Find gitignore scroll area and content widget
        gitignore_scroll_area = self._find_widget(widget, QScrollArea, "gitignore_scroll_area")
        gitignore_scroll_content = self._find_widget(gitignore_scroll_area, QWidget, "gitignore_scroll_content")
        gitignore_grid_layout = gitignore_scroll_content.layout()
        if gitignore_grid_layout is None:
            gitignore_grid_layout = QGridLayout()
            gitignore_scroll_content.setLayout(gitignore_grid_layout)
        
        # Store references
        self.gitignore_scroll_area = gitignore_scroll_area
        self.gitignore_scroll_content = gitignore_scroll_content
        self.gitignore_grid_layout = gitignore_grid_layout
        
        # Create button group for gitignore templates (exclusive - only one can be selected)
        self.gitignore_button_group = QButtonGroup()
        self.gitignore_button_group.setExclusive(True)
        self.gitignore_buttons = {}  # Dictionary to map buttons to template names
        self.gitignore_all_buttons = {}  # Store all buttons for filtering
        
        # Gitignore buttons will be populated in load_defaults()
        self.selected_gitignore_template = "None (empty)"  # Default
        
        # Connect search field to filter function
        self.gitignore_search_edit.textChanged.connect(self._filter_gitignore_buttons)
        
        self.topics_edit = self._find_widget(widget, QLineEdit, "topics_edit")
        self.help_browser = self._find_widget(widget, QTextBrowser, "help_browser")

        # Create button group for project type buttons (exclusive - only one can be selected)
        self.project_type_button_group = QButtonGroup()
        self.project_type_button_group.setExclusive(True)
        self.project_type_button_group.addButton(self.project_type_other_radio)
        self.project_type_button_group.addButton(self.project_type_python_lib_radio)
        self.project_type_button_group.addButton(self.project_type_python_cli_radio)
        self.project_type_button_group.addButton(self.project_type_js_radio)
        self.project_type_button_group.addButton(self.project_type_web_radio)
        self.project_type_button_group.addButton(self.project_type_data_radio)
        self.project_type_button_group.addButton(self.project_type_docs_radio)

        # Set tab order within groups
        self.setTabOrder(self.project_type_other_radio, self.project_type_python_lib_radio)
        self.setTabOrder(self.project_type_python_lib_radio, self.project_type_python_cli_radio)
        self.setTabOrder(self.project_type_python_cli_radio, self.project_type_js_radio)
        self.setTabOrder(self.project_type_js_radio, self.project_type_web_radio)
        self.setTabOrder(self.project_type_web_radio, self.project_type_data_radio)
        self.setTabOrder(self.project_type_data_radio, self.project_type_docs_radio)

        # Wire up signals
        self.project_type_other_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_python_lib_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_python_cli_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_js_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_web_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_data_radio.toggled.connect(self.on_project_type_changed)
        self.project_type_docs_radio.toggled.connect(self.on_project_type_changed)
        
        # Initialize focus tracking (if not already initialized)
        if not hasattr(self, "current_focus_section"):
            self.current_focus_section = ""
        
        # Set up focus tracking timer (if not already set up)
        if not hasattr(self, "focus_timer") or self.focus_timer is None:
            self.focus_timer = QTimer()
            self.focus_timer.timeout.connect(self.check_focus)
            self.focus_timer.start(100)  # Check every 100ms
        
        # Initialize help content
        self.update_help_info()
        
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab by loading .ui file"""
        widget = load_ui("advanced_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.remote_ssh_radio = self._find_widget(widget, QRadioButton, "remote_ssh_radio")
        self.remote_https_radio = self._find_widget(widget, QRadioButton, "remote_https_radio")
        
        # Create button group for remote type
        self.remote_button_group = QButtonGroup()
        self.remote_button_group.addButton(self.remote_ssh_radio)
        self.remote_button_group.addButton(self.remote_https_radio)
        
        # Ensure default is set (SSH checked)
        # This should already be set from .ui file, but we ensure it's correct
        self.remote_ssh_radio.setChecked(True)
        
        return widget
    
    def create_scaffold_tab(self) -> QWidget:
        """Create the project scaffold tab by loading .ui file"""
        widget = load_ui("scaffold_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.create_scaffold_check = self._find_widget(widget, QCheckBox, "create_scaffold_check")
        self.create_editorconfig_check = self._find_widget(widget, QCheckBox, "create_editorconfig_check")
        
        # Add custom FolderTreeWidget to the preview layout
        preview_group = self._find_widget(widget, QGroupBox, "preview_group")
        preview_layout = preview_group.layout()
        if preview_layout:
            self.scaffold_tree = FolderTreeWidget()
            self.scaffold_tree.setMinimumHeight(300)
            preview_layout.addWidget(self.scaffold_tree)
        else:
            # Fallback: create custom widget directly
            self.scaffold_tree = FolderTreeWidget()
            self.scaffold_tree.setMinimumHeight(300)
        
        # Wire up signals
        self.create_scaffold_check.toggled.connect(self.update_scaffold_tree)
        self.create_editorconfig_check.toggled.connect(self.update_scaffold_tree)
        
        # Update the tree initially
        self.update_scaffold_tree()
        
        return widget
    
    def create_readme_tab(self) -> QWidget:
        """Create the README.md customization tab by loading .ui file"""
        widget = load_ui("readme_tab.ui", self)
        
        # Find widgets from the loaded UI
        self.template_selector = self._find_widget(widget, QComboBox, "template_selector")
        self.regenerate_readme_btn = self._find_widget(widget, QPushButton, "regenerate_readme_btn")
        self.readme_editor = self._find_widget(widget, QTextEdit, "readme_editor")
        self.readme_preview = self._find_widget(widget, QTextEdit, "readme_preview")
        splitter = self._find_widget(widget, QSplitter, "splitter")
        
        # Configure widgets
        self.template_selector.addItems(
            ["Auto-generate from project type", "Custom template", "Minimal template"]
        )
        self.readme_editor.setFont(QFont("Monaco", 10))
        self.readme_preview.setMaximumWidth(400)
        
        # Set splitter proportions
        if splitter:
            splitter.setSizes([600, 400])
        
        # Wire up signals
        self.template_selector.currentTextChanged.connect(self.update_readme_preview)
        self.regenerate_readme_btn.clicked.connect(self.update_readme_preview)
        self.readme_editor.textChanged.connect(self.on_readme_editor_changed)
        
        return widget
    
    def load_defaults(self) -> None:
        """Load default values"""
        # Set default repository location to ~/dev
        default_location = os.path.expanduser("~/dev")
        os.makedirs(default_location, exist_ok=True)
        
        self.repo_location_edit.setText(default_location)
        
        # Set default repository name from current directory if run from command line
        # Otherwise, use empty string (user will need to enter it)
        default_name = os.path.basename(os.getcwd()) if sys.stdin.isatty() else ""
        self.repo_name_edit.setText(default_name)
        # Set folder name to same as repo name initially
        self.folder_name_edit.setText(default_name)
        
        # Load gitignore templates
        templates = GitHubAPI.get_gitignore_templates()
        
        # Add common languages and frameworks that don't have GitHub templates
        # These will be inserted in alphabetical order
        custom_templates = [
            # "C++",
            # "C#",
            # "Dart",
            # "Go",
            # "Java",
            # "JavaScript",
            # "Kotlin",
            # "PHP",
            # "Python",
            # "R",
            # "Ruby",
            # "Rust",
            # "Scala",
            # "Swift",
            # "TypeScript",
        ]

        # Create gitignore template buttons if the grid layout exists
        if hasattr(self, "gitignore_grid_layout"):
            # Clear existing buttons (if any)
            if hasattr(self, "gitignore_buttons"):
                for button in list(self.gitignore_buttons.values()):
                    self.gitignore_button_group.removeButton(button)
                    button.deleteLater()
                self.gitignore_buttons.clear()
                self.gitignore_all_buttons.clear()
            else:
                self.gitignore_buttons = {}
                self.gitignore_all_buttons = {}
            
            # Combine and sort all templates, with "None (empty)" first
            all_templates = ["None (empty)"] + sorted(templates + custom_templates)
            
            # Create buttons in a grid (4 columns for better layout)
            columns_per_row = 4
            for index, template in enumerate(all_templates):
                row = index // columns_per_row
                col = index % columns_per_row
                
                # Create checkable button
                button = QPushButton(template)
                button.setCheckable(True)
                button.setMinimumHeight(35)
                button.setMinimumWidth(120)
                
                # Add to button group
                self.gitignore_button_group.addButton(button)
                self.gitignore_buttons[template] = button
                # Store all buttons for filtering
                self.gitignore_all_buttons[template] = button
                
                # Connect signal
                button.toggled.connect(lambda checked, t=template: self._on_gitignore_button_toggled(t, checked))
                
                # Add to grid
                self.gitignore_grid_layout.addWidget(button, row, col)
            
            # Set "None (empty)" as default (checked)
            if "None (empty)" in self.gitignore_buttons:
                self.gitignore_buttons["None (empty)"].setChecked(True)
                self.selected_gitignore_template = "None (empty)"
            
            # Apply initial filter (in case search field has text)
            if hasattr(self, "gitignore_search_edit"):
                self._filter_gitignore_buttons(self.gitignore_search_edit.text())
        
        # Initialize README preview
        self.update_readme_preview()
        
        # Set focus to Folder Name field and select all text after window is shown
        # Use QTimer to ensure this happens after the window is fully displayed
        QTimer.singleShot(0, self._set_folder_name_focus)

    def _set_folder_name_focus(self) -> None:
        """Set focus to Folder Name field and select all text"""
        self.folder_name_edit.setFocus()
        self.folder_name_edit.selectAll()
    
    def browse_repository_location(self) -> None:
        """
        Open a directory dialog to select repository location.
        
        Updates the repository location field with the selected path.
        Validates the selected location and handles existing git repositories.
        """
        current_path = self.repo_location_edit.text().strip()
        if not current_path or not os.path.exists(current_path):
            current_path = os.path.expanduser("~")
        
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Repository Location",
            current_path,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )
        
        if directory:
            self.repo_location_edit.setText(directory)
            # Validate the selected location immediately (no debounce needed for browse)
            # Stop any pending validation timer
            if self.location_validation_timer:
                self.location_validation_timer.stop()
            # Perform validation immediately
            self._do_validate_repository_location()

    def validate_repository_location(self) -> None:
        """
        Trigger validation of repository location with debounce.

        This method sets up a timer to debounce validation when the user is typing.
        The actual validation happens in _do_validate_repository_location() after
        the user stops typing for 500ms.
        """
        # Stop any existing timer
        if self.location_validation_timer:
            self.location_validation_timer.stop()

        # Create a new timer that will trigger validation after user stops typing
        self.location_validation_timer = QTimer()
        self.location_validation_timer.setSingleShot(True)
        self.location_validation_timer.timeout.connect(self._do_validate_repository_location)
        self.location_validation_timer.start(500)  # 500ms delay

    def _do_validate_repository_location(self) -> None:
        """
        Validate and handle repository location when user types or selects a folder.

        This method:
        - Creates the folder if it doesn't exist
        - Checks if the folder contains an existing git repository
        - Warns the user if a git repo exists but allows them to proceed
        - Updates the UI field with the absolute path
        """
        repo_location = self.repo_location_edit.text().strip()

        # Skip validation if field is empty (user is still typing)
        if not repo_location:
            return

        # Convert to absolute path if relative
        if not os.path.isabs(repo_location):
            repo_location = os.path.abspath(repo_location)
            self.repo_location_edit.setText(repo_location)

        # Create directory if it doesn't exist
        if not os.path.exists(repo_location):
            try:
                os.makedirs(repo_location, exist_ok=True)
                logger.info(f"Created repository location directory: {repo_location}")
            except OSError as e:
                logger.error(f"Failed to create repository location: {str(e)}")
                QMessageBox.warning(
                    self,
                    "Directory Creation Failed",
                    f"Cannot create directory:\n{repo_location}\n\nError: {str(e)}",
                )
                return

        # Check if this is an existing git repository
        git_dir = os.path.join(repo_location, ".git")
        if os.path.exists(git_dir) and os.path.isdir(git_dir):
            # This is an existing git repository
            # Get the repository remote URL if possible
            remote_url = None
            try:
                result = subprocess.run(
                    ["git", "-C", repo_location, "remote", "get-url", "origin"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                remote_url = result.stdout.strip() if result.returncode == 0 else None
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                remote_url = None

            # Show warning dialog
            warning_msg = (
                f"The selected folder contains an existing Git repository:\n\n"
                f"Location: {repo_location}\n\n"
            )

            if remote_url:
                warning_msg += f"Remote: {remote_url}\n\n"

            warning_msg += (
                "⚠️ Important Notes:\n"
                "• A new repository will be created in this location\n"
                "• Nothing will be overwritten\n"
                "• The new repository will be initialized alongside the existing one\n"
                "• You may want to select a different folder or a subdirectory\n\n"
                "Do you want to continue with this location?"
            )

            reply = QMessageBox.warning(
                self,
                "Existing Git Repository Detected",
                warning_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.No:
                # User chose not to proceed, reset to default location
                default_location = os.path.expanduser("~/dev")
                self.repo_location_edit.setText(default_location)
                logger.info("User declined to use existing git repository location")
            else:
                logger.info(
                    f"User confirmed use of existing git repository location: {repo_location}"
                )

    def validate_inputs(self) -> tuple[bool, str]:
        """
        Validate user inputs including repository name, description, and topics.
        
        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is empty string.
        """
        # Validate repository location
        repo_location = self.repo_location_edit.text().strip()
        if not repo_location:
            return False, "Repository location is required"
        
        # Check if location is a valid path
        if not os.path.isabs(repo_location):
            # Make it absolute
            repo_location = os.path.abspath(repo_location)
            self.repo_location_edit.setText(repo_location)
        
        # Create directory if it doesn't exist (validate_repository_location handles this,
        # but we also check here for final validation)
        if not os.path.exists(repo_location):
            try:
                os.makedirs(repo_location, exist_ok=True)
            except OSError as e:
                return False, f"Cannot create repository location: {str(e)}"
        
        # Verify the location is accessible and writable
        if not os.path.isdir(repo_location):
            return False, f"Repository location is not a directory: {repo_location}"

        if not os.access(repo_location, os.W_OK):
            return False, f"Repository location is not writable: {repo_location}"

        # Validate Folder Name (allows spaces, but has restrictions)
        folder_name = self.folder_name_edit.text().strip()
        if not folder_name:
            return False, "Folder name is required"

        # Check for leading or trailing spaces
        if folder_name != folder_name.strip():
            return False, "Folder name cannot start or end with spaces"

        # Invalid characters for folder names on Windows: < > : " | ? * \
        # Also check for control characters
        invalid_folder_chars = ['<', '>', ':', '"', '|', '?', '*', '\\']
        control_chars = [chr(i) for i in range(32) if chr(i) not in ['\t', '\n', '\r']]
        invalid_chars_found = [char for char in folder_name if char in invalid_folder_chars or char in control_chars]
        if invalid_chars_found:
            return (
                False,
                f"Folder name contains invalid characters: "
                f"{', '.join(repr(c) for c in set(invalid_chars_found))}\n\n"
                f"These characters cannot be used in folder names on Windows and other systems.",
            )

        # Check for reserved folder names on Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        if folder_name.upper() in reserved_names:
            return (
                False,
                f"Folder name '{folder_name}' is a reserved name on Windows and cannot be used.",
            )

        # Check for empty name after trimming spaces
        if not folder_name or folder_name.isspace():
            return False, "Folder name cannot be empty or only spaces"

        # Validate Repository Name (GitHub rules: alphanumeric + - _ . only, max 100, cannot end with .git, cannot be . or ..)
        repo_name = self.repo_name_edit.text().strip()
        if not repo_name:
            return False, "Repository name is required"
        
        # GitHub rule: Cannot be just "." or ".."
        if repo_name == "." or repo_name == "..":
            return False, "Repository name cannot be '.' or '..'"

        # GitHub rule: Must be 1-100 characters
        if len(repo_name) < 1:
            return False, "Repository name must be at least 1 character"
        if len(repo_name) > 100:
            return False, "Repository name cannot exceed 100 characters"
        
        # GitHub rule: Only alphanumeric characters, hyphens, underscores, and dots
        if not re.match(r"^[a-zA-Z0-9._-]+$", repo_name):
            return (
                False,
                "Repository name can only contain alphanumeric characters (a-z, A-Z, 0-9), "
                "hyphens (-), underscores (_), and dots (.)",
            )

        # GitHub rule: Cannot end with .git
        if repo_name.endswith(".git"):
            return False, "Repository name cannot end with '.git'"

        # GitHub rule: Cannot start with a dot or hyphen (common practice, though not strictly enforced by GitHub)
        if repo_name.startswith(".") or repo_name.startswith("-"):
            return False, "Repository name cannot start with a dot (.) or hyphen (-)"

        # GitHub rule: Cannot end with a dot
        if repo_name.endswith("."):
            return False, "Repository name cannot end with a dot (.)"

        # Validate Description (GitHub: no strict limit, but recommend keeping reasonable)
        description = self.description_edit.text().strip()
        # GitHub doesn't enforce a strict limit, but descriptions are typically kept under 160 characters
        # for readability in the UI. We'll allow up to 500 characters but warn if longer.
        if len(description) > 500:
            return False, "Description is too long. GitHub recommends keeping descriptions concise (under 160 characters for best display)."

        # Check for dangerous characters in description (newlines, null bytes)
        if any(char in description for char in ["\n", "\r", "\x00"]):
            return False, "Description contains invalid characters (newlines or null bytes)"
        
        # Validate topics
        topics_text = self.topics_edit.text().strip()
        if topics_text:
            topics = [t.strip() for t in topics_text.split(",") if t.strip()]
            if len(topics) > 20:  # GitHub topics limit
                return False, "Maximum 20 topics allowed"
            
            for topic in topics:
                if len(topic) > 35:  # GitHub topic length limit
                    return False, f"Topic '{topic}' exceeds maximum length of 35 characters"
                if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]*$", topic):
                    return (
                        False,
                        f"Topic '{topic}' contains invalid characters. "
                        "Topics can only contain alphanumeric characters and "
                        "hyphens, and must start with a letter or number",
                    )
        
        # Check if gh CLI is available
        try:
            subprocess.run(["gh", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "GitHub CLI (gh) is not installed or not available"
        
        # Check if git is available
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False, "Git is not installed or not available"
        
        # Check if user is authenticated
        user_info = GitHubAPI.get_user_info()
        if not user_info:
            return False, "GitHub CLI is not authenticated. Run 'gh auth login' first"
        
        logger.debug(f"Input validation passed for repository: {repo_name}")
        return True, ""
    
    def on_visibility_changed(self) -> None:
        """Handle visibility change"""
        self.update_help_info()
    
    def on_license_changed(self) -> None:
        """Handle license change"""
        self.update_help_info()
    
    def on_project_type_changed(self) -> None:
        """Handle project type change"""
        # Get the selected project type
        project_type = self._get_selected_project_type()
        
        # Set gitignore template based on project type
        if "Python" in project_type:
            # Set gitignore to "Python" if project type contains "Python"
            if hasattr(self, "gitignore_buttons") and "Python" in self.gitignore_buttons:
                self.gitignore_buttons["Python"].setChecked(True)
        elif "JavaScript" in project_type:
            # Set gitignore to "JavaScript" if project type contains "JavaScript"
            if hasattr(self, "gitignore_buttons") and "JavaScript" in self.gitignore_buttons:
                self.gitignore_buttons["JavaScript"].setChecked(True)
        elif project_type == "Other":
            # If "Other" is selected, set gitignore to "None (empty)"
            if hasattr(self, "gitignore_buttons") and "None (empty)" in self.gitignore_buttons:
                self.gitignore_buttons["None (empty)"].setChecked(True)
        
        # Defer expensive updates to allow radio button to show as selected immediately
        # These will execute after the current event loop iteration completes
        QTimer.singleShot(0, self.update_help_info)
        QTimer.singleShot(0, self.update_readme_preview)
        QTimer.singleShot(0, self.update_scaffold_tree)

    def _select_gitignore_template(self, template_name: str) -> None:
        """
        Select a gitignore template by name.
        This is used by the popular languages quick-select buttons.
        
        Args:
            template_name: Name of the template to select
        """
        # Find the button in the grid that matches this template name
        if hasattr(self, "gitignore_buttons") and template_name in self.gitignore_buttons:
            button = self.gitignore_buttons[template_name]
            # Make sure the button is visible (in case it's filtered out)
            button.setVisible(True)
            # Scroll to the button to make it visible
            self.gitignore_scroll_area.ensureWidgetVisible(button)
            # Programmatically click the button to select it
            button.setChecked(True)
            # This will trigger _on_gitignore_button_toggled which updates the help pane
    
    def _on_gitignore_button_toggled(self, template_name: str, checked: bool) -> None:
        """Handle gitignore template button toggle"""
        if checked:
            self.selected_gitignore_template = template_name
            # Defer expensive updates to allow button to show as selected immediately
            # These will execute after the current event loop iteration completes
            QTimer.singleShot(0, self.update_help_info)
            QTimer.singleShot(0, self.update_scaffold_tree)
    
    def _filter_gitignore_buttons(self, search_text: str) -> None:
        """Filter gitignore template buttons based on search text"""
        if not hasattr(self, "gitignore_all_buttons"):
            return
        
        search_text_lower = search_text.lower().strip()
        
        # Show/hide buttons based on search text
        for template_name, button in self.gitignore_all_buttons.items():
            # Check if template name contains search text (case-insensitive)
            if not search_text_lower or search_text_lower in template_name.lower():
                button.setVisible(True)
            else:
                button.setVisible(False)
        
        # If a button is checked but becomes hidden, ensure it stays selected
        # (it will still be selected, just hidden - user can clear search to see it)
    
    def check_focus(self):
        """Check which widget currently has focus and update help accordingly"""
        focused_widget = QApplication.focusWidget()
        
        if focused_widget == self.folder_name_edit:
            if self.current_focus_section != "folder_name":
                self.current_focus_section = "folder_name"
                self.update_help_info()
        elif focused_widget == self.repo_name_edit:
            if self.current_focus_section != "repo_name":
                self.current_focus_section = "repo_name"
                self.update_help_info()
        elif focused_widget == self.description_edit:
            if self.current_focus_section != "description":
                self.current_focus_section = "description"
                self.update_help_info()
        elif focused_widget in [self.visibility_public_radio, self.visibility_private_radio]:
            if self.current_focus_section != "visibility":
                self.current_focus_section = "visibility"
                self.update_help_info()
        elif focused_widget in [
            self.license_none_radio,
            self.license_mit_radio,
            self.license_apache_radio,
            self.license_gpl_radio,
        ]:
            if self.current_focus_section != "license":
                self.current_focus_section = "license"
                self.update_help_info()
        elif focused_widget in [
            self.project_type_other_radio,
            self.project_type_python_lib_radio,
            self.project_type_python_cli_radio,
            self.project_type_js_radio,
            self.project_type_web_radio,
            self.project_type_data_radio,
            self.project_type_docs_radio,
        ]:
            if self.current_focus_section != "project_type":
                self.current_focus_section = "project_type"
                self.update_help_info()
        elif hasattr(self, "gitignore_buttons") and focused_widget in self.gitignore_buttons.values():
            if self.current_focus_section != "gitignore":
                self.current_focus_section = "gitignore"
                self.update_help_info()
        elif focused_widget == self.topics_edit:
            if self.current_focus_section != "topics":
                self.current_focus_section = "topics"
                self.update_help_info()
        elif self.current_focus_section != "":
            # No widget has focus, show general help
            self.current_focus_section = ""
            self.update_help_info()
    
    def on_focus_changed(self, section: str):
        """Handle focus changes to show context-aware help"""
        self.current_focus_section = section
        self.update_help_info()
    
    def update_help_info(self) -> None:
        """Update the help information based on current selections"""
        help_content = self._generate_help_content()
        self.help_browser.setHtml(help_content)
    
    def _generate_help_content(self) -> str:
        """Generate context-aware help content"""
        repo_name = self.repo_name_edit.text().strip()
        description = self.description_edit.text().strip()
        visibility = self._get_selected_visibility()
        gitignore = getattr(self, "selected_gitignore_template", "None (empty)")
        license_name = self._get_selected_license()
        project_type = self._get_selected_project_type()
        topics = [t.strip() for t in self.topics_edit.text().split(",") if t.strip()]
        
        # If no specific section is focused, show general overview
        if not self.current_focus_section:
            return self._generate_general_help(
                repo_name, description, visibility, gitignore, license_name, project_type, topics
            )
        
        # Show context-specific help based on focused section
        if self.current_focus_section == "folder_name":
            folder_name = self.folder_name_edit.text().strip()
            return self._generate_folder_name_help(folder_name)
        elif self.current_focus_section == "repo_name":
            return self._generate_repo_name_help(repo_name)
        elif self.current_focus_section == "description":
            return self._generate_description_help(description)
        elif self.current_focus_section == "visibility":
            return self._generate_visibility_help(visibility)
        elif self.current_focus_section == "license":
            return self._generate_license_help(license_name)
        elif self.current_focus_section == "project_type":
            return self._generate_project_type_help(project_type)
        elif self.current_focus_section == "gitignore":
            return self._generate_gitignore_help(gitignore)
        elif self.current_focus_section == "topics":
            return self._generate_topics_help(topics)
        
        return self._generate_general_help(
            repo_name, description, visibility, gitignore, license_name, project_type, topics
        )

    def _generate_general_help(
        self,
        repo_name: str,
        description: str,
        visibility: str,
        gitignore: str,
        license_name: str,
        project_type: str,
        topics: list[str],
    ) -> str:
        """Generate general overview help content"""
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont,
                    'Segoe UI', Roboto, sans-serif; }}
                h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                p {{ margin: 8px 0; line-height: 1.4; }}
                ul {{ margin: 8px 0; padding-left: 20px; }}
                li {{ margin: 4px 0; }}
                strong {{ color: #0366d6; }}
            </style>
        </head>
        <body>
            <h3>ℹ️ Project Overview</h3>
            <p>Click on any field or option to see detailed help information.</p>
            
            <h3>📁 Repository: {repo_name or "Not set"}</h3>
            <p>Click the repository name field for naming guidelines.</p>
            
            <h3>🔓 Visibility: {visibility.title()}</h3>
            <p>Click the visibility options for details about public vs private.</p>
            
            <h3>📄 License: {license_name}</h3>
            <p>Click the license options to understand different license types.</p>
            
            <h3>🐍 Project Type: {project_type}</h3>
            <p>Click the project type options to see what each type includes.</p>
        </body>
        </html>
        """
    
    def _generate_repo_name_help(self, repo_name: str) -> str:
        """Generate help content for repository name with GitHub validation rules"""
        validation_rules = """
            <h4>📋 GitHub Repository Name Rules:</h4>
            <ul>
                <li><strong>Allowed characters:</strong> Letters (a-z, A-Z), numbers (0-9), hyphens (-), underscores (_), and dots (.)</li>
                <li><strong>Length:</strong> 1 to 100 characters</li>
                <li><strong>Cannot:</strong> Start with a dot (.) or hyphen (-)</li>
                <li><strong>Cannot:</strong> End with a dot (.)</li>
                <li><strong>Cannot:</strong> End with ".git"</li>
                <li><strong>Cannot:</strong> Be just "." or ".."</li>
                <li><strong>Spaces:</strong> Not allowed (use hyphens instead)</li>
            </ul>
            <p><strong>Examples:</strong></p>
            <ul>
                <li>✅ Valid: "my-project", "project_v2", "project.name"</li>
                <li>❌ Invalid: "my project" (spaces), ".project" (starts with dot), "project.git" (ends with .git)</li>
            </ul>
        """
        
        if repo_name:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📁 Repository Name: <strong>{repo_name}</strong></h3>
                <p>This will be the name of your GitHub repository and will appear in the URL:</p>
                <p><strong>github.com/username/{repo_name}</strong></p>
                {validation_rules}
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📁 Repository Name</h3>
                <p>Enter a name for your GitHub repository. This name must follow GitHub's naming rules.</p>
                {validation_rules}
            </body>
            </html>
            """

    def _generate_folder_name_help(self, folder_name: str) -> str:
        """Generate help content for folder name with validation rules"""
        validation_rules = """
            <h4>📋 Folder Name Rules:</h4>
            <ul>
                <li><strong>Spaces:</strong> Allowed (but cannot start or end with spaces)</li>
                <li><strong>Invalid characters:</strong> &lt; &gt; : " | ? * \\ (these cannot be used in folder names)</li>
                <li><strong>Control characters:</strong> Not allowed</li>
                <li><strong>Reserved names:</strong> Cannot be CON, PRN, AUX, NUL, COM1-9, or LPT1-9 (Windows reserved)</li>
                <li><strong>Cannot be empty:</strong> Must contain at least one non-space character</li>
                </ul>
            <p><strong>Examples:</strong></p>
            <ul>
                <li>✅ Valid: "My Project", "project-folder", "project_folder"</li>
                <li>❌ Invalid: " project" (starts with space), "project:" (contains colon), "CON" (reserved name)</li>
            </ul>
            <p><strong>Note:</strong> This is the name of the local folder on your computer. It can be different from the GitHub repository name.</p>
        """
        
        if folder_name:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📂 Folder Name: <strong>{folder_name}</strong></h3>
                <p>This will be the name of the local folder on your computer where the repository will be created.</p>
                {validation_rules}
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📂 Folder Name</h3>
                <p>Enter a name for the local folder where the repository will be created. This can include spaces and be different from the GitHub repository name.</p>
                {validation_rules}
            </body>
            </html>
            """
    
    def _generate_description_help(self, description: str) -> str:
        """Generate help content for description with GitHub validation rules"""
        validation_rules = """
            <h4>📋 GitHub Description Rules:</h4>
            <ul>
                <li><strong>Length:</strong> Recommended under 160 characters for best display</li>
                <li><strong>Maximum:</strong> 500 characters (very long descriptions may be truncated in UI)</li>
                <li><strong>Cannot contain:</strong> Newlines or null bytes</li>
                <li><strong>Best practices:</strong> Keep it concise, informative, and searchable</li>
            </ul>
            <p><strong>Tips:</strong></p>
            <ul>
                <li>Explain what the project does in one sentence</li>
                <li>Mention key technologies or frameworks used</li>
                <li>Include the main benefit or purpose</li>
                <li>Make it searchable with relevant keywords</li>
            </ul>
        """
        
        desc_length = len(description)
        length_warning = ""
        if desc_length > 500:
            length_warning = f'<p style="color: #d73a49;"><strong>❌ Error:</strong> Description is {desc_length} characters, which exceeds the 500 character limit.</p>'
        elif desc_length > 160:
            length_warning = f'<p style="color: #d73a49;"><strong>⚠️ Warning:</strong> Description is {desc_length} characters. GitHub recommends keeping descriptions under 160 characters for best display.</p>'
        
        if description:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📝 Description</h3>
                <p><strong>Current ({desc_length} chars):</strong> {description}</p>
                {length_warning}
                <p>This description will appear on your GitHub repository page and in search results.</p>
                {validation_rules}
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    h4 {{ color: #586069; margin-top: 15px; margin-bottom: 8px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>📝 Description</h3>
                <p>Add a brief description of what your project does. This helps others understand your project quickly.</p>
                {validation_rules}
            </body>
            </html>
            """
    
    def _generate_visibility_help(self, visibility: str) -> str:
        """Generate help content for visibility"""
        if visibility == "public":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔓 Visibility: Public</h3>
                <p><strong>✅ Anyone can see your repository</strong></p>
                <ul>
                    <li>Visible in search results</li>
                    <li>Can be starred and forked by anyone</li>
                    <li>Great for open source projects</li>
                    <li>Free for unlimited public repositories</li>
                    <li>Good for portfolio and collaboration</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔒 Visibility: Private</h3>
                <p><strong>🔐 Only you and collaborators can see it</strong></p>
                <ul>
                    <li>Not visible in search results</li>
                    <li>Perfect for personal projects</li>
                    <li>Good for proprietary code</li>
                    <li>Requires GitHub Pro for unlimited private repos</li>
                    <li>You control who can access it</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_license_help(self, license_name: str) -> str:
        """Generate help content for license"""
        if license_name == "MIT":  # noqa: SIM116
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: MIT</h3>
                <p><strong>🔄 Very permissive license</strong></p>
                <ul>
                    <li>Anyone can use, modify, and distribute</li>
                    <li>Must include original license and copyright</li>
                    <li>No warranty provided</li>
                    <li>Most popular for open source</li>
                    <li>Great for libraries and tools</li>
                </ul>
            </body>
            </html>
            """
        elif license_name == "Apache 2.0":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: Apache 2.0</h3>
                <p><strong>🛡️ Permissive with patent protection</strong></p>
                <ul>
                    <li>Similar to MIT but with patent protection</li>
                    <li>Good for enterprise use</li>
                    <li>Requires stating changes</li>
                    <li>Popular for business-friendly projects</li>
                    <li>Explicit patent grant</li>
                </ul>
            </body>
            </html>
            """
        elif license_name == "GPL 3.0":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: GPL 3.0</h3>
                <p><strong>🔗 Copyleft license</strong></p>
                <ul>
                    <li>Derivative works must also be GPL</li>
                    <li>Ensures code stays open source</li>
                    <li>More restrictive than MIT/Apache</li>
                    <li>Good for ensuring openness</li>
                    <li>Requires source code sharing</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 License: None</h3>
                <p><strong>⚠️ No license specified</strong></p>
                <ul>
                    <li>All rights reserved</li>
                    <li>Others cannot legally use your code</li>
                    <li>Not recommended for open source</li>
                    <li>Consider adding a license later</li>
                    <li>You retain full copyright</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_project_type_help(self, project_type: str) -> str:
        """Generate help content for project type"""
        if project_type == "Other":  # noqa: SIM116
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🔧 Project Type: Other</h3>
                <p><strong>📁 Generic project structure</strong></p>
                <ul>
                    <li>Basic project scaffolding</li>
                    <li>Standard documentation files</li>
                    <li>GitHub templates and workflows</li>
                    <li>Flexible for any project type</li>
                    <li>Minimal language-specific setup</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Python Library":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🐍 Project Type: Python Library</h3>
                <p><strong>📦 Standard Python package</strong></p>
                <ul>
                    <li>Installable via pip</li>
                    <li>Includes pytest for testing</li>
                    <li>Uses black, flake8 for linting</li>
                    <li>PyPI badges and documentation</li>
                    <li>setup.py and pyproject.toml</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Python CLI Tool":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🐍 Project Type: Python CLI Tool</h3>
                <p><strong>⚡ Command-line interface</strong></p>
                <ul>
                    <li>Uses Click for CLI framework</li>
                    <li>Installable as command-line tool</li>
                    <li>Includes help documentation</li>
                    <li>Cross-platform compatibility</li>
                    <li>Entry point configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "JavaScript/Node.js Package":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🟨 Project Type: JavaScript/Node.js Package</h3>
                <p><strong>📦 npm package</strong></p>
                <ul>
                    <li>Installable via npm</li>
                    <li>Uses Jest for testing</li>
                    <li>ESLint and Prettier for formatting</li>
                    <li>Modern ES6+ JavaScript</li>
                    <li>package.json configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Web Application":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🌐 Project Type: Web Application</h3>
                <p><strong>🚀 Full-stack web app</strong></p>
                <ul>
                    <li>Frontend and backend setup</li>
                    <li>Docker configuration</li>
                    <li>Deployment workflows</li>
                    <li>Modern web technologies</li>
                    <li>Database configuration</li>
                </ul>
            </body>
            </html>
            """
        elif project_type == "Data Science Project":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📊 Project Type: Data Science Project</h3>
                <p><strong>🔬 ML/Data analysis</strong></p>
                <ul>
                    <li>Jupyter notebook support</li>
                    <li>Data science dependencies</li>
                    <li>Visualization tools</li>
                    <li>Research-friendly structure</li>
                    <li>Model training setup</li>
                </ul>
            </body>
            </html>
            """
        else:  # Documentation Site
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📚 Project Type: Documentation Site</h3>
                <p><strong>📖 Static documentation</strong></p>
                <ul>
                    <li>Static site generator</li>
                    <li>Search functionality</li>
                    <li>Mobile-responsive design</li>
                    <li>Easy to maintain</li>
                    <li>Version control for docs</li>
                </ul>
            </body>
            </html>
            """
    
    def _generate_gitignore_help(self, gitignore: str) -> str:  # noqa: SIM116
        """Generate help content for gitignore"""
        custom_templates = [
        #     "C++",
        #     "C#",
        #     "Dart",
        #     "Go",
        #     "Java",
        #     "JavaScript",
        #     "Kotlin",
        #     "PHP",
        #     "Python",
        #     "R",
        #     "Ruby",
        #     "Rust",
        #     "Scala",
        #     "Swift",
        #     "TypeScript",
        ]
        
        if gitignore == "None":
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: None</h3>
                <p>No .gitignore file will be created. You can add one later to
                exclude files from version control.</p>
                <p><strong>Consider adding a gitignore if you have:</strong></p>
                <ul>
                    <li>Build artifacts or compiled files</li>
                    <li>Dependencies (node_modules, __pycache__)</li>
                    <li>IDE configuration files</li>
                    <li>Temporary or cache files</li>
                    <li>Sensitive configuration files</li>
                </ul>
            </body>
            </html>
            """
        elif gitignore in custom_templates:
            # Get full content for custom templates
            template_content = self._get_gitignore_template(gitignore)
            # Escape HTML special characters for display
            escaped_content = html.escape(template_content)
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                    pre {{ 
                        background-color: #f6f8fa; 
                        border: 1px solid #e1e4e8; 
                        border-radius: 6px; 
                        padding: 12px; 
                        font-family: 'SF Mono', Monaco, 'Cascadia Code',
                            'Roboto Mono', Consolas, 'Courier New', monospace;
                        font-size: 11px;
                        line-height: 1.4;
                        margin: 12px 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        max-width: 100%;
                        overflow-y: auto;
                        max-height: 500px;
                    }}
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: {gitignore}</h3>
                <p><strong>🔧 Custom template (not in GitHub's library)</strong></p>
                <p>This will create a custom .gitignore file for {gitignore} projects.</p>
                <p><strong>Full template content:</strong></p>
                <pre>{escaped_content}</pre>
            </body>
            </html>
            """
        else:
            # Get full content for official templates
            template_content = self._get_gitignore_template(gitignore)
            # Escape HTML special characters for display
            escaped_content = html.escape(template_content)
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                    pre {{ 
                        background-color: #f6f8fa; 
                        border: 1px solid #e1e4e8; 
                        border-radius: 6px; 
                        padding: 12px; 
                        font-family: 'SF Mono', Monaco, 'Cascadia Code',
                            'Roboto Mono', Consolas, 'Courier New', monospace;
                        font-size: 11px;
                        line-height: 1.4;
                        margin: 12px 0;
                        white-space: pre-wrap;
                        word-wrap: break-word;
                        overflow-wrap: break-word;
                        max-width: 100%;
                        overflow-y: auto;
                        max-height: 500px;
                    }}
                </style>
            </head>
            <body>
                <h3>📄 Gitignore: {gitignore}</h3>
                <p>This will create a .gitignore file using GitHub's official
                template for {gitignore} projects.</p>
                <p><strong>Full template content:</strong></p>
                <pre>{escaped_content}</pre>
            </body>
            </html>
            """
    
    def _generate_topics_help(self, topics: list[str]) -> str:
        """Generate help content for topics"""
        if topics:
            return f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }}
                    h3 {{ color: #24292e; margin-top: 20px; margin-bottom: 10px; }}
                    p {{ margin: 8px 0; line-height: 1.4; }}
                    ul {{ margin: 8px 0; padding-left: 20px; }}
                    li {{ margin: 4px 0; }}
                    strong {{ color: #0366d6; }}
                </style>
            </head>
            <body>
                <h3>🏷️ Topics: {", ".join(topics)}</h3>
                <p>These topics will help others discover your repository on
                GitHub and understand what it's about.</p>
                <p><strong>Benefits:</strong></p>
                <ul>
                    <li>Improves discoverability in searches</li>
                    <li>Shows up in topic-based browsing</li>
                    <li>Helps categorize your project</li>
                    <li>Makes it easier for others to find</li>
                </ul>
            </body>
            </html>
            """
        else:
            return """
            <html>
            <head>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, Arial, sans-serif; }
                    h3 { color: #24292e; margin-top: 20px; margin-bottom: 10px; }
                    p { margin: 8px 0; line-height: 1.4; }
                    ul { margin: 8px 0; padding-left: 20px; }
                    li { margin: 4px 0; }
                    strong { color: #0366d6; }
                </style>
            </head>
            <body>
                <h3>🏷️ Topics</h3>
                <p>Add topics to help others discover your repository. Use
                comma-separated values like "python, gui, qt".</p>
                <p><strong>Good topic examples:</strong></p>
                <ul>
                    <li>Programming language: python, javascript, rust</li>
                    <li>Framework: react, django, flask</li>
                    <li>Purpose: cli, gui, api, web</li>
                    <li>Domain: machine-learning, web-development</li>
                    <li>Technology: docker, kubernetes, aws</li>
                </ul>
            </body>
            </html>
            """
    
    def _get_gitignore_template(self, template_name: str) -> str:
        """Get the full gitignore template content"""
        custom_templates = [
        #     "C++",
        #     "C#",
        #     "Dart",
        #     "Go",
        #     "Java",
        #     "JavaScript",
        #     "Kotlin",
        #     "PHP",
        #     "Python",
        #     "R",
        #     "Ruby",
        #     "Rust",
        #     "Scala",
        #     "Swift",
        #     "TypeScript",
        ]
        
        if template_name in custom_templates:
            # Return sample for custom templates
            if template_name == "JavaScript":  # noqa: SIM116
                return """# .gitignore for JavaScript projects
# No files are ignored for JavaScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
..."""
            elif template_name == "TypeScript":
                return """# .gitignore for TypeScript projects
# No files are ignored for TypeScript projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# node_modules/
# .env
# .env.local
# .env.development.local
# .env.test.local
# .env.production.local
# npm-debug.log*
# yarn-debug.log*
# yarn-error.log*
# .next/
# .nuxt/
# dist/
# build/
# *.tsbuildinfo
..."""
            elif template_name == "Java":
                return """# .gitignore for Java projects
# No files are ignored for Java projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# *.class
# *.jar
# *.war
# *.ear
# .gradle/
# build/
# out/
# .idea/
# *.iml
..."""
            elif template_name == "C++":
                return """# .gitignore for C++ projects
# No files are ignored for C++ projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# bin/
# obj/
# *.o
# *.a
# *.so
# *.dll
# *.exe
# CMakeFiles/
# CMakeCache.txt
..."""
            elif template_name == "C#":
                return """# .gitignore for C# projects
# No files are ignored for C# projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# obj/
# *.user
# *.suo
# *.cache
# *.dll
# *.exe
# *.pdb
# *.log
# .vs/
# packages/
..."""
            elif template_name == "Go":
                return """# .gitignore for Go projects
# No files are ignored for Go projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# bin/
# pkg/
# *.exe
# *.exe~
# *.dll
# *.so
# *.dylib
# go.work
..."""
            elif template_name == "Rust":
                return """# .gitignore for Rust projects
# No files are ignored for Rust projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# target/
# Cargo.lock
# *.pdb
..."""
            elif template_name == "Python":
                return """# .gitignore for Python projects
# No files are ignored for Python projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# __pycache__/
# *.py[cod]
# *$py.class
# *.so
# .Python
# build/
# develop-eggs/
# dist/
# downloads/
# eggs/
# .eggs/
# lib/
# lib64/
# parts/
# sdist/
# var/
# wheels/
# *.egg-info/
# .installed.cfg
# *.egg
# MANIFEST
# .pytest_cache/
# .coverage
# .env
# .venv
# env/
# venv/
# ENV/
# env.bak/
# venv.bak/
..."""
            else:
                # Generic template for other languages
                return f"""# .gitignore for {template_name} projects
# No files are ignored for {template_name} projects by default
# Add specific patterns as needed for your project

# Common patterns you might want to add:
# build/
# dist/
# .env
# *.log
# .cache/
# .tmp/
..."""
        else:
            # Check cache first to avoid repeated network calls
            if template_name in self.gitignore_template_cache:
                return self.gitignore_template_cache[template_name]
            
            # For official GitHub templates, try to get the actual content
            try:
                result = subprocess.run(
                    ["gh", "api", f"gitignore/templates/{template_name}"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=2,  # 2 second timeout to prevent hanging
                )
                template_data = json.loads(result.stdout)
                content = template_data.get("source", "")
                
                # Cache the full content
                self.gitignore_template_cache[template_name] = content
                return content
            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, subprocess.TimeoutExpired):
                # Fallback if we can't get the actual template
                fallback = f"""# .gitignore for {template_name} projects
# This will use GitHub's official {template_name} template
# The actual content will be fetched from GitHub's template library
# when the repository is created.

# Common patterns typically included:
# Build artifacts and compiled files
# Dependencies and package managers
# Temporary and cache files
# IDE and editor files
# OS-specific files
..."""
                # Cache the fallback to avoid repeated failed attempts
                self.gitignore_template_cache[template_name] = fallback
                return fallback
    
    def _get_selected_visibility(self) -> str:
        """Get selected visibility from radio buttons"""
        if self.visibility_public_radio.isChecked():
            return "public"
        else:
            return "private"
    
    def _get_selected_license(self) -> str:
        """Get selected license from radio buttons"""
        if self.license_mit_radio.isChecked():
            return "MIT"
        elif self.license_apache_radio.isChecked():
            return "Apache 2.0"
        elif self.license_gpl_radio.isChecked():
            return "GPL 3.0"
        else:
            return "None"
    
    def _get_selected_project_type(self) -> str:
        """Get selected project type from project type buttons"""
        if self.project_type_other_radio.isChecked():
            return "Other"
        elif self.project_type_python_lib_radio.isChecked():
            return "Python Library"
        elif self.project_type_python_cli_radio.isChecked():
            return "Python CLI Tool"
        elif self.project_type_js_radio.isChecked():
            return "JavaScript/Node.js Package"
        elif self.project_type_web_radio.isChecked():
            return "Web Application"
        elif self.project_type_data_radio.isChecked():
            return "Data Science Project"
        elif self.project_type_docs_radio.isChecked():
            return "Documentation Site"
        else:
            return "Other"  # Default
    
    def update_readme_preview(self) -> None:
        """Update the README preview based on current settings"""
        try:
            # Import template system
            from templates import READMETemplate, get_project_type_by_name
            
            # Get current project configuration
            config = self.get_basic_config()
            
            # Get project type from radio buttons
            project_type_name = self._get_selected_project_type()
            project_type = get_project_type_by_name(project_type_name)
            config["project_type"] = project_type
            
            # Generate README content
            template = READMETemplate(config)
            readme_content = template.generate()
            
            # Update editor and preview
            self.readme_editor.setPlainText(readme_content)
            self.update_readme_preview_html(readme_content)
            
        except ImportError:
            # Fallback if template system is not available
            user_info = GitHubAPI.get_user_info()
            username = user_info["login"] if user_info else "username"
            fallback_content = f"""# {self.repo_name_edit.text()}

            {self.description_edit.text() or "A professional project created with RepoSpark."}

## Installation

```bash
# Install the project
git clone https://github.com/{username}/{self.repo_name_edit.text()}.git
cd {self.repo_name_edit.text()}
```

## Usage

See the documentation for usage examples.

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of
conduct and the process for submitting pull requests.

## License

This project is licensed under the {self._get_selected_license()} License.
"""
            self.readme_editor.setPlainText(fallback_content)
            self.update_readme_preview_html(fallback_content)
    
    def update_readme_preview_html(self, markdown_content: str):
        """Convert markdown to HTML for preview using GitHub-flavored markdown"""
        try:
            import markdown
            
            # Configure markdown with GitHub-flavored extensions
            md = markdown.Markdown(
                extensions=[
                    "markdown.extensions.fenced_code",  # GitHub-style code blocks
                    "markdown.extensions.tables",  # Tables
                    "markdown.extensions.nl2br",  # Line breaks
                    "markdown.extensions.sane_lists",  # Better list handling
                    "markdown.extensions.codehilite",  # Syntax highlighting
                    "markdown.extensions.toc",  # Table of contents
                    "markdown.extensions.attr_list",  # Attribute lists
                    "markdown.extensions.def_list",  # Definition lists
                    "markdown.extensions.footnotes",  # Footnotes
                    "markdown.extensions.abbr",  # Abbreviations
                    "markdown.extensions.md_in_html",  # Markdown in HTML
                ]
            )
            
            # Convert markdown to HTML
            html_content = md.convert(markdown_content)
            
            # Add GitHub-style CSS
            styled_html = f"""
            <html>
            <head>
                <style>
                    /* GitHub-style CSS */
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont,
                            'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
                        font-size: 14px;
                        line-height: 1.5;
                        color: #24292f;
                        background-color: #ffffff;
                        padding: 20px;
                        margin: 0;
                    }}
                    
                    /* Headers */
                    h1, h2, h3, h4, h5, h6 {{
                        margin-top: 24px;
                        margin-bottom: 16px;
                        font-weight: 600;
                        line-height: 1.25;
                        color: #24292f;
                    }}
                    
                    h1 {{
                        font-size: 2em;
                        border-bottom: 1px solid #d0d7de;
                        padding-bottom: 0.3em;
                    }}
                    
                    h2 {{
                        font-size: 1.5em;
                        border-bottom: 1px solid #d0d7de;
                        padding-bottom: 0.3em;
                    }}
                    
                    h3 {{
                        font-size: 1.25em;
                    }}
                    
                    /* Paragraphs and spacing */
                    p {{
                        margin-top: 0;
                        margin-bottom: 16px;
                    }}
                    
                    /* Lists */
                    ul, ol {{
                        margin-top: 0;
                        margin-bottom: 16px;
                        padding-left: 2em;
                    }}
                    
                    li {{
                        margin-top: 0.25em;
                    }}
                    
                    /* Code */
                    code {{
                        padding: 0.2em 0.4em;
                        margin: 0;
                        font-size: 85%;
                        background-color: rgba(175, 184, 193, 0.2);
                        border-radius: 6px;
                        font-family: ui-monospace, SFMono-Regular, 'SF Mono',
                            Consolas, 'Liberation Mono', Menlo, monospace;
                    }}
                    
                    /* Code blocks */
                    pre {{
                        padding: 16px;
                        overflow: auto;
                        font-size: 85%;
                        line-height: 1.45;
                        background-color: #f6f8fa;
                        border-radius: 6px;
                        border: 1px solid #d0d7de;
                        margin-top: 0;
                        margin-bottom: 16px;
                    }}
                    
                    pre code {{
                        padding: 0;
                        margin: 0;
                        background-color: transparent;
                        border: 0;
                        font-size: 100%;
                        word-break: normal;
                        white-space: pre;
                    }}
                    
                    /* Links */
                    a {{
                        color: #0969da;
                        text-decoration: none;
                    }}
                    
                    a:hover {{
                        text-decoration: underline;
                    }}
                    
                    /* Blockquotes */
                    blockquote {{
                        padding: 0 1em;
                        color: #656d76;
                        border-left: 0.25em solid #d0d7de;
                        margin: 0 0 16px 0;
                    }}
                    
                    /* Tables */
                    table {{
                        border-spacing: 0;
                        border-collapse: collapse;
                        margin-top: 0;
                        margin-bottom: 16px;
                        width: 100%;
                    }}
                    
                    th, td {{
                        padding: 6px 13px;
                        border: 1px solid #d0d7de;
                    }}
                    
                    th {{
                        font-weight: 600;
                        background-color: #f6f8fa;
                    }}
                    
                    /* Horizontal rules */
                    hr {{
                        height: 0.25em;
                        padding: 0;
                        margin: 24px 0;
                        background-color: #d0d7de;
                        border: 0;
                    }}
                    
                    /* Images */
                    img {{
                        max-width: 100%;
                        height: auto;
                        box-sizing: content-box;
                    }}
                    
                    /* Badges */
                    img[src*="shields.io"] {{
                        display: inline-block;
                        margin: 2px;
                    }}
                    
                    /* Task lists */
                    .task-list-item {{
                        list-style-type: none;
                    }}
                    
                    .task-list-item input {{
                        margin: 0 0.2em 0.25em -1.4em;
                        vertical-align: middle;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.readme_preview.setHtml(styled_html)
            
        except ImportError:
            # Fallback to simple conversion if markdown library is not available
            html_content = markdown_content.replace("\n", "<br>")
            html_content = html_content.replace("```", "<pre><code>")
            html_content = html_content.replace("`", "<code>")
            html_content = html_content.replace("# ", "<h1>")
            html_content = html_content.replace("## ", "<h2>")
            html_content = html_content.replace("### ", "<h3>")
            html_content = html_content.replace("- ", "<li>")
            
            styled_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont,
                        'Segoe UI', Roboto, sans-serif; padding: 20px; }}
                    h1 {{ color: #24292e; border-bottom: 1px solid #e1e4e8;
                        padding-bottom: 0.3em; }}
                    h2 {{ color: #24292e; border-bottom: 1px solid #e1e4e8;
                        padding-bottom: 0.3em; }}
                    h3 {{ color: #24292e; }}
                    code {{ background-color: #f6f8fa; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background-color: #f6f8fa; padding: 16px;
                        border-radius: 6px; overflow-x: auto; }}
                    li {{ margin: 4px 0; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.readme_preview.setHtml(styled_html)
    
    def on_readme_editor_changed(self):
        """Handle README editor content changes"""
        content = self.readme_editor.toPlainText()
        self.update_readme_preview_html(content)
    
    def update_scaffold_tree(self) -> None:
        """Update the scaffold tree based on current settings"""
        self.scaffold_tree.clear()
        
        if not self.create_scaffold_check.isChecked():
            # Show empty state
            root_item = QTreeWidgetItem(self.scaffold_tree)
            root_item.setText(0, "project-name/")
            root_item.setIcon(
                0,
                self.scaffold_tree.style().standardIcon(
                    self.scaffold_tree.style().StandardPixmap.SP_DirIcon
                ),
            )
            return
        
        # Create root project folder
        project_name = (
            self.repo_name_edit.text().strip()
            if self.repo_name_edit.text().strip()
            else "project-name"
        )
        root_item = self.scaffold_tree.add_folder_item(None, f"{project_name}/", "root")
        
        # Add standard directories with specific types
        src_folder = self.scaffold_tree.add_folder_item(root_item, "src/", "src")
        tests_folder = self.scaffold_tree.add_folder_item(root_item, "tests/", "tests")
        docs_folder = self.scaffold_tree.add_folder_item(root_item, "docs/", "docs")
        github_folder = self.scaffold_tree.add_folder_item(root_item, ".github/", "github")
        
        # Add files in root with specific types
        self.scaffold_tree.add_file_item(root_item, "README.md", "readme")
        self.scaffold_tree.add_file_item(root_item, "CHANGELOG.md", "changelog")
        self.scaffold_tree.add_file_item(root_item, "CONTRIBUTING.md", "contributing")
        self.scaffold_tree.add_file_item(root_item, "CODE_OF_CONDUCT.md", "conduct")
        self.scaffold_tree.add_file_item(root_item, "SECURITY.md", "security")
        self.scaffold_tree.add_file_item(root_item, ".gitattributes", "config")
        
        # Add .editorconfig if enabled
        if self.create_editorconfig_check.isChecked():
            self.scaffold_tree.add_file_item(root_item, ".editorconfig", "config")
        
        # Add project-specific files based on project type
        project_type = self._get_selected_project_type()
        self._add_project_specific_files(root_item, src_folder, tests_folder, project_type)
        
        # Add files in .github folder
        self.scaffold_tree.add_file_item(github_folder, "ISSUE_TEMPLATE.md", "issue")
        self.scaffold_tree.add_file_item(github_folder, "PULL_REQUEST_TEMPLATE.md", "pr")
        
        # Add files in docs folder
        self.scaffold_tree.add_file_item(docs_folder, "index.md", "docs")
        
        # Add files in tests folder
        self.scaffold_tree.add_file_item(tests_folder, "test_placeholder.txt", "test")
        
        # Expand the root item
        self.scaffold_tree.expandItem(root_item)
    
    def _add_project_specific_files(
        self,
        root_item: QTreeWidgetItem,
        src_folder: QTreeWidgetItem,
        tests_folder: QTreeWidgetItem,
        project_type: str,
    ) -> None:
        """Add project-specific files based on the selected project type"""
        if project_type == "Python Library":
            # Python library specific files
            self.scaffold_tree.add_file_item(root_item, "pyproject.toml", "config")
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(root_item, "setup.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_main.py", "test")
            
        elif project_type == "Python CLI Tool":
            # Python CLI specific files
            self.scaffold_tree.add_file_item(root_item, "pyproject.toml", "config")
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(src_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "cli.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "__init__.py", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_cli.py", "test")
            
        elif project_type == "JavaScript/Node.js Package":
            # JavaScript package specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "package-lock.json", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.js", "config")
            self.scaffold_tree.add_file_item(tests_folder, "index.test.js", "test")
            
        elif project_type == "Web Application":
            # Web application specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "webpack.config.js", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.html", "config")
            self.scaffold_tree.add_file_item(src_folder, "app.js", "config")
            self.scaffold_tree.add_file_item(src_folder, "styles.css", "config")
            self.scaffold_tree.add_file_item(tests_folder, "app.test.js", "test")
            
        elif project_type == "Data Science Project":
            # Data science specific files
            self.scaffold_tree.add_file_item(root_item, "requirements.txt", "config")
            self.scaffold_tree.add_file_item(root_item, "environment.yml", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "main.py", "config")
            self.scaffold_tree.add_file_item(src_folder, "data_analysis.ipynb", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_analysis.py", "test")
            
        elif project_type == "Documentation Site":
            # Documentation site specific files
            self.scaffold_tree.add_file_item(root_item, "package.json", "config")
            self.scaffold_tree.add_file_item(root_item, "mkdocs.yml", "config")
            self.scaffold_tree.add_file_item(root_item, ".gitignore", "config")
            self.scaffold_tree.add_file_item(src_folder, "index.html", "config")
            self.scaffold_tree.add_file_item(src_folder, "styles.css", "config")
            self.scaffold_tree.add_file_item(tests_folder, "test_docs.py", "test")
    
    def get_basic_config(self) -> dict[str, Any]:
        """
        Get basic configuration for templates.
        
        Returns:
            Dictionary containing basic repository configuration
        """
        user_info = GitHubAPI.get_user_info()
        
        return {
            "repo_name": self.repo_name_edit.text().strip(),
            "description": self.description_edit.text().strip(),
            "license": self._get_selected_license().lower().replace(" ", "-")
            if self._get_selected_license() != "None"
            else "",
            "topics": [t.strip() for t in self.topics_edit.text().split(",") if t.strip()],
            "username": user_info["login"] if user_info else "username",
        }

    def get_config(self) -> dict[str, Any]:
        """
        Get complete configuration from UI for repository creation.
        
        Returns:
            Dictionary containing all configuration needed to create repository
        """
        user_info = GitHubAPI.get_user_info()
        
        return {
            "repo_name": self.repo_name_edit.text().strip(),
            "folder_name": self.folder_name_edit.text().strip(),
            "description": self.description_edit.text().strip(),
            "visibility": self._get_selected_visibility(),
            "gitignore_template": (
                ""
                if getattr(self, "selected_gitignore_template", "None (empty)") == "None (empty)"
                else getattr(self, "selected_gitignore_template", "None (empty)")
            ),
            "license": self._get_selected_license().lower().replace(" ", "-")
            if self._get_selected_license() != "None"
            else "",
            "topics": [t.strip() for t in self.topics_edit.text().split(",") if t.strip()],
            "remote_type": "ssh" if self.remote_ssh_radio.isChecked() else "https",
            "create_scaffold": self.create_scaffold_check.isChecked(),
            "create_editorconfig": self.create_editorconfig_check.isChecked(),
            "open_browser": self.open_browser_check.isChecked(),
            "username": user_info["login"] if user_info else "",
            "repo_location": self.repo_location_edit.text().strip(),
            "project_type": self._get_selected_project_type(),
            "readme_content": self.readme_editor.toPlainText()
            if hasattr(self, "readme_editor")
            else "",
        }

    def _show_confirm_dialog(self, config: dict[str, Any]) -> bool:
        """
        Show confirmation dialog for repository creation.

        Args:
            config: Repository configuration dictionary

        Returns:
            True if user confirmed (Yes), False if cancelled (No)
        """
        try:
            # Load the confirmation dialog UI (returns QDialog directly)
            dialog = load_ui("confirm_dialog.ui", self)
            if not isinstance(dialog, QDialog):
                # Fallback: if not a QDialog, wrap it
                temp_dialog = QDialog(self)
                layout = QVBoxLayout(temp_dialog)
                layout.addWidget(dialog)
                dialog = temp_dialog

            # Find widgets within the dialog
            title_label = self._find_widget(dialog, QLabel, "title_label")
            details_browser = self._find_widget(dialog, QTextBrowser, "details_browser")
            yes_button = self._find_widget(dialog, QPushButton, "yes_button")
            no_button = self._find_widget(dialog, QPushButton, "no_button")

            # Update title with repository name
            title_label.setText(f"Create repository '{config['repo_name']}'?")

            # Format details message
            details_html = f"""<html>
<head>
<style>
body {{ font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; }}
h3 {{ color: #24292e; margin-top: 10px; margin-bottom: 8px; }}
p {{ margin: 4px 0; line-height: 1.5; }}
strong {{ color: #0366d6; }}
</style>
</head>
<body>
<h3>Repository Details:</h3>
<p><strong>GitHub Name:</strong> {config["repo_name"]}</p>
<p><strong>Folder Name:</strong> {config["folder_name"]}</p>
<p><strong>Location:</strong> {config["repo_location"]}</p>
<p><strong>Visibility:</strong> {config["visibility"]}</p>
<p><strong>Description:</strong> {config["description"] or "None"}</p>
<p><strong>Gitignore:</strong> {config["gitignore_template"] or "None"}</p>
<p><strong>License:</strong> {config["license"] or "None"}</p>
<p><strong>Topics:</strong> {", ".join(config["topics"]) if config["topics"] else "None"}</p>
<p><strong>Remote:</strong> {config["remote_type"].upper()}</p>
<p><strong>Scaffold:</strong> {"Yes" if config["create_scaffold"] else "No"}</p>
<br>
<p><strong>This will create the repository on GitHub and set up the local git repository in:</strong></p>
<p>{os.path.join(config["repo_location"], config["folder_name"])}</p>
</body>
</html>"""
            details_browser.setHtml(details_html)

            # Connect buttons
            result = [False]  # Use list to allow modification in nested function

            def on_yes():
                result[0] = True
                dialog.accept()

            def on_no():
                result[0] = False
                dialog.reject()

            yes_button.clicked.connect(on_yes)
            no_button.clicked.connect(on_no)

            # Center dialog on screen
            dialog.setWindowModality(Qt.WindowModality.WindowModal)
            screen = QApplication.primaryScreen()
            screen_geometry = screen.geometry()
            dialog_geometry = dialog.frameGeometry()
            center_point = screen_geometry.center()
            dialog_geometry.moveCenter(center_point)
            dialog.move(dialog_geometry.topLeft())

            # Execute dialog (No is default button from .ui file)
            dialog.exec()
            return result[0]

        except Exception as e:
            logger.error(f"Failed to load confirmation dialog: {e}")
            # Fallback to QMessageBox if custom dialog fails
            msg = f"""Create repository '{config["repo_name"]}'?

Repository Details:
• GitHub Name: {config["repo_name"]}
• Folder Name: {config["folder_name"]}
• Location: {config["repo_location"]}
• Visibility: {config["visibility"]}
• Description: {config["description"] or "None"}
• Gitignore: {config["gitignore_template"] or "None"}
• License: {config["license"] or "None"}
• Topics: {", ".join(config["topics"]) if config["topics"] else "None"}
• Remote: {config["remote_type"]}
• Scaffold: {"Yes" if config["create_scaffold"] else "No"}

This will create the repository on GitHub and set up the local git repository in:
{os.path.join(config["repo_location"], config["folder_name"])}"""

            reply = QMessageBox.question(
                self,
                "Confirm Creation",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,  # No as default
            )
            return reply == QMessageBox.StandardButton.Yes

    def create_repository(self) -> None:
        """Start repository creation process"""
        # Validate inputs
        is_valid, error_msg = self.validate_inputs()
        if not is_valid:
            QMessageBox.critical(self, "Validation Error", error_msg)
            return
        
        # Get configuration
        config = self.get_config()
        
        # Store config for later use (e.g., opening browser after success)
        self.current_config = config.copy()

        # Confirm creation using custom dialog
        if not self._show_confirm_dialog(config):
            return
        
        # Start worker
        self.worker = RepositoryWorker(config)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_creation_finished)
        
        # Update UI
        self.create_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Creating repository...")
        
        self.worker.start()
    
    def update_progress(self, message: str) -> None:
        """
        Update progress message in a thread-safe manner.
        
        This method can be called from any thread and will safely update
        the UI using QMetaObject.invokeMethod for explicit thread safety.
        
        Args:
            message: Progress message to display
        """
        # Use QMetaObject.invokeMethod for explicit thread-safe UI updates
        # pyright: ignore[reportArgumentType, reportCallIssue]
        QMetaObject.invokeMethod(
            self.status_label, "setText", Qt.ConnectionType.QueuedConnection, Q_ARG(str, message)
        )
    
    def on_creation_finished(self, success: bool, message: str) -> None:
        """
        Handle repository creation completion in a thread-safe manner.
        
        This method is called from the worker thread and uses thread-safe
        methods to update the UI.
        
        Args:
            success: Whether the operation succeeded
            message: Completion message
        """
        # Use thread-safe UI updates
        # pyright: ignore[reportArgumentType, reportCallIssue]
        QMetaObject.invokeMethod(
            self.progress_bar, "setVisible", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
        )
        # pyright: ignore[reportArgumentType, reportCallIssue]
        QMetaObject.invokeMethod(
            self.create_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True)
        )
        # pyright: ignore[reportArgumentType, reportCallIssue]
        QMetaObject.invokeMethod(
            self.cancel_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
        )
        
        if success:
            # pyright: ignore[reportArgumentType, reportCallIssue]
            QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Repository created successfully!"),
            )
            # Show message box in main thread using QTimer for thread safety
            QTimer.singleShot(0, lambda: self._show_success_message(message))

            # Open in browser if requested (use stored config)
            if self.current_config and self.current_config.get("open_browser", False):
                QTimer.singleShot(0, lambda: self._open_repo_in_browser())
        else:
            # pyright: ignore[reportArgumentType, reportCallIssue]
            QMetaObject.invokeMethod(
                self.status_label,
                "setText",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Repository creation failed"),
            )
            # Show error message box in main thread using QTimer for thread safety
            QTimer.singleShot(0, lambda: self._show_error_message(message))
    
    def _show_success_message(self, message: str) -> None:
        """Thread-safe helper to show success message box"""
        QMessageBox.information(self, "Success", message)
    
    def _show_error_message(self, message: str) -> None:
        """Thread-safe helper to show error message box"""
        QMessageBox.critical(self, "Repository Creation Failed", message)

    def _open_repo_in_browser(self) -> None:
        """Open the repository in browser (called from main thread)"""
        if not self.current_config:
            return
        try:
            with contextlib.suppress(subprocess.CalledProcessError):
                subprocess.run(
                    [
                        "gh",
                        "repo",
                        "view",
                        f"{self.current_config['username']}/{self.current_config['repo_name']}",
                        "--web",
                    ]
                )
        except Exception as e:
            logger.error(f"Failed to open repository in browser: {e}")
    
    def cancel_operation(self) -> None:
        """Cancel the current operation"""
        if self.worker and self.worker.isRunning():
            # Use graceful shutdown instead of terminate()
            self.worker._should_stop = True
            self.status_label.setText("Cancelling operation...")
            # Wait for thread to finish gracefully (with timeout)
            if not self.worker.wait(3000):  # 3 second timeout
                # If still running, force termination as last resort
                self.worker.terminate()
                self.worker.wait()
        
        self.progress_bar.setVisible(False)
        self.create_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.status_label.setText("Operation cancelled")
    
    def _create_menu_bar(self) -> None:
        """
        Create menu bar with Help menu containing About dialog.
        """
        menu_bar = self.menuBar()
        
        # Create Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Add About action
        about_action = help_menu.addAction("&About RepoSpark...")
        about_action.triggered.connect(self.show_about_dialog)
        about_action.setShortcut("F1")  # F1 for help/about
        
        # Add About Qt action (standard Qt action)
        help_menu.addSeparator()
        about_qt_action = help_menu.addAction("About &Qt...")
        about_qt_action.triggered.connect(lambda: QMessageBox.aboutQt(self))
    
    def show_about_dialog(self) -> None:
        """
        Show About dialog with application information and version.
        """
        from repospark import __version__
        
        about_text = f"""
        <h2>RepoSpark</h2>
        <p><b>Version {__version__}</b></p>
        <p>A PySide6 GUI application for creating GitHub repositories</p>
        <p>Author: Rich Lewis</p>
        <p>GitHub: <a href="https://github.com/RichLewis007">@RichLewis007</a></p>
        <hr>
        <p>RepoSpark helps you create comprehensive GitHub repositories with:</p>
        <ul>
            <li>Customizable project scaffolds</li>
            <li>README.md generation</li>
            <li>License and gitignore templates</li>
            <li>Topic management</li>
            <li>And much more!</li>
        </ul>
        <p>Built with PySide6 6.7.3</p>
        <p>Python {sys.version.split()[0]}</p>
        """
        
        QMessageBox.about(self, "About RepoSpark", about_text)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window geometry for next session
        settings = QSettings("RepoSpark", "RepoSpark")
        settings.beginGroup("MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.endGroup()
        
        # Stop focus timer
        if self.focus_timer:
            self.focus_timer.stop()
        
        # Stop location validation timer
        if self.location_validation_timer:
            self.location_validation_timer.stop()
        
        # Cancel any running operations
        if self.worker and self.worker.isRunning():
            self.worker._should_stop = True
            if not self.worker.wait(2000):  # 2 second timeout
                self.worker.terminate()
                self.worker.wait()
        
        event.accept()
