# /machine_learning/ml_functions.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas
import logging  # Provides a flexible framework for logging in Python applications.

setup_logging() 
logger = logging.getLogger(__name__)

def aggregate_data(df, time_unit):
    """
    Aggregates data over the specified time unit.
    
    Args:
        df (pd.DataFrame): Dataframe with an 'timestamp' column in epoch time.
        time_unit (str): The time unit for aggregation. Default is 'D' for daily.
                         Other options include 'W' for weekly, 'M' for monthly.
    
    Returns:
        pd.DataFrame: Aggregated DataFrame.
    """
    # Convert 'timestamp' from epoch to datetime
    df['timestamp'] = pandas.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)
    
    # Resample and aggregate
    if time_unit == 'D':
        aggregated_df = df.resample('D').mean()  # Example aggregation by mean
    elif time_unit == 'W':
        aggregated_df = df.resample('W').mean()
    elif time_unit == 'M':
        aggregated_df = df.resample('M').mean()
    
    return aggregated_df

def decompose_time_series(df, column_name, model='additive', period=365):
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
    # Ensure the DataFrame's index is in datetime format for decomposition
    df.index = pandas.to_datetime(df.index, unit='s')

    # Perform the decomposition
    decomposition_result = seasonal_decompose(df[column_name], model=model, period=period, extrapolate_trend='freq')

    return decomposition_result
