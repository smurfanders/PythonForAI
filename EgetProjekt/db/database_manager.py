# /db/database_manager.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from utils.config_loader import load_config
from db.database_operations import initialize_main_database_async, initialize_intermediary_database_async
from sqlalchemy import MetaData, exc
from alembic import command
from alembic.config import Config
from alembic.util.exc import CommandError
import argparse
import logging  # Provides a flexible framework for logging in Python applications.

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
exchange_config = load_config()

def generate_migrations(database_url, message="Auto-generate migrations"):
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.revision(alembic_cfg, autogenerate=True, message=message)
        logger.info(f"Migrations generated successfully for {database_url}.")
    except CommandError as e:
        logger.error(f"Alembic command error during migration generation for {database_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during migration generation for {database_url}: {e}")


def apply_migrations(database_url):
    try:
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        command.upgrade(alembic_cfg, "head")
        logger.info(f"Migrations applied successfully to {database_url}.")
    except CommandError as e:
        logger.error(f"Alembic command error during migration application to {database_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during migration application to {database_url}: {e}")


async def sync_databases_async(main_engine_async, intermediary_engine_async):
    """
    Asynchronously synchronizes data from the intermediary database to the main database.
    Reflects tables from both databases, clears the main database tables,
    and copies all records from the intermediary database.
    
    Args:
        main_engine_async (AsyncEngine): The SQLAlchemy async engine instance for the main database.
        intermediary_engine_async (AsyncEngine): The SQLAlchemy async engine instance for the intermediary database.
    """
    intermediary_metadata = MetaData()
    main_metadata = MetaData()
    """
    Use async engine to reflect tables
    """
    async with intermediary_engine_async.connect() as intermediary_conn:
        await intermediary_metadata.reflect(bind=intermediary_conn)
    async with main_engine_async.connect() as main_conn:
        await main_metadata.reflect(bind=main_conn)

        async with main_conn.begin() as transaction: # Begin a transaction on the main database
            try:
                for table_name in intermediary_metadata.tables: # For each table, clear records in the main database and copy from intermediary
                    intermediary_table = intermediary_metadata.tables[table_name]
                    main_table = main_metadata.tables[table_name]
                    await main_conn.execute(main_table.delete()) # Clear existing records in the main database table
                    select_stmt = intermediary_table.select() # Select and insert records from intermediary to main database
                    records = await intermediary_conn.execute(select_stmt)
                    await main_conn.execute(main_table.insert(), await records.fetchall())
                await transaction.commit() # Commit transaction if all operations succeed
                logger.info("Database synchronization completed successfully.")
            except exc.IntegrityError as e:
                await transaction.rollback()
                logger.error(f"Integrity error during database synchronization: {e}. Rolled back the transaction.")
                raise
            except exc.SQLAlchemyError as e:
                await transaction.rollback()
                logger.error(f"SQLAlchemy error during database synchronization: {e}. Rolled back the transaction.")
                raise
            except Exception as e:
                await transaction.rollback()  # Rollback transaction on error
                logger.error(f"Error during database synchronization: {e}")
                raise

async def syncDb_command():
    try:
        parser = argparse.ArgumentParser(description="Database management and synchronization tool.")
        parser.add_argument('--migrate', action='store_true', help='Run database migrations.')
        parser.add_argument('--sync', action='store_true', help='Synchronize databases asynchronously.')
        args = parser.parse_args()

        if not args.migrate and not args.sync:
            logger.error("No operation specified. Use '--migrate' to run migrations or '--sync' to synchronize databases.")
            parser.print_help()
            return
        if args.migrate:
            # Generate and apply migrations for the main database
            generate_migrations("sqlite:///db/main_exchangeData.sqlite", "Generate main db migrations")
            apply_migrations("sqlite:///db/main_exchangeData.sqlite")
            
            # Generate and apply migrations for the intermediary database
            generate_migrations("sqlite:///db/intermediary_exchangeData.sqlite", "Generate intermediary db migrations")
            apply_migrations("sqlite:///db/intermediary_exchangeData.sqlite")
        if args.sync:
            # Synchronize databases if needed
            main_session_factory, _ = await initialize_main_database_async()
            intermediary_session_factory, _ = await initialize_intermediary_database_async()
            
            # Use the session factories to create sessions if necessary for syncing
            await sync_databases_async(main_session_factory(), intermediary_session_factory())
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
