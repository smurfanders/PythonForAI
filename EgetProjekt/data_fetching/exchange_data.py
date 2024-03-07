# /data_fetching/exchange_data.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from db.models_exchangeData import DataRecord
from db.database_operations import initialize_intermediary_database_async, get_or_create_exchange_async, get_or_create_symbol_async
from utils.config_loader import load_config_async, save_config_async
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select # Correct import for async operations
from typing import Dict
import ccxt
import ccxt.async_support as ccxt_async
import time
import datetime
import aiohttp
import asyncio
import logging  # Provides a flexible framework for logging in Python applications.

setup_logging() 
logger = logging.getLogger(__name__)

def fetch_data_from_binance_ccxt(symbol):
    """
    Fetches ticker data from Binance for a specified symbol using the CCXT library.

    Args:
        symbol (str): The trading symbol or pair (e.g., 'BTC/USDT').
    
    Returns:
        dict: The JSON response from the Binance API, parsed into a dictionary.

    Logs an error message and returns None if an error occurs during the API call.
    """
    exchange = ccxt.binance({
        'rateLimit': True,  # Enable CCXT's built-in rate limiting mechanism
        'enableRateLimit': True,  # More explicit flag to enable rate limiting
        'verbose': False,  # Set to False to reduce console output, True for debugging
    })

    try:
        data = exchange.fetch_ticker(symbol)
        logger.info(f"fetch_data_from_binance_ccxt Ticker data fetched successfully for {symbol}")
        return data
    except ccxt.NetworkError as e:
        logger.error(f"fetch_data_from_binance_ccxt Network error while fetching ticker for {symbol}: {e}")
        time.sleep(10)  # Optional: Retry after a delay based on the application's requirements
    except ccxt.ExchangeError as e:
        logger.error(f"Exchange fetch_data_from_binance_ccxt error while fetching ticker for {symbol}: {e}")
    except ccxt.BaseError as e:
        logger.error(f"CCXT base fetch_data_from_binance_ccxt error while fetching ticker for {symbol}: {e}")
    except Exception as e:
        logger.error(f"Unexpected fetch_data_from_binance_ccxt error while fetching ticker for {symbol}: {e}")

    return None

# # Example usage
# symbol = "BTCUSDT"  # Example symbol
# ticker_data = fetch_data_from_binance_ccxt(symbol)
# if ticker_data:
#     print(ticker_data)  # Process or log the data as needed
# else:
#     logger.info("Failed to fetch ticker data.")

async def handle_rate_limit_errors(exchange_name: str, status: int, headers: Dict[str, str]):
    logger.info(f"Handling rate limit errors for {exchange_name} with status {status}")
    exchange_config = await load_config_async() # Load configuration asynchronously
    default_cooldown_period = exchange_config['exchanges'].get(exchange_name, {}).get('rate_limit_cooldown', 60) # Default cooldown period
    if status == 429:  # Rate limit exceeded
        retry_after = int(headers.get('Retry-After', default_cooldown_period))
        logger.warning(f"HTTP 429 Rate Limit Exceeded received from {exchange_name}. Waiting for {retry_after} seconds.")
        await asyncio.sleep(retry_after)
    elif status == 418:  # IP ban
        retry_after = int(headers.get('Retry-After', default_cooldown_period))
        logger.warning(f"HTTP 418 IP Ban received from {exchange_name}. IP banned. Waiting for {retry_after} seconds before retrying.")
        await asyncio.sleep(retry_after)
    else:  # Other 5XX errors or fallback
        logger.warning(f"5XX response or other error received from {exchange_name}. Initiating cooldown for {default_cooldown_period} seconds.")
        await asyncio.sleep(default_cooldown_period)

