"""
UI loader utility for loading Qt Designer .ui files at runtime.

This module provides functionality to load Qt Designer .ui files at runtime
using QUiLoader. It supports custom widget registration and proper error handling.
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import importlib.resources
import logging
from typing import Optional, Type, Dict

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget

# Configure logging
logger = logging.getLogger(__name__)

# Registry for custom widget classes
_custom_widgets: Dict[str, Type[QWidget]] = {}


def register_custom_widget(name: str, widget_class: Type[QWidget]) -> None:
    """
    Register a custom widget class for QUiLoader.
    
    Custom widgets must be registered before loading .ui files that use them.
    
    Args:
        name: The class name as it appears in the .ui file
        widget_class: The Python class to instantiate
        
    Example:
        >>> register_custom_widget("MyCustomWidget", MyCustomWidget)
    """
    _custom_widgets[name] = widget_class
    logger.debug(f"Registered custom widget: {name} -> {widget_class.__name__}")


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
        
        try:
            # Use QUiLoader to instantiate the widget tree
            loader = QUiLoader()
            
            # Register custom widgets
            for name, widget_class in _custom_widgets.items():
                loader.registerCustomWidget(widget_class)
                logger.debug(f"Registered custom widget with loader: {name}")
            
            widget = loader.load(buffer, parent)
            
            if widget is None:
                error_msg = loader.errorString()
                logger.error(f"Failed to load UI file {ui_filename}: {error_msg}")
                raise RuntimeError(f"Failed to load UI file: {ui_filename}. Error: {error_msg}")
            
            logger.info(f"Successfully loaded UI file: {ui_filename}")
            return widget
        finally:
            # Ensure buffer is closed
            if buffer.isOpen():
                buffer.close()
        
    except FileNotFoundError as e:
        logger.error(f"UI file not found: {ui_filename}")
        raise RuntimeError(f"UI file not found: {ui_filename}") from e
    except Exception as e:
        logger.error(f"Failed to load UI file {ui_filename}: {str(e)}")
        raise RuntimeError(f"Failed to load UI file {ui_filename}: {str(e)}") from e
