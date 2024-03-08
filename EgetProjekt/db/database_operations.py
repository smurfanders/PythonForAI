# /db/database_operations.py

from operator import and_
from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from utils.config_loader import load_config
from .models_exchangeData import DataRecord, Exchange, Symbol, ExchangeBase # Ensure relative Exchange imports are correctly structured
from .models_greedData import GreedRecord, GreedSource, GreedBase # Ensure relative Greed imports are correctly structured
from sqlalchemy import exc, and_, distinct
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select # Correct import for async operations
from sqlalchemy.orm import sessionmaker
import logging  # Provides a flexible framework for logging in Python applications.

"""
Initializes logging configuration for consistent application-wide logging.
This step applies the logging settings defined in the YAML file to the logging module. 
By calling this function, we ensure that all subsequent logging calls within the application 
adhere to the configured settings, providing a consistent logging experience. 
It is crucial to call this function before any logging is done to ensure the logging system is correctly configured.
"""
setup_logging() 
"""
Initializes a module-level logger, organizing logs hierarchically and inheriting settings from the configured root logger.
The getLogger function is called with the special variable __name__, which is automatically set to the name of 
the current module in which this code is executed. This practice is recommended because it organizes logs in a hierarchical manner, 
following the structure of the application's modules. 
The created logger will inherit settings from the root logger, which was configured by the setup_logging call.
"""
logger = logging.getLogger(__name__)
exchange_config = load_config()

MAIN_DATABASE_URI = 'sqlite+aiosqlite:///db/main_exchangeData.sqlite'
INTERMEDIARY_DATABASE_URI = 'sqlite+aiosqlite:///db/intermediary_exchangeData.sqlite'
MAIN_GREEDBASE_URI = 'sqlite+aiosqlite:///db/main_greedData.sqlite'
INTERMEDIARY_GREEDBASE_URI = 'sqlite+aiosqlite:///db/intermediary_greedData.sqlite'

async def initialize_main_database_async(echo=False):
    logger.info("Inside initialize_main_database_async")
    """
    Initializes the main database engine and session factory asynchronously.
    
    Parameters:
        echo (bool): Enables the logging of SQL statements if True. Defaults to False.
    
    Returns:
        A tuple containing the session factory and engine for the main database.
    """
    main_engine_async = create_async_engine(MAIN_DATABASE_URI, echo=echo) # Create an async engine
    AsyncSessionFactory = sessionmaker(main_engine_async, expire_on_commit=False, class_=AsyncSession) # Session factory bound to the async engine
    async with main_engine_async.begin() as conn: # Asynchronously create all tables if they don't exist. Ensure the models are imported correctly.
        await conn.run_sync(ExchangeBase.metadata.create_all) # MetaData.create_all is a blocking call, so use `run_sync` to run it in a non-blocking way
    return AsyncSessionFactory, main_engine_async

async def initialize_intermediary_database_async(echo=False):
    logger.info("Inside initialize_intermediary_database_async")
    """
    Initializes the intermediary database engine and session factory asynchronously.
    
    Parameters:
        echo (bool): Enables the logging of SQL statements if True. Defaults to False.
    
    Returns:
        A tuple containing the session factory and engine for the intermediary database.
    """
    intermediary_engine_async = create_async_engine(INTERMEDIARY_DATABASE_URI, echo=echo) # Create an async engine
    AsyncSessionFactory = sessionmaker(intermediary_engine_async, expire_on_commit=False, class_=AsyncSession) # Session factory bound to the async engine
    async with intermediary_engine_async.begin() as conn: # Asynchronously create all tables if they don't exist. Ensure the models are imported correctly.
        await conn.run_sync(ExchangeBase.metadata.create_all) # MetaData.create_all is a blocking call, so use `run_sync` to run it in a non-blocking way
    return AsyncSessionFactory, intermediary_engine_async

async def get_or_create_exchange_async(session: AsyncSession, exchange_name: str):
    logger.info(f"Inside get_or_create_exchange_async with exchange_name: {exchange_name}")
    """
    Retrieves an existing exchange from the database or creates a new one if it does not exist.

    Args:
        session: The SQLAlchemy session for database operations.
        exchange_name (str): The name of the exchange to retrieve or create.

    Returns:
        An instance of the Exchange model.
    """    
    if not isinstance(exchange_name, str):
        logger.error(f"get_or_create_exchange_async Invalid exchange_name type: {type(exchange_name)}. Expected string.")
        return None
    exchange_name = exchange_name.lower()
    try: # Attempt to begin a transaction
        async with session.begin(): 
            result = await session.execute(select(Exchange).filter_by(name=exchange_name)) # Try to fetch the existing exchange
            exchange = result.scalars().first()
            if not exchange: # If not found, create a new one
                logger.info(f"get_or_create_exchange_async Exchange not found, creating new: {exchange_name}")
                exchange = Exchange(name=exchange_name)
                session.add(exchange)
                #await session.commit()  # Removed explicit commit, the context manager handles it
                logger.info(f"get_or_create_exchange_async Created new exchange in database: {exchange_name}")
            else:
                logger.info(f"get_or_create_exchange_async Exchange found: {exchange_name}")
            return exchange # Return the exchange (either fetched or newly created)
    except exc.IntegrityError as e:
        logger.error(f"Integrity error occurred while get_or_create_exchange_async '{exchange_name}': {e}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error occurred while get_or_create_exchange_async '{exchange_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unknown error occurred while get_or_create_exchange_async {exchange_name}: {e}")
        raise

