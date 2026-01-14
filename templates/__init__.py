"""
Template system for RepoSpark
Provides professional templates for GitHub repository files
"""
# Author: Rich Lewis - GitHub: @RichLewis007

from .readme_template import READMETemplate
from .project_types import ProjectType, get_project_types, get_project_type_by_name, get_project_type_by_id, get_project_type_names

__all__ = [
    'READMETemplate', 
    'ProjectType', 
    'get_project_types',
    'get_project_type_by_name',
    'get_project_type_by_id', 
    'get_project_type_names'
]
