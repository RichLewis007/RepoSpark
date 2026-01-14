"""
UI loader utility for loading Qt Designer .ui files at runtime
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import importlib.resources
from typing import Optional, Type, Dict

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget


# Registry for custom widget classes
_custom_widgets: Dict[str, Type[QWidget]] = {}


def register_custom_widget(name: str, widget_class: Type[QWidget]) -> None:
    """
    Register a custom widget class for QUiLoader.
    
    Args:
        name: The class name as it appears in the .ui file
        widget_class: The Python class to instantiate
    """
    _custom_widgets[name] = widget_class


def load_ui(ui_filename: str, parent: Optional[QWidget] = None) -> QWidget:
    """
    Load a Qt Designer .ui file at runtime using QUiLoader.
    
    Reads the .ui file bytes from the ui folder via importlib.resources,
    wraps them in a QBuffer, and lets QUiLoader instantiate the widget tree.
    
    Args:
        ui_filename: Name of the .ui file (e.g., "main_window.ui")
        parent: Optional parent widget for the loaded widget
        
    Returns:
        QWidget: The root widget from the .ui file
        
    Raises:
        RuntimeError: If loading the .ui file fails
    """
    try:
        # Load .ui file bytes using importlib.resources
        ui_package = importlib.resources.files("repospark.assets.ui")
        ui_bytes = (ui_package / ui_filename).read_bytes()
        
        # Create QBuffer from bytes
        buffer = QBuffer()
        buffer.setData(ui_bytes)
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        
        # Use QUiLoader to instantiate the widget tree
        loader = QUiLoader()
        
        # Register custom widgets
        for name, widget_class in _custom_widgets.items():
            loader.registerCustomWidget(widget_class)
        
        widget = loader.load(buffer, parent)
        
        if widget is None:
            raise RuntimeError(f"Failed to load UI file: {ui_filename}. Error: {loader.errorString()}")
        
        return widget
        
    except Exception as e:
        raise RuntimeError(f"Failed to load UI file {ui_filename}: {str(e)}") from e
