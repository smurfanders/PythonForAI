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
        pd.DataFrame: Aggregated DataFrame with timestamp reset as a column.
    """
    print(f"aggregate_data columns:\n{agg_df.columns}")  # Check columns

    # Convert 'timestamp' from epoch to datetime and set as index
    agg_df['timestamp'] = pandas.to_datetime(agg_df['timestamp'], unit='s')
    agg_df.set_index('timestamp', inplace=True)
    
    # Resample and aggregate
    if time_unit == 'D':
        aggregated_df = agg_df.resample('D').mean()  # Example aggregation by mean
    elif time_unit == 'W':
        aggregated_df = agg_df.resample('W').mean()
    elif time_unit == 'M':
        aggregated_df = agg_df.resample('M').mean()

    # Reset index to move 'timestamp' back to a column
    aggregated_df.reset_index(inplace=True)
    
    print(f"aggregate_data aggregated_df output columns:\n{aggregated_df.columns}")  # Check columns
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
