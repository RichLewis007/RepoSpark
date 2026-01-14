#!/bin/bash
# Convenient script to launch Qt Designer from PySide6 and open the UI file
# Author: Rich Lewis - GitHub: @RichLewis007

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UI_DIR="${SCRIPT_DIR}/src/python_gui_scaffold/assets/ui"
UI_FILE="${UI_DIR}/main_window.ui"

# Dynamically detect PySide6 installation path
# Try to find Designer.app in the virtual environment
if [ -d "${SCRIPT_DIR}/.venv" ]; then
    # Use Python from venv to find PySide6 location
    PYTHON_VENV="${SCRIPT_DIR}/.venv/bin/python"
    if [ -f "$PYTHON_VENV" ]; then
        DESIGNER_APP=$("$PYTHON_VENV" -c "import PySide6; import os; print(os.path.join(os.path.dirname(PySide6.__file__), 'Designer.app'))" 2>/dev/null)
        if [ -z "$DESIGNER_APP" ] || [ ! -d "$DESIGNER_APP" ]; then
            DESIGNER_APP=""
        fi
    fi
fi

# Fallback: try common locations
if [ -z "$DESIGNER_APP" ] || [ ! -d "$DESIGNER_APP" ]; then
    # Try to find any pythonX.Y in .venv/lib
    for PYTHON_VER_DIR in "${SCRIPT_DIR}/.venv/lib"/python*; do
        if [ -d "$PYTHON_VER_DIR/site-packages/PySide6/Designer.app" ]; then
            DESIGNER_APP="${PYTHON_VER_DIR}/site-packages/PySide6/Designer.app"
            break
        fi
    done
fi

if [ -z "$DESIGNER_APP" ] || [ ! -d "$DESIGNER_APP" ]; then
    echo "Error: Designer.app not found in PySide6 installation"
    echo "Make sure PySide6 is installed in your virtual environment"
    exit 1
fi

# Open the UI file with Qt Designer (this will launch Designer and open the file)
if [ -f "$UI_FILE" ]; then
    open -a "$DESIGNER_APP" "$UI_FILE"
elif [ -d "$UI_DIR" ]; then
    # If main_window.ui doesn't exist, open the first .ui file found
    FIRST_UI=$(find "$UI_DIR" -maxdepth 1 -name "*.ui" | head -1)
    if [ -n "$FIRST_UI" ]; then
        echo "Opening $FIRST_UI"
        open -a "$DESIGNER_APP" "$FIRST_UI"
    else
        echo "No .ui files found in $UI_DIR"
        echo "Opening Qt Designer without a file."
        open "$DESIGNER_APP"
    fi
else
    echo "Warning: UI directory not found at $UI_DIR"
    echo "Opening Qt Designer without a file."
    open "$DESIGNER_APP"
fi