async def get_or_create_symbol_async(session: AsyncSession, exchange_name: str, symbol_name: str):
    """
    Retrieves an existing symbol for a given exchange from the database or creates a new one if it does not exist.

    Args:
        session: The SQLAlchemy session for database operations.
        exchange_name (str): The name of the exchange the symbol belongs to.
        symbol_name (str): The name of the symbol to retrieve or create.

    Returns:
        An instance of the Symbol model.
    """
    logger.info(f"Inside get_or_create_symbol_async: {symbol_name} for exchange: {exchange_name}")
    if not isinstance(exchange_name, str):
        logger.error(f"get_or_create_symbol_async Invalid exchange_name type: {type(exchange_name)}. Expected string.")
        return None
    exchange_name = exchange_name.lower()
    try:
        async with session.begin():
            logger.info(f"get_or_create_symbol_async Checking for existing exchange: {exchange_name}")
            result = await session.execute(select(Exchange).filter_by(name=exchange_name))
            exchange = result.scalars().first()

            if not exchange:
                logger.error(f"get_or_create_symbol_async Exchange '{exchange_name}' not found, unable to create symbol: {symbol_name}.")
                return None

            logger.info(f"get_or_create_symbol_async Checking for existing symbol: {symbol_name}")
            result = await session.execute(select(Symbol).filter_by(name=symbol_name, exchange_id=exchange.id))
            symbol = result.scalars().first()

            if not symbol:
                logger.info(f"get_or_create_symbol_async Creating new symbol: {symbol_name} for exchange: {exchange_name}")
                symbol = Symbol(name=symbol_name, exchange_id=exchange.id)
                session.add(symbol)
                # Explicitly logging before commit
                logger.info(f"get_or_create_symbol_async Committing new symbol: {symbol_name} to database.")
                await session.commit()
                logger.info(f"get_or_create_symbol_async Symbol '{symbol_name}' for exchange '{exchange_name}' successfully created.")
            else:
                logger.info(f"get_or_create_symbol_async Symbol '{symbol_name}' for exchange '{exchange_name}' already exists in database.")

            return symbol

    except exc.IntegrityError as e:
        logger.error(f"Integrity error while get_or_create_symbol_async '{symbol_name}' for exchange '{exchange_name}': {e}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error while get_or_create_symbol_async '{symbol_name}' for exchange '{exchange_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while get_or_create_symbol_async '{symbol_name}' for exchange '{exchange_name}': {e}")
        raise

async def initialize_main_greedbase_async(echo=False):
    logger.info("Inside initialize_main_greedbase_async")
    """
    Initializes the main greedbase engine and session factory asynchronously.
    
    Parameters:
        echo (bool): Enables the logging of SQL statements if True. Defaults to False.
    
    Returns:
        A tuple containing the session factory and engine for the main greedbase.
    """
    main_greed_engine_async = create_async_engine(MAIN_GREEDBASE_URI, echo=echo) # Create an async engine
    AsyncGreedSessionFactory = sessionmaker(main_greed_engine_async, expire_on_commit=False, class_=AsyncSession) # Session factory bound to the async engine
    async with main_greed_engine_async.begin() as conn: # Asynchronously create all tables if they don't exist. Ensure the models are imported correctly.
        await conn.run_sync(GreedBase.metadata.create_all) # MetaData.create_all is a blocking call, so use `run_sync` to run it in a non-blocking way
    return AsyncGreedSessionFactory, main_greed_engine_async

async def initialize_intermediary_greedbase_async(echo=False):
    logger.info("Inside initialize_intermediary_greedbase_async")
    """
    Initializes the intermediary greedbase engine and session factory asynchronously.
    
    Parameters:
        echo (bool): Enables the logging of SQL statements if True. Defaults to False.
    
    Returns:
        A tuple containing the session factory and engine for the intermediary greedbase.
    """
    intermediary_greed_engine_async = create_async_engine(INTERMEDIARY_GREEDBASE_URI, echo=echo) # Create an async engine
    AsyncGreedSessionFactory = sessionmaker(intermediary_greed_engine_async, expire_on_commit=False, class_=AsyncSession) # Session factory bound to the async engine
    async with intermediary_greed_engine_async.begin() as conn: # Asynchronously create all tables if they don't exist. Ensure the models are imported correctly.
        await conn.run_sync(GreedBase.metadata.create_all) # MetaData.create_all is a blocking call, so use `run_sync` to run it in a non-blocking way
    return AsyncGreedSessionFactory, intermediary_greed_engine_async

