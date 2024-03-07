# /db/models.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.schema import MetaData
import datetime

# Naming convention for Alembic migrations
alembic_naming_convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

alembic_metadata = MetaData(naming_convention=alembic_naming_convention)
ExchangeBase = declarative_base(metadata=alembic_metadata)

class Exchange(ExchangeBase):
    """
    Represents a cryptocurrency exchange in the database.
    
    Attributes:
        id: A unique identifier for the exchange.
        name: The name of the exchange.
        symbols: A list of trading pairs or symbols available on the exchange.
    """
    __tablename__ = 'exchanges'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)  # Adding an index for name as it's likely to be queried often
    symbols = relationship("Symbol", back_populates="exchange")

class Symbol(ExchangeBase):
    """
    Represents a trading pair or symbol in the database.
    
    Attributes:
        id: A unique identifier for the symbol.
        name: The name of the trading pair (e.g., BTC/USDT).
        exchange_id: A foreign key linking to the associated exchange.
    """
    __tablename__ = 'symbols'
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)  # Adding an index for name
    exchange_id = Column(Integer, ForeignKey('exchanges.id'), index=True)  # Adding an index for faster join operations
    exchange = relationship("Exchange", back_populates="symbols")
    data_records = relationship("DataRecord", back_populates="symbol")

class DataRecord(ExchangeBase):
    """
    Stores historical trading data for a symbol.
    
    Attributes:
        id: A unique identifier for the record.
        symbol_id: A foreign key linking to the associated symbol.
        timestamp, open, high, low, close, volume: Trading data metrics.
    """
    __tablename__ = 'data_records'
    id = Column(Integer, primary_key=True)
    symbol_id = Column(Integer, ForeignKey('symbols.id'), index=True)  # Adding an index for faster join operations
    timestamp = Column(Integer, index=True)  # Adding an index for timestamp to improve time-based query performance
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    symbol = relationship("Symbol", back_populates="data_records")

    __table_args__ = (
        Index('ix_data_records_symbol_timestamp', 'symbol_id', 'timestamp'),  # Composite index for querying by symbol and time
    )

class SyncMetadata(ExchangeBase):
    """
    Represents metadata for synchronization operations between intermediary and main databases.
    
    Attributes:
        id (Integer): A unique identifier for the metadata record.
        table_name (String): The name of the table that was synchronized.
        last_synced (DateTime): The timestamp when the last synchronization was completed.
        data_hash (String): A hash of the data at the time of the last synchronization, used to detect changes.
    """
    __tablename__ = 'sync_metadata'
    id = Column(Integer, primary_key=True)
    table_name = Column(String, index=True, nullable=False)  # Adding an index for the table_name
    last_synced = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # Use datetime.datetime.utcnow
    data_hash = Column(String, nullable=False)  # Assuming the hash is a string. Adjust accordingly.

    def __repr__(self):
        return f"<SyncMetadata(table_name='{self.table_name}', last_synced='{self.last_synced}', data_hash='{self.data_hash}')>"
    