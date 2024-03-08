# /data_fetching/fear_greed_data.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from db.database_operations import initialize_intermediary_greedbase_async, get_or_create_greed_source_async, get_or_create_greed_record_async
from utils.config_loader import load_config_async
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import aiohttp
import aiofiles
import csv
import json
import pandas
import logging  # Provides a flexible framework for logging in Python applications.

setup_logging() 
logger = logging.getLogger(__name__)

def convert_greed_value_to_rating(greed_value: int):
    """
    Converts a numerical greed value into a descriptive rating.
    
    Parameters:
    - greed_value (int): The numerical representation of greed.

    Returns:
    - str: A descriptive string representing the level of greed.
    """
    if 0 <= greed_value <= 24:
        return 'extreme fear'
    elif 25 <= greed_value <= 44:
        return 'fear'
    elif 45 <= greed_value <= 54:
        return 'neutral'
    elif 55 <= greed_value <= 74:
        return 'greed'
    elif 75 <= greed_value <= 100:
        return 'extreme greed'
    else:
        return 'unknown'

async def db_data_to_dataframe(exchange_symbol_data):
    """
    Converts cryptocurrency data into a pandas DataFrame.

    This function takes the raw data fetched from the database and transforms it into
    a structured pandas DataFrame format, facilitating easier manipulation and visualization.

    Args:
        exchange_symbol_data (list): A list of data record objects fetched from the database.

    Returns:
        pd.DataFrame: A DataFrame containing structured cryptocurrency data.
    """
    # Attempt to transform the data into a DataFrame.
    try:
        exchange_data = [{
            #"timestamp": datetime.datetime.fromtimestamp(data_records.timestamp).strftime('%Y-%m-%d %H:%M'),
            "timestamp": data_records.timestamp,  # Do not convert to string here if epoch time is needed for aggregation
            "open": data_records.open,
            "high": data_records.high,
            "low": data_records.low,
            "close": data_records.close,
            "volume": data_records.volume
        } for data_records in exchange_symbol_data]
        exchange_df = pandas.DataFrame(exchange_data)
        #exchange_df['timestamp'] = pandas.to_datetime(exchange_df['timestamp'], unit='s')  # Adjust based on actual timestamp unit if different
        print(f"exchange_df:{exchange_df}")
        return exchange_df
    except Exception as e:
        logger.error(f"Failed to convert db_data_to_dataframe: {e}", exc_info=True)
        # Optionally raise the exception to halt the execution or handle it accordingly.
        raise

async def greed_db_data_to_dataframe(greed_records_data):
    """
    Converts greed data FGI data into a pandas DataFrame.

    This function takes the raw data fetched from the database and transforms it into
    a structured pandas DataFrame format, facilitating easier manipulation and visualization.

    Args:
        greed_records_data (list): A list of data record objects fetched from the database.

    Returns:
        pd.DataFrame: A DataFrame containing structured cryptocurrency data.
    """
    # Attempt to transform the data into a DataFrame.
    try:
        greed_data = [{
            #"timestamp": datetime.datetime.fromtimestamp(greed_record.timestamp).strftime('%Y-%m-%d %H:%M'),
            "timestamp": greed_record.timestamp, # Do not convert to string here if epoch time is needed for aggregation
            "greed_value": greed_record.greed_value,
            "greed_rating": greed_record.greed_rating,
        } for greed_record in greed_records_data]
        greed_df = pandas.DataFrame(greed_data)
        #greed_df['timestamp'] = pandas.to_datetime(greed_df['timestamp'], unit='s')  # Adjust based on actual timestamp unit if different
        print(f"greed_df:{greed_df}")
        return greed_df
    except Exception as e:
        logger.error(f"Failed to convert greed_db_data_to_dataframe: {e}", exc_info=True)
        # Optionally raise the exception to halt the execution or handle it accordingly.
        raise

