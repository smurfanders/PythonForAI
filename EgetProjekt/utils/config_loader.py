# /utils/config_loader.py

from utils.setup_project import setup_logging  # Standardizes logging YAML configuration across the application.
from decouple import config as decouple_config  # Renamed to avoid confusion with the config dictionary
import os
import copy
import aiofiles # Asynchronous file I/O.
import yaml # YAML parsing.
import logging  # Application-wide logging framework.

# Initializes logging configuration for consistent application-wide logging.
# This step applies the logging settings defined in the YAML file to the logging module. 
# By calling this function, we ensure that all subsequent logging calls within the application 
# adhere to the configured settings, providing a consistent logging experience. 
# It is crucial to call this function before any logging is done to ensure the logging system is correctly configured.
setup_logging() 
# Initializes a module-level logger, organizing logs hierarchically and inheriting settings from the configured root logger.
# The getLogger function is called with the special variable __name__, which is automatically set to the name of 
# the current module in which this code is executed. This practice is recommended because it organizes logs in a hierarchical manner, 
# following the structure of the application's modules. 
# The created logger will inherit settings from the root logger, which was configured by the setup_logging call.
logger = logging.getLogger(__name__)

def load_config(file_name="config.yaml"):
    logger.info(f"Inside load_config")
    """
    Loads the YAML configuration file and enriches it with sensitive data from environment variables.

    Args:
        file_name (str): The filename of the YAML configuration file, defaults to 'config.yaml'.
    """
    # Determine the directory of this script file (__file__)
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # Construct the absolute path to the configuration file
    config_path = os.path.join(dir_path, file_name)

    with open(config_path, 'r') as file:
        yaml_config = yaml.safe_load(file)

    # Update API keys and secrets from environment variables
    yaml_config['exchanges']['binance']['api_key'] = decouple_config('BINANCE_API_KEY')
    yaml_config['exchanges']['binance']['api_secret'] = decouple_config('BINANCE_API_SECRET')
    yaml_config['exchanges']['kucoin']['api_key'] = decouple_config('KUCOIN_API_KEY', default='')
    yaml_config['exchanges']['kucoin']['api_secret'] = decouple_config('KUCOIN_API_SECRET', default='')

    return yaml_config

# Example usage
#exchange_config = load_config()

async def load_config_async(file_name="config.yaml"):
    logger.info(f"Inside load_config_async")
    """
    Asynchronously loads the YAML configuration file and enriches it with sensitive data from environment variables.

    Args:
        file_name (str): The filename of the YAML configuration file, defaults to 'config.yaml'.
    
    Returns:
        dict: The loaded and enriched configuration dictionary.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, file_name)

    async with aiofiles.open(config_path, 'r') as file:
        content = await file.read()
        yaml_config = yaml.safe_load(content)

    # Update API keys and secrets from environment variables
    yaml_config['exchanges']['binance']['api_key'] = decouple_config('BINANCE_API_KEY')
    yaml_config['exchanges']['binance']['api_secret'] = decouple_config('BINANCE_API_SECRET')
    yaml_config['exchanges']['kucoin']['api_key'] = decouple_config('KUCOIN_API_KEY', default='')
    yaml_config['exchanges']['kucoin']['api_secret'] = decouple_config('KUCOIN_API_SECRET', default='')

    return yaml_config

def save_config(config_data, file_name="config.yaml"):
    logger.info(f"Inside save_config")
    """
    Saves the updated configuration data back to the YAML configuration file.

    Parameters:
        config_data (dict): The updated configuration data to save.
        file_name (str): The filename of the YAML configuration file, defaults to 'config.yaml'.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, file_name)

    try:
        with open(config_path, 'w') as file:
            yaml.dump(config_data, file)
        logger.info("save_config Configuration saved successfully.")
    except Exception as e:
        logger.error(f"save_config Failed to save configuration: {e}")

async def save_config_async(config_data, file_name="config.yaml"):
    logger.info(f"Inside save_config_async")
    """
    Saves the updated configuration data back to the YAML configuration file.

    Parameters:
        config_data (dict): The updated configuration data to save.
        file_name (str): The filename of the YAML configuration file, defaults to 'config.yaml'.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_path = os.path.join(dir_path, file_name)
    sanitized_config = copy.deepcopy(config_data) # Create a deep copy of config_data to avoid mutating the original data
    for exchange in sanitized_config.get('exchanges', {}).values(): # Iterate through exchanges and remove sensitive data
        exchange.pop('api_key', None)
        exchange.pop('api_secret', None)
    try:
        async with aiofiles.open(config_path, 'w') as file:
            yaml_content = yaml.dump(sanitized_config) # Correctly handling YAML dump before writing
            await file.write(yaml_content)
        logger.info("save_config_async Configuration asynchronously saved successfully.")
    except Exception as e:
        logger.error(f"save_config_async Failed to asynchronously save configuration: {e}")