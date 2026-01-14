"""
Project type definitions for RepoSpark
Defines different project types and their specific configurations
"""
# Author: Rich Lewis - GitHub: @RichLewis007

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ProjectType:
    """Represents a project type with its specific configurations"""
    id: str
    name: str
    description: str
    language: str
    package_manager: str
    test_framework: str
    linting_tools: List[str]
    ci_cd: str
    badges: List[str]
    installation_cmd: str
    usage_example: str
    file_extensions: List[str]
    dependencies: List[str]
    dev_dependencies: List[str]


def get_project_types() -> Dict[str, ProjectType]:
    """Get all available project types"""
    return {
        "other": ProjectType(
            id="other",
            name="Other",
            description="A generic project with basic structure",
            language="Generic",
            package_manager="None",
            test_framework="None",
            linting_tools=[],
            ci_cd="GitHub Actions",
            badges=[
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="",
            usage_example="""```bash
# Clone the repository
git clone https://github.com/{username}/{repo_name}.git
cd {repo_name}

# Follow the project's specific setup instructions
```""",
            file_extensions=[],
            dependencies=[],
            dev_dependencies=[]
        ),
        
        "python-library": ProjectType(
            id="python-library",
            name="Python Library",
            description="A standard Python package/library",
            language="Python",
            package_manager="pip",
            test_framework="pytest",
            linting_tools=["black", "flake8", "mypy"],
            ci_cd="GitHub Actions",
            badges=[
                "![Python](https://img.shields.io/badge/python-3.8+-blue.svg)",
                "![PyPI](https://img.shields.io/pypi/v/{package_name}.svg)",
                "![Tests](https://github.com/{username}/{repo_name}/workflows/Tests/badge.svg)",
                "![Code Coverage](https://codecov.io/gh/{username}/{repo_name}/branch/main/graph/badge.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="pip install {package_name}",
            usage_example="""```python
import {package_name}

# Basic usage
result = {package_name}.main_function()
print(result)
```""",
            file_extensions=[".py", ".pyi"],
            dependencies=[],
            dev_dependencies=["pytest", "black", "flake8", "mypy", "coverage"]
        ),
        
        "python-cli": ProjectType(
            id="python-cli",
            name="Python CLI Tool",
            description="A command-line interface tool",
            language="Python",
            package_manager="pip",
            test_framework="pytest",
            linting_tools=["black", "flake8"],
            ci_cd="GitHub Actions",
            badges=[
                "![Python](https://img.shields.io/badge/python-3.8+-blue.svg)",
                "![PyPI](https://img.shields.io/pypi/v/{package_name}.svg)",
                "![Tests](https://github.com/{username}/{repo_name}/workflows/Tests/badge.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="pip install {package_name}",
            usage_example="""```bash
# Install the tool
pip install {package_name}

# Use the CLI
{package_name} --help
{package_name} command --option value
```""",
            file_extensions=[".py"],
            dependencies=["click"],
            dev_dependencies=["pytest", "black", "flake8"]
        ),
        
        "javascript-package": ProjectType(
            id="javascript-package",
            name="JavaScript/Node.js Package",
            description="A Node.js package/library",
            language="JavaScript",
            package_manager="npm",
            test_framework="jest",
            linting_tools=["eslint", "prettier"],
            ci_cd="GitHub Actions",
            badges=[
                "![Node.js](https://img.shields.io/badge/node.js-16+-green.svg)",
                "![npm](https://img.shields.io/npm/v/{package_name}.svg)",
                "![Tests](https://github.com/{username}/{repo_name}/workflows/Tests/badge.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="npm install {package_name}",
            usage_example="""```javascript
const {package_name} = require('{package_name}');

// Basic usage
const result = {package_name}.mainFunction();
console.log(result);
```""",
            file_extensions=[".js", ".ts"],
            dependencies=[],
            dev_dependencies=["jest", "eslint", "prettier"]
        ),
        
        "web-application": ProjectType(
            id="web-application",
            name="Web Application",
            description="A full-stack web application",
            language="JavaScript/Python",
            package_manager="npm/pip",
            test_framework="jest/pytest",
            linting_tools=["eslint", "prettier"],
            ci_cd="GitHub Actions",
            badges=[
                "![Deploy](https://github.com/{username}/{repo_name}/workflows/Deploy/badge.svg)",
                "![Tests](https://github.com/{username}/{repo_name}/workflows/Tests/badge.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="npm install && pip install -r requirements.txt",
            usage_example="""```bash
# Install dependencies
npm install
pip install -r requirements.txt

# Run development server
npm run dev
# or
python app.py
```""",
            file_extensions=[".js", ".ts", ".py", ".html", ".css"],
            dependencies=["express", "react"],
            dev_dependencies=["jest", "eslint", "prettier"]
        ),
        
        "data-science": ProjectType(
            id="data-science",
            name="Data Science Project",
            description="A data science or machine learning project",
            language="Python",
            package_manager="pip",
            test_framework="pytest",
            linting_tools=["black", "flake8"],
            ci_cd="GitHub Actions",
            badges=[
                "![Python](https://img.shields.io/badge/python-3.8+-blue.svg)",
                "![Jupyter](https://img.shields.io/badge/jupyter-notebook-orange.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="pip install -r requirements.txt",
            usage_example="""```python
# Install dependencies
pip install -r requirements.txt

# Run Jupyter notebook
jupyter notebook

# Or run scripts
python train_model.py
python evaluate.py
```""",
            file_extensions=[".py", ".ipynb", ".md"],
            dependencies=["numpy", "pandas", "matplotlib", "scikit-learn"],
            dev_dependencies=["pytest", "black", "flake8", "jupyter"]
        ),
        
        "documentation": ProjectType(
            id="documentation",
            name="Documentation Site",
            description="A documentation website",
            language="Markdown/HTML",
            package_manager="npm",
            test_framework="None",
            linting_tools=["markdownlint"],
            ci_cd="GitHub Actions",
            badges=[
                "![Deploy](https://github.com/{username}/{repo_name}/workflows/Deploy/badge.svg)",
                "![License](https://img.shields.io/badge/license-{license}-green.svg)"
            ],
            installation_cmd="npm install",
            usage_example="""```bash
# Install dependencies
npm install

# Build documentation
npm run build

# Serve locally
npm run serve
```""",
            file_extensions=[".md", ".html", ".css", ".js"],
            dependencies=["vuepress", "docusaurus"],
            dev_dependencies=["markdownlint"]
        )
    }


def get_project_type_by_id(project_id: str) -> Optional[ProjectType]:
    """Get a specific project type by ID"""
    project_types = get_project_types()
    return project_types.get(project_id)


def get_project_type_names() -> List[str]:
    """Get list of project type names for UI"""
    project_types = get_project_types()
    return [pt.name for pt in project_types.values()]


def get_project_type_by_name(name: str) -> Optional[ProjectType]:
    """Get project type by display name"""
    project_types = get_project_types()
    for pt in project_types.values():
        if pt.name == name:
            return pt
    return None
