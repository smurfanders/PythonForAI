# /notebooks/rootPath_setup.py

import os
import sys

def add_project_root_to_path():
    """
    Adds the project root directory to sys.path to enable imports from the entire project.
    This script resides in the 'notebooks' directory located one level below the project root.
    """
    notebook_dir = os.path.abspath(os.getcwd())
    project_root = os.path.dirname(notebook_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"Added {project_root} to sys.path")
    else:
        print(f"{project_root} is already in sys.path")