async def get_or_create_greed_source_async(greedsession: AsyncSession, greed_source_name: str):
    """
    Retrieves an existing greed source from the database or creates a new one if it does not exist.
    
    Args:
        session (AsyncSession): The SQLAlchemy asynchronous session for database operations.
        source_name (str): The name of the greed source to retrieve or create.
    
    Returns:
        GreedSource: An instance of the GreedSource model.
    """
    logger.info(f"Attempting to get_or_create_greed_source_async with name:{greed_source_name}")
    try:
        async with greedsession.begin():
            result = await greedsession.execute(select(GreedSource).filter_by(name=greed_source_name))
            greed_source = result.scalars().first()
            if not greed_source:
                logger.info(f"get_or_create_greed_source_async created: {greed_source_name}")
                greed_source = GreedSource(name=greed_source_name)
                greedsession.add(greed_source)
                await greedsession.commit()
                logger.info(f"get_or_create_greed_source_async created: {greed_source_name}")
            return greed_source
    except exc.IntegrityError as e:
        logger.error(f"Integrity error while get_or_create_greed_source_async:{greed_source_name}: {e}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error while get_or_create_greed_source_async:{greed_source_name}: {e}")
        raise
    except Exception as e:
        logger.error(f"get_or_create_greed_source_async error:{e}")
        raise

async def get_or_create_greed_record_async(greedsession: AsyncSession, greed_source_name: str, timestamp: int, greed_value: int, greed_rating: str):
    """
    Retrieves an existing greed record from the database or creates a new one if it does not exist.

    Args:
        greedsession (AsyncSession): The SQLAlchemy asynchronous session for database operations.
        greed_source_name (str): The name of the greed source associated with the record.
        timestamp (int): The epoch timestamp of the greed record.
        greed_value (int): The fear and greed value.
        greed_rating (str): The fear and greed rating.

    Returns:
        GreedRecord: An instance of the GreedRecord model.
    """
    logger.info(f"Attempting to get_or_create_greed_record_async for greed_source_name: {greed_source_name} at timestamp: {timestamp}")
    try:
        async with greedsession.begin():
            # First, get the greed source by name to ensure it exists
            source_result = await greedsession.execute(select(GreedSource).filter_by(name=greed_source_name))
            greed_source = source_result.scalars().first()

            if not greed_source:
                logger.error(f"Greed source '{greed_source_name}' not found. Cannot proceed with creating greed record.")
                return None

            # Now, we can properly query for GreedRecord using the greed_source.id
            result = await greedsession.execute(select(GreedRecord).filter_by(greed_source_id=greed_source.id, timestamp=timestamp))
            greed_record = result.scalars().first()
            if not greed_record:
                logger.info(f"Greed record not found, creating new for source: {greed_source_name} at timestamp: {timestamp}")
                greed_record = GreedRecord(greed_source_id=greed_source.id, timestamp=timestamp, greed_value=greed_value, greed_rating=greed_rating)
                greedsession.add(greed_record)
                await greedsession.commit()
                logger.info(f"Created new greed record for source: {greed_source_name} at timestamp: {timestamp}")
            return greed_record
    except exc.IntegrityError as e:
        logger.error(f"Integrity error while creating greed record '{greed_source_name}': {e}")
        raise
    except exc.SQLAlchemyError as e:
        logger.error(f"Database error while creating greed record '{greed_source_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_or_create_greed_record_async: {e}")
        raise

# async def fetch_db_historical_data_ordered(exchange_name: str, symbol_name: str, existing_session=None):
#     """
#     Fetch historical data for a given cryptocurrency symbol, optionally filtering by exchange.
#     """
#     db_fetch_session = existing_session
#     #close_session = False
#     # Initialize the database session asynchronously
#     if not existing_session:
#         logger.info(f"fetch_db_historical_data_ordered Starting new session: {exchange_name}")
#         AsyncSessionFactory, _ = await initialize_intermediary_database_async()
#         #db_session = session_factory()
#         #close_session = True
#     if not isinstance(exchange_name, str):
#         logger.error(f"Invalid fetch_db_historical_data_ordered type: {type(exchange_name)}. Expected string.")
#         return None
#     async with AsyncSessionFactory() as db_fetch_session:
#         db_query = select(DataRecord)\
#                             .join(Symbol, Symbol.id == DataRecord.symbol_id) \
#                             .join(Exchange, Exchange.id == Symbol.exchange_id) \
#                             .filter(Exchange.name == exchange_name, Symbol.name == symbol_name) \
#                             .order_by(DataRecord.timestamp)
#         db_result = await db_fetch_session.execute(db_query)
#         db_data_ordered = db_result.scalars().all()
#         return db_data_ordered
    