async def adjust_start_date_async(exchange_name, symbol, initial_start_date, http_session):
    #logger.info(f"Inside adjust_start_date_async with intial start date: {initial_start_date} exchange: {exchange_name} and symbol: {symbol}")
    exchange_config = await load_config_async()
    #adjusted_start_date = datetime.datetime.fromtimestamp(initial_start_date) # Initialize the start_date as a datetime object from the given epoch timestamp
    base_url = exchange_config['exchanges'][exchange_name]['base_url']
    ohlcv_endpoint = exchange_config['exchanges'][exchange_name]['endpoints']['ohlcv']
    #api_limit = exchange_config['exchanges'][exchange_name]['api_limit']
    # Convert initial start date from timestamp to milliseconds
    adjusted_start_date = int(initial_start_date * 1000) # Convert to milliseconds
    # Define the interval for trying to fetch data
    interval = '1d'  # Daily intervals; adjust as needed
    #interval_adjust_start = (24 * 60 * 60 * 1000)
    ohlcv_url = f"{base_url}{ohlcv_endpoint}?symbol={symbol}&interval={interval}&startTime={adjusted_start_date}&limit=10"
    #logger.debug(f"OHLCV URL: {ohlcv_url}")

    async with http_session.get(ohlcv_url) as response:
        logger.info(f"adjust_start_date_async from:{datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
        if response.status == 200:
            ohlcv_data = await response.json()
            if ohlcv_data and len(ohlcv_data) > 0:
                adjusted_start_date = ohlcv_data[0][0]
                logger.info(f"adjust_start_date_async start date to:{datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
                return adjusted_start_date // 1000
            else:
                logger.info(f"No data found after: {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
                return None
        else:
            logger.error(f"Failed to fetch adjust_start_date_async HTTP {response.status}")
            return None
    # while True:
    #     try:
    #         # Construct the URL with the required parameters
    #         #api_params = {"symbol": {symbol}, "interval": {interval}, "startTime": {adjusted_start_date}, "limit": {api_limit}}
    #         ohlcv_url = f"{base_url}{ohlcv_endpoint}?symbol={symbol}&interval={interval}&startTime={adjusted_start_date}&limit={api_limit}"
    #         logger.debug(f"OHLCV URL: {ohlcv_url}")
    #         async with http_session.get(ohlcv_url) as response:
    #             if response.status == 200:
    #                 ohlcv_data = await response.json()
    #                 logger.debug(f"Raw API response: {ohlcv_data}")
    #                 if ohlcv_data and len(ohlcv_data) > 0:
    #                     # Successfully found data for the start date
    #                     logger.info(f"Trying to start data fetching from: {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
    #                     break  # Exit the loop as we've found the earliest data point
    #                 else:
    #                     # No data found for the given start date, try the next day
    #                     logger.debug(f"No data found for: {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}, trying next day.")
    #                     adjusted_start_date += interval_adjust_start 
    #                 logger.error(f"Error fetching data for: {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}: HTTP {response.status}")
    #                 adjusted_start_date += interval_adjust_start
    #     except Exception as e:
    #         logger.error(f"Unexpected adjust_start_date_async error: {e}")
    #         adjusted_start_date += interval_adjust_start
    # logger.info(f"Found data and adjusted start date to: {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
    # return adjusted_start_date // 1000 # Return the epoch timestamp of the adjusted start date

async def fetch_ohlcv_async(exchange_name, symbol, interval, adjusted_start_date, api_limit, http_session):
    exchange_config = await load_config_async()
    exchange_config = exchange_config
    base_url = exchange_config['exchanges'][exchange_name]['base_url']
    ohlcv_endpoint = exchange_config['exchanges'][exchange_name]['endpoints']['ohlcv']
    since = int(adjusted_start_date * 1000)  # Convert adjusted_start_date to milliseconds
    ohlcv_url = f"{base_url}{ohlcv_endpoint}?symbol={symbol}&interval={interval}&startTime={since}&limit={api_limit}"
    logger.info(f"fetch_ohlcv_async data for {symbol} with {interval} interval starting from:{datetime.datetime.fromtimestamp(adjusted_start_date)}")
    try:
        async with http_session.get(ohlcv_url) as response:
            if response.status == 200:
                ohlcv_data = await response.json()
                if ohlcv_data:
                    logger.info(f"Successfully fetched {len(ohlcv_data)} data points.")
                    return ohlcv_data
                else:
                    logger.warning(f"No data returned for {symbol} starting from {datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}")
                    return []
            else:
                logger.error(f"Failed to fetch OHLCV data: HTTP {response.status}")
                return []
    except Exception as e:
        logger.error(f"Error fetching OHLCV data: {e}")
        return []

# Example call to fetch_ohlcv_async
# candles = await fetch_ohlcv_async('binance', 'BTCUSDT', '1d', adjusted_start_epoch, 1000, http_session)

async def orchestrate_exchange_data_to_db_pipeline(exchange_name: str, symbol_name: str, start_epoch, end_epoch, timeframe='1d'):
    """
    Coordinates the entire process of data fetching and storage, including session management and any pre/post processing steps.
    """
    session_factory, _ = await initialize_intermediary_database_async()
    #logger.info(f"Orchestrating {exchange_name} to db pipeline")
    if not isinstance(exchange_name, str):
        logger.error(f"Invalid orchestrate_exchange_data_to_db_pipeline exchange_name type: {type(exchange_name)}. Expected string.")
        return None
    async with session_factory() as db_session:
        exchange = await get_or_create_exchange_async(db_session, exchange_name) # Assuming `get_or_create_exchange_async` and other operations are correctly handling the session
        logger.info(f"Exchange orchestrate_exchange_data_to_db_pipeline obtained or created: {exchange.name}")
        if not isinstance(exchange_name, str):
            logger.error(f"Invalid orchestrate_exchange_data_to_db_pipeline exchange_name type: {type(exchange_name)}. Expected string.")
            return None
        await fetch_exchange_data_to_db_async(exchange_name, symbol_name, start_epoch, end_epoch, timeframe, db_session)

# Example usage in a Jupyter Notebook cell
# asyncio.run(orchestrate_exchange_data_to_db_pipeline('binance', 'BTC/USDT', start_epoch, end_epoch, '1d'))
    
async def fetch_exchange_data_to_db_async(exchange_name: str, symbol_name: str, start_epoch: int, end_epoch: int, timeframe='1d', existing_session=None, http_session=None):
    """
    Fetches historical OHLCV data for a specified symbol and timeframe from an exchange and stores it in the database.

    Args:
        exchange_name (str): The name of the cryptocurrency exchange (e.g., 'Binance').
        symbol_name (str): The symbol or trading pair to fetch data for (e.g., 'BTC/USDT').
        start_epoch (int): The start date for data fetching as an epoch timestamp.
        end_epoch (int): The end date for data fetching as an epoch timestamp.
        timeframe (str): The timeframe or interval for the data (e.g., '1h' for one hour).
        existing_session (Session, optional): An existing SQLAlchemy session.
    
    This function utilizes the CCXT library to interact with the exchange's API and fetch the OHLCV data
    for the specified symbol and timeframe. It checks for data duplication before storing new records
    to ensure the database contains unique entries for each timestamp. The function handles various
    errors such as network errors, exchange-specific errors, and database errors gracefully.
    Implements backoff strategy when approaching rate limit.
    """
    logger.info(f"Inside fetch_exchange_data_to_db_async for {exchange_name}: {symbol_name} from {start_epoch} to {end_epoch} with timeframe {timeframe}")
    if not isinstance(exchange_name, str):
        logger.error(f"fetch_exchange_data_to_db_async Invalid exchange_name type: {type(exchange_name)}. Expected string.")
        return None
    exchange_name = exchange_name.lower()
    exchange_config = await load_config_async()
    exchange_config = exchange_config
    cooldown_period = exchange_config['exchanges'][exchange_name].get('rate_limit_cooldown', 60)  # Default to 60 seconds
    api_limit = int(exchange_config['exchanges'][exchange_name]['api_limit'])
    rate_limit = int(exchange_config['exchanges'][exchange_name]['rate_limit'])
    raw_rate_limit = int(exchange_config['exchanges'][exchange_name]['raw_rate_limit'])
    """
    Initialize the exchange client using ccxt.async_support
    """
    db_session = existing_session
    close_session = False
    # Initialize the database session asynchronously
    if not existing_session:
        logger.info(f"fetch_exchange_data_to_db_async Starting new session: {exchange_name}")
        session_factory, _ = await initialize_intermediary_database_async()
        db_session = session_factory()
        close_session = True
    try:
        #logger.info(f"Inside fetch_exchange_data_to_db_async first try:")
        try:
            #logger.info(f"Inside fetch_exchange_data_to_db_async second try:")
            symbol = await get_or_create_symbol_async(db_session, exchange_name, symbol_name) # Ensure the symbol exists in the database and create it if not
            logger.info(f"{exchange_name} symbol obtained: {symbol.name}")
        except Exception as e:
            logger.error(f"fetch_exchange_data_to_db_async Error fetching symbol: {e}")
            raise
        async with aiohttp.ClientSession() as http_session:
            base_url = exchange_config['exchanges'][exchange_name]['base_url']
            exchangeInfo_endpoint = exchange_config['exchanges'][exchange_name]['endpoints']['exchangeInfo']
            api_limit = exchange_config['exchanges'][exchange_name]['api_limit']
            exchangeInfo_url = f"{base_url}{exchangeInfo_endpoint}"
            await fetch_binance_rate_limit_async(exchange_name, http_session)
            #logger.info(f"Rate limit for {exchange_name} fetched: {rate_limit['REQUEST_WEIGHT']['limit']}")
            adjusted_start_epoch = await adjust_start_date_async(exchange_name, symbol_name, start_epoch, http_session) # Adjust the start date based on the available data
            #logger.info(f"fetch_exchange_data_to_db_async Processing fetched data for {symbol_name} starting from epoch {adjusted_start_epoch}")
            while adjusted_start_epoch < end_epoch:  # Main logic to fetch OHLCV data in a loop until the entire requested timeframe is covered
                #logger.debug(f"fetch_exchange_data_to_db_async Rate limit info: {rate_limit}")
                # Check if we are approaching the rate limit
                async with http_session.get(exchangeInfo_url) as response:
                    if response.status == 200:
                        await check_and_handle_rate_limit(response.headers, exchange_config, exchange_name)
                        # Extract rate limit info from headers
                        request_weight_used = int(response.headers.get('X-MBX-USED-WEIGHT-1M', '0'))
                        raw_requests_used = int(response.headers.get('X-MBX-USED-WEIGHT-5M', '0'))  # Adjust the key as per actual headers
                        # Implement logic to adjust request frequency based on these values
                        if request_weight_used >= rate_limit - 200:
                            logger.info(f"fetch_exchange_data_to_db_async Requests:{request_weight_used} Approaching limit:{rate_limit}. Initiating cooldown period of:{cooldown_period} seconds.")
                            await asyncio.sleep(cooldown_period)
                        elif raw_requests_used >= raw_rate_limit - 500:
                            logger.info(f"fetch_exchange_data_to_db_async Raw requests:{raw_requests_used} Approaching limit: {raw_rate_limit}. Initiating cooldown period of:{cooldown_period} seconds.")
                            await asyncio.sleep(cooldown_period)  # Cooldown period before next request
                        logger.info(f"fetch_exchange_data_to_db_async Requests:{request_weight_used} limit:{rate_limit} - Raw requests:{raw_requests_used} limit:{raw_rate_limit}.")
                        #logger.info(f"fetch_exchange_data_to_db_async OHLCV data for {symbol_name} starting at {datetime.datetime.fromtimestamp(adjusted_start_epoch)}")
                        candles = await fetch_ohlcv_async(exchange_name, symbol.name, timeframe, adjusted_start_epoch, api_limit, http_session)
                        for candle in candles: # Process each candle and store it in the database
                            timestamp = candle[0] // 1000 # Extract and convert timestamp
                            stmt = select(DataRecord).where(DataRecord.symbol_id == symbol.id, DataRecord.timestamp == timestamp)
                            result = await db_session.execute(stmt)
                            data_record = result.scalars().first()
                            if not data_record:  # Check for existing data to avoid duplicates and insert new data
                                data_record = DataRecord(symbol_id=symbol.id, timestamp=timestamp, open=candle[1], high=candle[2], low=candle[3], close=candle[4], volume=candle[5])
                                db_session.add(data_record)
                            if not candles or adjusted_start_epoch >= end_epoch:
                                logger.info("Reached the end date or no more data available. Stopping data fetch.")
                                break
                        await db_session.commit() # Commit the session to save changes to the database
                        adjusted_start_epoch = candles[-1][0] / 1000 + 1 if candles else end_epoch # Update the start_epoch for the next fetch operation
                    else:
                        # Handle non-200 responses
                        logger.error(f"Failed API call. Status: {response.status}")
                        # Potentially break or implement retry logic            
            await http_session.close() # Commit the session to save changes to the database    
    # Handle specific exceptions as needed, especially those related to rate limits, network issues, etc.
    except ccxt.NetworkError as e:
        logger.error(f"Network error while fetch_exchange_data_to_db_async for {symbol_name}: {e}", exc_info=True)
        handle_rate_limit_errors()  # Handle rate limit errors (e.g., HTTP 429) need to catch specific errors from CCXT that indicate rate limit has been hit.
    except ccxt.ExchangeError as e:
        logger.error(f"fetch_exchange_data_to_db_async Exchange error: {e}")
    except SQLAlchemyError as e:
        logger.error(f"fetch_exchange_data_to_db_async Database error: {e}")
    except Exception as e:
        logger.error(f"fetch_exchange_data_to_db_async Unexpected error: {e}")
        
    finally: # Clean up the exchange client and database session
        if close_session:
            logger.info("fetch_exchange_data_to_db_async Closing exchange client and database session.")
            await http_session.close()
        # if not existing_session:
        #     await session.close()
            
async def check_and_handle_rate_limit(response_headers, exchange_config, exchange_name):
    request_weight_used = int(response_headers.get('X-MBX-USED-WEIGHT-1M', '0'))
    raw_requests_used = int(response_headers.get('X-MBX-USED-WEIGHT-5M', '0'))
    rate_limit = exchange_config['exchanges'][exchange_name].get('rate_limit', 1200)
    raw_rate_limit = exchange_config['exchanges'][exchange_name].get('raw_rate_limit', 1200)
    cooldown_period = exchange_config['exchanges'][exchange_name].get('rate_limit_cooldown', 60)

    if request_weight_used >= rate_limit - 200:
        logger.info(f"REQUEST_WEIGHT {request_weight_used} approaching {rate_limit}. Cooling down for {cooldown_period} seconds.")
        await asyncio.sleep(cooldown_period)
    elif raw_requests_used >= raw_rate_limit - 500:
        logger.info(f"RAW_REQUESTS {raw_requests_used} approaching {raw_rate_limit}. Cooling down for {cooldown_period} seconds.")
        await asyncio.sleep(cooldown_period)

async def fetch_binance_rate_limit_async(exchange_name: str, http_session):
    """
    Asynchronously fetches and updates Binance API rate limit from the exchangeInfo endpoint,
    updating the application's configuration with the latest limit.

    Returns:
        dict: A dictionary containing the rate limit for various types of requests, or
        None if the rate limit couldn't be fetched.
    """
    #exchange_name = "binance"
    exchange_config = await load_config_async()
    logger.info(f"Inside fetch_binance_rate_limit_async after exchange_config with exchange_name: {exchange_name}")
    base_url = exchange_config['exchanges'][exchange_name]['base_url']
    exchangeInfo_endpoint = exchange_config['exchanges'][exchange_name]['endpoints']['exchangeInfo']
    exchangeInfo_url = f"{base_url}{exchangeInfo_endpoint}"
    #logger.info(f"Inside fetch_binance_rate_limit_async after url=exchange_config with exchange_name: {exchange_name}")
    try:
        logger.info(f"fetch_binance_rate_limit_async from URL: {exchangeInfo_url}")
        async with http_session.get(exchangeInfo_url) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch_binance_rate_limit_async {exchange_name} rate limit. HTTP Status: {response.status}")
                return None
            data = await response.json()
            request_weight_limit = next((limit for limit in data.get('rateLimits', []) if limit['rateLimitType'] == 'REQUEST_WEIGHT'), None) # Extracting the REQUEST_WEIGHT limit
            raw_request_weight_limit = next((limit for limit in data.get('rateLimits', []) if limit['rateLimitType'] == 'RAW_REQUESTS'), None) # Extracting the RAW_REQUESTS limit
            if request_weight_limit: # Update the rate limit in the configuration
                exchange_config['exchanges'][exchange_name]['rate_limit'] = request_weight_limit['limit']
                await save_config_async(exchange_config)  # Save the updated rate limit back to config.yaml
                logger.info(f"{exchange_name} REQUEST_WEIGHT fetch_binance_rate_limit_async updated to {request_weight_limit['limit']}.")
            if raw_request_weight_limit: # Update the rate limit in the configuration
                exchange_config['exchanges'][exchange_name]['raw_rate_limit'] = raw_request_weight_limit['limit']
                await save_config_async(exchange_config)  # Save the updated rate limit back to config.yaml
                logger.info(f"{exchange_name} RAW_REQUESTS fetch_binance_rate_limit_async updated to {raw_request_weight_limit['limit']}.")
            return request_weight_limit, raw_request_weight_limit
    except aiohttp.ClientError as e:
        logger.error(f"fetch_binance_rate_limit_async aiohttp client error while updating {exchange_name} rate limit: {e}")
        raise
    except Exception as e:
        logger.error(f"fetch_binance_rate_limit_async Unexpected error while updating {exchange_name} rate limit: {e}")
        raise

# Example usage
# await asyncio.run(fetch_binance_rate_limit_async())
    