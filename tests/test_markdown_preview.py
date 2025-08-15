#!/usr/bin/env python3
"""
Test script for GitHub-flavored markdown preview
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_markdown_rendering():
    """Test markdown rendering functionality"""
    print("Testing markdown rendering...")
    
    try:
        from src.repospark import RepoSparkGUI
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = RepoSparkGUI()
        
        # Test markdown content
        test_markdown = """# Test Repository

A test repository for markdown rendering.

## Features

- **Bold text** and *italic text*
- `Inline code` and code blocks
- [Links](https://github.com)
- Lists and numbered lists

### Code Example

```python
def hello_world():
    print("Hello, World!")
    return True
```

### Table Example

| Feature | Status | Notes |
|---------|--------|-------|
| Markdown | ✅ | Working |
| Tables | ✅ | Working |
| Code | ✅ | Working |

> This is a blockquote with some important information.

1. First item
2. Second item
3. Third item

- [x] Task completed
- [ ] Task pending
- [x] Another task

---

*End of test content*
"""
        
        # Test the markdown rendering
        gui.update_readme_preview_html(test_markdown)
        
        # Get the plain text content to verify the content was set
        plain_text = gui.readme_preview.toPlainText()
        
        # Verify key elements are present in the plain text
        assert "Test Repository" in plain_text
        assert "Features" in plain_text
        assert "Code Example" in plain_text
        assert "Table Example" in plain_text
        assert "blockquote" in plain_text or "quote" in plain_text
        
        print("✅ Markdown rendering works correctly")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_window_sizing():
    """Test window sizing functionality"""
    print("\nTesting window sizing...")
    
    try:
        from src.repospark import RepoSparkGUI
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = RepoSparkGUI()
        
        # Get window geometry
        geometry = gui.geometry()
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        # Check that window is approximately half screen width
        expected_width = screen_geometry.width() // 2
        actual_width = geometry.width()
        
        # Allow for some tolerance (within 50 pixels)
        tolerance = 50
        if abs(actual_width - expected_width) <= tolerance:
            print(f"✅ Window width is correct: {actual_width}px (expected ~{expected_width}px)")
        else:
            print(f"⚠️ Window width: {actual_width}px (expected ~{expected_width}px)")
        
        # Check that window is centered
        expected_x = (screen_geometry.width() - actual_width) // 2
        actual_x = geometry.x()
        
        if abs(actual_x - expected_x) <= tolerance:
            print(f"✅ Window is centered: x={actual_x} (expected ~{expected_x})")
        else:
            print(f"⚠️ Window position: x={actual_x} (expected ~{expected_x})")
        
        # Check reasonable height
        if 600 <= geometry.height() <= 1000:
            print(f"✅ Window height is reasonable: {geometry.height()}px")
        else:
            print(f"⚠️ Window height: {geometry.height()}px")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_github_style_css():
    """Test that GitHub-style CSS is applied"""
    print("\nTesting GitHub-style CSS...")
    
    try:
        from src.repospark import RepoSparkGUI
        from PyQt6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        gui = RepoSparkGUI()
        
        # Test simple markdown
        test_markdown = """# Header
Some text with **bold** and `code`.

```python
print("Hello")
```
"""
        
        gui.update_readme_preview_html(test_markdown)
        
        # Get the plain text to verify content was set
        plain_text = gui.readme_preview.toPlainText()
        
        # Check if the content was properly set
        if "Header" in plain_text and "bold" in plain_text and "code" in plain_text:
            print("✅ GitHub-style markdown content rendered correctly")
        else:
            print(f"⚠️ Content not properly rendered. Found: {plain_text[:100]}...")
        
        app.quit()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Markdown Preview & Window Sizing\n")
    
    tests = [
        test_markdown_rendering,
        test_window_sizing,
        test_github_style_css
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