async def fetch_db_historical_data_ordered(symbol_name: str, exchange_name: str = None, existing_session=None):
    """
    Fetch historical data for a given cryptocurrency symbol, optionally filtering by exchange.

    Args:
        symbol_name (str): The name of the cryptocurrency symbol to fetch data for.
        exchange_name (str, optional): The name of the exchange to filter by. If None, fetches data for the symbol across all exchanges.
        existing_session (AsyncSession, optional): An existing SQLAlchemy async session. If None, a new session is created.

    Returns:
        List[DataRecord]: A list of DataRecord instances, ordered by timestamp.
    """
    # Initialize the database session asynchronously if not provided
    if not existing_session:
        logger.info(f"fetch_db_historical_data_ordered Starting new session for symbol: {symbol_name}")
        AsyncSessionFactory, _ = await initialize_intermediary_database_async()
        db_fetch_session = AsyncSessionFactory()
    else:
        db_fetch_session = existing_session

    async with db_fetch_session:
        # Construct the base query
        db_query = select(DataRecord).join(Symbol, Symbol.id == DataRecord.symbol_id)
        # Filter by exchange name if provided
        if exchange_name:
            db_query = db_query.join(Exchange, Exchange.id == Symbol.exchange_id)\
                            .filter(Exchange.name == exchange_name)
                            
        db_query = db_query.filter(Symbol.name == symbol_name).order_by(DataRecord.timestamp)
        
        db_result = await db_fetch_session.execute(db_query)
        db_data_ordered = db_result.scalars().all()
        
        return db_data_ordered

async def fetch_greed_db_historical_data_ordered(greed_source_name, start_date, end_date, existing_greed_session=None):
    """
    Fetch historical Fear and Greed index data, ordered by timestamp, optionally filtering by a given source.

    Args:
        greed_source_name (str, optional): The name of the greed source to filter by. If None, fetches all records.
        existing_greed_session (AsyncSession, optional): An existing SQLAlchemy async session. If None, a new session is created.

    Returns:
        List[GreedRecord]: A list of GreedRecord instances, ordered by timestamp.
    
    Note:
        The function does not close the session. Session management (open/close) is the responsibility
        of the caller to allow for flexible transaction management across multiple operations.
    """
    db_fetch_greed_session = existing_greed_session
    # Initialize the database session asynchronously if not provided
    if not existing_greed_session:
        logger.info(f"fetch_greed_db_historical_data_ordered Starting new session for source: {greed_source_name}")
        AsyncGreedSessionFactory, _ = await initialize_intermediary_greedbase_async()
        db_fetch_greed_session = AsyncGreedSessionFactory()

    async with db_fetch_greed_session:
        # Construct the base query
        db_greed_query = select(GreedRecord)
        # If a specific greed source is specified, add it to the query filter
        if greed_source_name:
            db_greed_query = db_greed_query.join(GreedSource).filter(GreedSource.name == greed_source_name)

            # Filter records between start_date and end_date
            db_greed_query = db_greed_query.filter(
                and_(
                    GreedRecord.timestamp >= start_date,
                    GreedRecord.timestamp <= end_date
                )
            ).order_by(GreedRecord.timestamp)

        db_greed_result = await db_fetch_greed_session.execute(db_greed_query)
        greed_db_data_ordered = db_greed_result.scalars().all()
        return greed_db_data_ordered
    
async def fetch_available_greed_sources(existing_greed_session=None):
    """
    Fetches a list of distinct sources available in the Greed data table.

    This function attempts to retrieve all unique source names recorded in the Greed data.
    It uses an existing database session if provided; otherwise, it initiates a new session
    for this operation. It's the caller's responsibility to manage (open/close) the session.

    Args:
        existing_greed_session (AsyncSession, optional): An existing async SQLAlchemy session for database operations.

    Returns:
        List[str]: A list of unique source names.
        
    Note:
        The function does not close the session. Session management (open/close) is the responsibility
        of the caller to allow for flexible transaction management across multiple operations.
    """
    db_fetch_greed_session = existing_greed_session
    # Initialize the database session asynchronously if not provided
    if not existing_greed_session:
        logger.info(f"fetch_available_greed_sources Starting new session")
        AsyncGreedSessionFactory, _ = await initialize_intermediary_greedbase_async()
        db_fetch_greed_session = AsyncGreedSessionFactory()
    async with db_fetch_greed_session:
        query = select(distinct(GreedSource.name))
        result = await db_fetch_greed_session.execute(query)
        greed_sources = result.scalars().all()
        return greed_sources
