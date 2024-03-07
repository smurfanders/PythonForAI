# /utils/logger.py

import logging.config
import yaml
import os

def setup_logging(default_path='utils/logging.yaml', default_level=logging.DEBUG, env_key='LOG_CFG'):
    """
    Set up logging configuration from a YAML file.

    Args:
        default_path (str): Default path to the logging configuration file.
        default_level (logging.Level): Default logging level if configuration file is not found.
        env_key (str): Environment variable key for dynamically specifying the logging configuration file path.
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)
        logging.warning('Failed to load logging configuration from {}. Using default settings.'.format(default_path))
