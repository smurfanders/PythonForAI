# /utils/setup_project.py

import logging.config
import os
import subprocess
import sys
import yaml

def setup_logging(config_path='utils/logging.yaml'):
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

def setup_project():
    # Check if a virtual environment is activated
    if 'VIRTUAL_ENV' not in os.environ:
        print("Virtual environment is not activated. Please activate the .venv environment before running this setup.")
        sys.exit(1)
    
    # Define the project root directory relative to this script's location
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Path to requirements.txt in the project root
    requirements_path = os.path.join(project_root, "requirements.txt")
    
    # Install dependencies
    try:
        subprocess.run(["pip", "install", "-r", requirements_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        sys.exit(1)
    
    # # Register the virtual environment as a Jupyter kernel
    # venv_name = os.path.basename(os.environ['VIRTUAL_ENV'])  # Or set a custom name
    # try:
    #     subprocess.run(["python", "-m", "ipykernel", "install", "--user", "--name", venv_name, "--display-name", f"Python ({venv_name})"], check=True)
    #     print(f"Jupyter kernel '{venv_name}' installed successfully.")
    # except subprocess.CalledProcessError as e:
    #     print(f"Failed to register the virtual environment as a Jupyter kernel: {e}")
    #     sys.exit(1)

    # Initialize Alembic if it hasn't been already
    alembic_path = os.path.join(project_root, "alembic")
    if not os.path.exists(alembic_path):
        try:
            subprocess.run(["alembic", "init", "alembic"], cwd=project_root, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to initialize Alembic: {e}")
            sys.exit(1)

if __name__ == "__main__":
    setup_project()
