# /db/models_greedData.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey, Index, DateTime
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
GreedBase = declarative_base(metadata=alembic_metadata)

class GreedSource(GreedBase):
    """
    Represents a source of Fear and Greed index data.

    Attributes:
        id (Integer): A unique identifier for the data source.
        name (String): The name of the data source, distinguishing between different providers or methods of data collection.
        greed_records (relationship): A list of GreedRecord instances associated with this data source.
    """
    __tablename__ = 'greed_sources'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)
    greed_records = relationship("GreedRecord", back_populates="greed_source")

class GreedRecord(GreedBase):
    """
    Represents an individual Fear and Greed index data record.

    Attributes:
        id (Integer): A unique identifier for the record.
        data_source_id (Integer): A foreign key linking to the associated GreedSource.
        timestamp (Integer): The epoch time when the data was recorded, facilitating time-based comparisons and analyses.
        fg_value (Integer): The numerical value of the Fear and Greed index at this timestamp.
        fg_rating (String): A qualitative rating or interpretation of the fg_value, such as "Extreme Fear" or "Extreme Greed".
        data_source (relationship): The GreedSource that provided this data record.
    """
    __tablename__ = 'greed_records'
    id = Column(Integer, primary_key=True)
    greed_source_id = Column(Integer, ForeignKey('greed_sources.id'), index=True)  # Corrected the foreign key reference
    timestamp = Column(Integer, index=True)
    greed_value = Column(Integer)
    greed_rating = Column(String)
    greed_source = relationship("GreedSource", back_populates="greed_records")  # Corrected relationship attribute name

class GreedSyncMetadata(GreedBase):
    """
    Represents synchronization metadata for Fear and Greed index data.

    Attributes:
        id (Integer): A unique identifier for the metadata record.
        table_name (String): The name of the table that was synchronized, enabling tracking of multiple synchronization processes.
        last_synced (DateTime): The timestamp when the last synchronization with the data source was completed.
        data_hash (String): A hash of the data at the time of the last synchronization, used to identify changes and trigger updates.
    """
    __tablename__ = 'greed_sync_metadata'
    id = Column(Integer, primary_key=True)
    table_name = Column(String, index=True, nullable=False)  # Adding an index for the table_name
    last_synced = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # Use datetime.datetime.utcnow
    data_hash = Column(String, nullable=False)  # Assuming the hash is a string. Adjust accordingly.

    def __repr__(self):
        return f"<SyncMetadata(table_name='{self.table_name}', last_synced='{self.last_synced}', data_hash='{self.data_hash}')>"