async def orchestrate_greed_data_to_db_pipeline(greed_source_name: str):
    """
    Orchestrates the pipeline for fetching and storing greed data into the database.
    
    Parameters:
    - greed_source_name (str): Identifier for the greed data source.
    """
    AsyncGreedSessionFactory, _ = await initialize_intermediary_greedbase_async()
    if not isinstance(greed_source_name, str):
        logger.error(f"Invalid orchestrate_greed_data_to_db_pipeline type: {type(greed_source_name)}. Expected string or None.")
        return None
    async with AsyncGreedSessionFactory() as greed_db_session:
        greedsource = await get_or_create_greed_source_async(greed_db_session, greed_source_name)
        logger.info(f"orchestrate_greed_data_to_db_pipeline obtained or created GreedSource:{greedsource.name}")
        if greed_source_name.startswith('csv_'):
            await csv_greed_data_to_db_async(greed_source_name, greed_db_session)
        else:
            await fetch_greed_data_to_db_async(greed_source_name, greed_db_session)


async def fetch_greed_data_to_db_async(greed_source_name: str, existing_greed_db_session=None):
    """
    Fetches greed data from a remote source and stores it in the database.
    
    Parameters:
    - greed_source_name (str): The name of the greed data source.
    - existing_greed_db_session (Session, optional): An existing database session, if any.
    """
    if not isinstance(greed_source_name, str):
        logger.error(f"Invalid fetch_greed_data_to_db_async type: {type(greed_source_name)}. Expected string or None.")
        return None
    greed_config = await load_config_async()
    greed_db_session = existing_greed_db_session
    greed_source_config = greed_config['greedsources'].get(greed_source_name)
    greed_source_timestamp_divide = greed_source_config['timestamp_divide']
    print(f"{greed_source_timestamp_divide}")
    if not greed_source_config:
        logger.error(f"Configuration fetch_greed_data_to_db_async {greed_source_name} not found.")
        return
    close_greed_db_session = False
    if not existing_greed_db_session:
        logger.info(f"fetch_greed_data_to_db_async Starting new session: {greed_source_name}")
        greed_session_factory, _ = await initialize_intermediary_greedbase_async()
        greed_db_session = greed_session_factory()
        close_greed_db_session = True
    try:
        async with aiohttp.ClientSession() as greed_http_session:
            print(f"fetch_greed_data_to_db_async URL:{(greed_source_config['url'])}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)\
                AppleWebKit/537.36 (KHTML, like Gecko)\
                Chrome/58.0.3029.110 Safari/537.3',
                'Accept': 'application/json',
            }
            greed_response = await greed_http_session.get(greed_source_config['url'], headers=headers)
            if greed_response.status != 200:
                logger.error(f"Failed to fetch_greed_data_to_db_async from:{greed_source_name} Status:{greed_response.status}")
                return None
            try:
                greed_http_data = await greed_response.json()
            except json.JSONDecodeError as e:
                logger.error(f"fetch_greed_data_to_db_async JSON parsing error:{greed_source_name}:{e}")
                return
            except aiohttp.ClientError as e:
                logger.error(f"fetch_greed_data_to_db_async HTTP request error:{greed_source_name}:{e}")
                return
            except Exception as e:
                logger.error(f"fetch_greed_data_to_db_async unknown error:{greed_source_name}:{e}")
                return
            for key in greed_source_config['path_to_data'].split('.'):
                greed_http_data = greed_http_data.get(key, [])
            for item in greed_http_data:
                timestamp = int(item[greed_source_config['mappings']['timestamp']]) // greed_source_timestamp_divide
                greed_value = int(item[greed_source_config['mappings']['greed_value']])
                greed_rating = convert_greed_value_to_rating(greed_value).lower()
                await get_or_create_greed_record_async(greed_db_session, greed_source_name, timestamp, greed_value, greed_rating)
    except aiohttp.ClientError as e:
        logger.error(f"fetch_greed_data_to_db_async aiohttp client error while updating:{greed_source_name}:{e}")
        raise
    except SQLAlchemyError as e:
        logger.error(f"fetch_greed_data_to_db_async Database error:{greed_source_name}:{e}")
        raise
    except Exception as e:
        logger.error(f"fetch_greed_data_to_db_async Unexpected error:{greed_source_name}:{e}")
        raise
    finally: # Clean up the greed client and database session
        if close_greed_db_session:
            await greed_db_session.close()
            logger.info("fetch_greed_data_to_db_async greed_db_session closed.")

