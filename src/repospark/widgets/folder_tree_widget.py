"""
RepoSpark - Folder Tree Widget
File: src/repospark/widgets/folder_tree_widget.py
Version: 0.3.0
Description: Custom tree widget for displaying project structure preview.
Created: 2025-01-16
Author: Rich Lewis - GitHub: @RichLewis007
License: MIT
"""

# Configure logging
import logging

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

logger = logging.getLogger(__name__)


class FolderTreeWidget(QTreeWidget):
    """
    Custom tree widget that displays project structure like macOS Finder/Windows Explorer.

    This widget is used in the Project Scaffold tab to show a preview of the
    directory structure that will be created.

    Features:
    - Custom styling to match modern file browsers
    - Support for folder and file items with icons
    - Color-coded items based on type
    """

    def __init__(self, parent=None):
        """
        Initialize the folder tree widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(True)
        self.setAlternatingRowColors(False)
        self.setIndentation(24)
        # Base64-encoded SVG data URLs for tree branch icons
        closed_icon = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuNSA2TDEwIDZMMTAgNUw0LjUgNUw0LjUgNloiIGZpbGw9IiM2NTZkNzYiLz4KPHBhdGggZD0iTTYuNSA0LjVMMTAuNSA2TDYuNSA3LjVMNi41IDQuNVoiIGZpbGw9IiM2NTZkNzYiLz4KPC9zdmc+"  # noqa: E501
        open_icon = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNC41TDEwIDQuNUwxMCA1LjVMNCA1LjVMNCA0LjVaIiBmaWxsPSIjNjU2ZDc2Ii8+Cjwvc3ZnPg=="  # noqa: E501
        self.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #ffffff;
                border: 1px solid #d0d7de;
                border-radius: 8px;
                font-family: system-ui, -apple-system, BlinkMacSystemFont,
                    'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                font-size: 13px;
                color: #24292f;
                selection-background-color: #0969da;
                selection-color: white;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 8px 12px;
                border: none;
                background: transparent;
                border-radius: 6px;
                margin: 2px 4px;
                min-height: 20px;
            }}
            QTreeWidget::item:hover {{
                background-color: #f6f8fa;
                border: 1px solid #e1e4e8;
            }}
            QTreeWidget::item:selected {{
                background-color: #0969da;
                color: white;
                border: 1px solid #0969da;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                image: url({closed_icon});
            }}
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                image: url({open_icon});
            }}
            QTreeWidget::branch:!has-children:!has-siblings,
            QTreeWidget::branch:!has-children:has-siblings {{
                image: none;
            }}
            QTreeWidget::branch:has-children:!has-siblings:closed:hover,
            QTreeWidget::branch:closed:has-children:has-siblings:hover,
            QTreeWidget::branch:open:has-children:!has-siblings:hover,
            QTreeWidget::branch:open:has-children:has-siblings:hover {{
                background-color: #f6f8fa;
                border-radius: 3px;
            }}
        """)

    def add_folder_item(
        self, parent: QTreeWidgetItem | None, name: str, folder_type: str = "default"
    ) -> QTreeWidgetItem:
        """
        Add a folder item with appropriate icon.

        Args:
            parent: Parent item (None for root level)
            name: Folder name
            folder_type: Type of folder ('src', 'tests', 'docs', 'github', 'root', or 'default')

        Returns:
            The created tree widget item
        """
        item = QTreeWidgetItem(self) if parent is None else QTreeWidgetItem(parent)
        item.setText(0, name)

        # Set appropriate folder icon based on type
        if folder_type == "src":
            item.setIcon(0, self._get_folder_icon("📁", "#0366d6"))  # Blue for source
        elif folder_type == "tests":
            item.setIcon(0, self._get_folder_icon("📁", "#28a745"))  # Green for tests
        elif folder_type == "docs":
            item.setIcon(0, self._get_folder_icon("📁", "#6f42c1"))  # Purple for docs
        elif folder_type == "github":
            item.setIcon(0, self._get_folder_icon("📁", "#24292e"))  # Dark for .github
        elif folder_type == "root":
            item.setIcon(0, self._get_folder_icon("📁", "#f6f8fa"))  # Light for root
        else:
            item.setIcon(0, self._get_folder_icon("📁", "#586069"))  # Default gray

        return item

    def add_file_item(
        self, parent: QTreeWidgetItem | None, name: str, file_type: str = "default"
    ) -> QTreeWidgetItem:
        """
        Add a file item with appropriate icon.

        Args:
            parent: Parent item (None for root level)
            name: File name
            file_type: Type of file ('readme', 'changelog', 'contributing', etc.)

        Returns:
            The created tree widget item
        """
        item = QTreeWidgetItem(self) if parent is None else QTreeWidgetItem(parent)
        item.setText(0, name)

        # Set appropriate file icon based on type
        if file_type == "readme":
            item.setIcon(0, self._get_file_icon("📖", "#0366d6"))  # Blue for README
        elif file_type == "changelog":
            item.setIcon(0, self._get_file_icon("📝", "#28a745"))  # Green for changelog
        elif file_type == "contributing":
            item.setIcon(0, self._get_file_icon("🤝", "#6f42c1"))  # Purple for contributing
        elif file_type == "conduct":
            item.setIcon(0, self._get_file_icon("📋", "#d73a49"))  # Red for code of conduct
        elif file_type == "security":
            item.setIcon(0, self._get_file_icon("🔒", "#f6a434"))  # Orange for security
        elif file_type == "config":
            item.setIcon(0, self._get_file_icon("⚙️", "#586069"))  # Gray for config files
        elif file_type == "issue":
            item.setIcon(0, self._get_file_icon("🐛", "#d73a49"))  # Red for issues
        elif file_type == "pr":
            item.setIcon(0, self._get_file_icon("🔀", "#28a745"))  # Green for PRs
        elif file_type == "docs":
            item.setIcon(0, self._get_file_icon("📚", "#6f42c1"))  # Purple for docs
        elif file_type == "test":
            item.setIcon(0, self._get_file_icon("🧪", "#f6a434"))  # Orange for tests
        else:
            item.setIcon(0, self._get_file_icon("📄", "#586069"))  # Default gray

        return item

    def _get_folder_icon(self, emoji: str, color: str) -> QIcon:
        """
        Create a custom folder icon with emoji and color.

        Args:
            emoji: Emoji character for the icon
            color: Color code (not currently used, but kept for future enhancement)

        Returns:
            QIcon: The folder icon
        """
        # For now, use the system folder icon but with a simpler approach
        base_icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirIcon)

        # If we want to add color, we can do it later with a more robust approach
        # For now, just return the base icon to avoid mask issues
        return base_icon

    def _get_file_icon(self, emoji: str, color: str) -> QIcon:
        """
        Create a custom file icon with emoji and color.

        Args:
            emoji: Emoji character for the icon
            color: Color code (not currently used, but kept for future enhancement)

        Returns:
            QIcon: The file icon
        """
        # For now, use the system file icon but with a simpler approach
        base_icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)

        # If we want to add color, we can do it later with a more robust approach
        # For now, just return the base icon to avoid mask issues
        return base_icon
