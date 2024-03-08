# /machine_learning/ml_functions.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas
import logging  # Provides a flexible framework for logging in Python applications.

setup_logging() 
logger = logging.getLogger(__name__)

def aggregate_data(agg_df, time_unit):
    """
    Aggregates data over the specified time unit.
    
    Args:
        agg_df (pd.DataFrame): Dataframe with an 'timestamp' column in epoch time.
        time_unit (str): The time unit for aggregation. Default is 'D' for daily.
                         Other options include 'W' for weekly, 'M' for monthly.
    Returns:
        pd.DataFrame: Aggregated DataFrame with datetime_timestamp reset as a column.
    """
    print(f"aggregate_data columns agg_df:\n{agg_df.columns}")  # Check columns
    #print("aggregate_data Before conversion, index type:", type(agg_df.index))

    # Assuming that the epoch time might be in milliseconds, we check the magnitude
    # If the epoch time is too large, it might be in milliseconds.
    # if agg_df['timestamp'].max() > 10**10:
    #     agg_df['timestamp'] /= 1000  # Convert from milliseconds to seconds if necessary

    # Convert 'timestamp' from epoch to datetime
    # agg_df['timestamp'] = pandas.to_datetime(agg_df['timestamp'], unit='s', utc=True)

    # Set 'datetime_timestamp' as the DataFrame index if it's not already
    if not isinstance(agg_df.index, pandas.DatetimeIndex):
        agg_df.set_index('datetime_timestamp', inplace=True)
    print("aggregate_data After setting 'datetime_timestamp' as agg_df index, index type:", type(agg_df.index))
    print(f"aggregate_data After setting 'datetime_timestamp' as agg_df index agg_df:\n{agg_df}") 
    # Resample and aggregate
    if time_unit == 'D':
        aggregated_df = agg_df.resample('D').mean()  # Example aggregation by mean
    elif time_unit == 'W':
        aggregated_df = agg_df.resample('W').mean()
    elif time_unit == 'ME':
        aggregated_df = agg_df.resample('ME').mean()

    # Reset index so 'datetime_timestamp' becomes a column again
    # aggregated_df = aggregated_df.reset_index()
    aggregated_df.reset_index(inplace=True)
    # Set 'datetime_timestamp' as the DataFrame index if it's not already
    # if not isinstance(agg_df.index, pandas.DatetimeIndex):
    #     agg_df.set_index('datetime_timestamp', inplace=True)
    # # Convert the index to the local timezone if necessary
    # aggregated_df['datetime_timestamp'] = aggregated_df['datetime_timestamp'].dt.tz_convert(None)
    print("aggregate_data After reset_index, index type:", type(aggregated_df.index))
    #print(f"aggregate_data aggregated_df output columns:\n{aggregated_df.columns}")  # Check columns
    print(f"aggregate_data aggregated_df:\n{aggregated_df}")
    return aggregated_df

def decompose_time_series(dec_df, column_name, model='additive', period=365):
    """
    Decomposes a time series into its trend, seasonal, and residual components.

    Args:
        df (pd.DataFrame): DataFrame containing the time series data.
        column_name (str): Name of the column to decompose.
        model (str): Type of decomposition model ('additive' or 'multiplicative').
        period (int): The cycle length in the time series data.

    Returns:
        DecomposeResult: Object with the decomposition components.
    """
    print(f"decompose_time_series columns:\n{dec_df.columns}")  # Check columns

    # Ensure the DataFrame's index is in datetime format for decomposition
    dec_df.index = pandas.to_datetime(dec_df.index, unit='s')

    # Perform the decomposition
    decomposition_result = seasonal_decompose(dec_df[column_name], model=model, period=period, extrapolate_trend='freq')
    print(f"decompose_time_series decomposition_result:\n{decomposition_result}")  # Check columns
    return decomposition_result