async def csv_greed_data_to_db_async(greed_source_name: str, existing_greed_db_session=None):
    """
    Asynchronously processes greed data from a CSV file and stores it in the database.

    This function reads greed-related data (such as greed values and timestamps) from a specified
    CSV file, converts the data into a consistent format, and then stores it in the database
    using an existing or a new database session.

    Parameters:
    - greed_source_name (str): The unique identifier for the greed data source as specified in the configuration.
    - existing_greed_db_session (AsyncSession, optional): An optional existing SQLAlchemy async session
      to be used for database operations. If not provided, a new session is created.

    Returns:
    - None. However, it updates the database with greed data from the CSV file.

    Raises:
    - SQLAlchemyError: If any database operation fails.
    - Exception: For any unexpected errors during the file processing or database update.
    """
    # Validate greed_source_name type
    if not isinstance(greed_source_name, str):
        logger.error(f"Invalid csv_greed_data_to_db_async type:{type(greed_source_name)}. Expected string or None.")
        return None
    # Load configuration settings
    greed_config = await load_config_async()
    # Retrieve the specific configuration for the given greed source
    if greed_source_name not in greed_config['greedsources']:
        logger.error(f"Configuration csv_greed_data_to_db_async:{greed_source_name} not found.")
        return
    greed_source_config = greed_config['greedsources'].get(greed_source_name)
    greed_db_session = existing_greed_db_session
    close_greed_db_session = False
    # Initialize database session if not already provided
    if not existing_greed_db_session:
        logger.info(f"csv_greed_data_to_db_async Starting new session:{greed_source_name}")
        greed_session_factory, _ = await initialize_intermediary_greedbase_async()
        greed_db_session = greed_session_factory()
        close_greed_db_session = True
    # Define function for parsing timestamp based on the source configuration
    if 'timestamp_format' in greed_source_config:
        # If timestamp is provided in a date format
        def parse_greed_timestamp(greed_csv_row):
            return int(datetime.strptime(greed_csv_row[greed_source_config['timestamp_column']], greed_source_config['timestamp_format']).timestamp())
    elif greed_source_config.get('timestamp_divide', 1) != 1:
        # If timestamp is in epoch format and needs to be divided (e.g., milliseconds to seconds)
        def parse_greed_timestamp(greed_csv_row):
            return int(greed_csv_row[greed_source_config['timestamp_column']]) // greed_source_config['timestamp_divide']
    else:
        # If timestamp is in epoch format (seconds)
        def parse_greed_timestamp(greed_csv_row):
            return int(greed_csv_row[greed_source_config['timestamp_column']])
    # Process and store data from CSV
    try:
        async with aiofiles.open(greed_source_config['greed_csv_path'], mode='r', encoding='utf-8') as greed_file:
            greed_csv_content = await greed_file.read()
            greed_reader = csv.DictReader(greed_csv_content.splitlines())
            for greed_csv_row in greed_reader:
                try:
                    timestamp = parse_greed_timestamp(greed_csv_row)
                    greed_value = int(float(greed_csv_row[greed_source_config['greed_value_column']]))
                    greed_rating = convert_greed_value_to_rating(greed_value).lower()
                    await get_or_create_greed_record_async(greed_db_session, greed_source_name, timestamp, greed_value, greed_rating)
                except Exception as e:
                    logger.error(f"csv_greed_data_to_db_async Error processing row {greed_csv_row}: {e}")
    except SQLAlchemyError as e:
        logger.error(f"csv_greed_data_to_db_async Database error:{e} for {greed_source_name}")
        raise
    except Exception as e:
        logger.error(f"csv_greed_data_to_db_async Unexpected error:{e} for {greed_source_name}")
        raise
    finally:
        # Cleanup: Close the database session if it was opened in this function
        if close_greed_db_session:
            await greed_db_session.close()
            logger.info("csv_greed_data_to_db_async greed_db_session closed.")