#!/usr/bin/env python3
"""
Test script for the template system
"""
# Author: Rich Lewis - GitHub: @RichLewis007

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_project_types():
    """Test project types system"""
    print("Testing project types...")
    
    try:
        from templates import get_project_types, get_project_type_by_name
        
        # Get all project types
        project_types = get_project_types()
        print(f"✅ Found {len(project_types)} project types:")
        
        for pt_id, pt in project_types.items():
            print(f"  - {pt.name}: {pt.description}")
        
        # Test getting by name
        python_lib = get_project_type_by_name("Python Library")
        if python_lib:
            print(f"✅ Python Library project type found:")
            print(f"  - Language: {python_lib.language}")
            print(f"  - Package Manager: {python_lib.package_manager}")
            print(f"  - Test Framework: {python_lib.test_framework}")
            print(f"  - Badges: {len(python_lib.badges)} badges")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_readme_template():
    """Test README template generation"""
    print("\nTesting README template...")
    
    try:
        from templates import READMETemplate, get_project_type_by_name
        
        # Test configuration
        config = {
            'repo_name': 'test-project',
            'description': 'A test project for template system',
            'license': 'mit',
            'topics': ['python', 'test', 'template'],
            'username': 'testuser',
            'project_type': get_project_type_by_name("Python Library")
        }
        
        # Generate README
        template = READMETemplate(config)
        readme_content = template.generate()
        
        print(f"✅ README generated successfully ({len(readme_content)} characters)")
        print("\nFirst 500 characters:")
        print("-" * 50)
        print(readme_content[:500])
        print("-" * 50)
        
        # Check for key sections
        required_sections = [
            "# test-project",
            "## 📖 About",
            "## ✨ Features", 
            "## 🚀 Installation",
            "## 📖 Usage",
            "## 🤝 Contributing",
            "## 📄 License"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in readme_content:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"❌ Missing sections: {missing_sections}")
            return False
        else:
            print("✅ All required sections present")
            return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_different_project_types():
    """Test README generation for different project types"""
    print("\nTesting different project types...")
    
    try:
        from templates import READMETemplate, get_project_type_by_name
        
        project_types = ["Python Library", "JavaScript/Node.js Package", "Web Application"]
        
        for pt_name in project_types:
            print(f"\nTesting {pt_name}...")
            
            config = {
                'repo_name': f'test-{pt_name.lower().replace(" ", "-")}',
                'description': f'A test {pt_name.lower()} project',
                'license': 'mit',
                'topics': ['test', 'template'],
                'username': 'testuser',
                'project_type': get_project_type_by_name(pt_name)
            }
            
            template = READMETemplate(config)
            readme_content = template.generate()
            
            # Check for project-specific content
            if "Python" in pt_name and "pip install" in readme_content:
                print(f"✅ {pt_name}: Python-specific content found")
            elif "JavaScript" in pt_name and "npm install" in readme_content:
                print(f"✅ {pt_name}: JavaScript-specific content found")
            elif "Web Application" in pt_name and "npm install" in readme_content:
                print(f"✅ {pt_name}: Web app content found")
            else:
                print(f"⚠️ {pt_name}: Generic content")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Testing Template System\n")
    
    tests = [
        test_project_types,
        test_readme_template,
        test_different_project_types
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
