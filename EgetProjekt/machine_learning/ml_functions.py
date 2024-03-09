# /machine_learning/ml_functions.py

from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas
import torch
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
    # print(f"aggregate_data columns agg_df:\n{agg_df.columns}")  # Check columns
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
    # print("aggregate_data After setting 'datetime_timestamp' as agg_df index, index type:", type(agg_df.index))
    # print(f"aggregate_data After setting 'datetime_timestamp' as agg_df index agg_df:\n{agg_df}") 
    # Resample and aggregate
    if time_unit == 'D':
        aggregated_df = agg_df.resample('D').mean()  # Example aggregation by mean
    elif time_unit == 'W':
        aggregated_df = agg_df.resample('W').mean()
    elif time_unit == 'MS':
        aggregated_df = agg_df.resample('MS').mean()
    
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

def normalize_dataframe_column_torch(incoming_df, column_name, norm_method, return_tensor=False):
    """
    Normalizes the specified column in the DataFrame using PyTorch according to the selected normalization method.

    Parameters:
    - incoming_df (pandas.DataFrame): The DataFrame containing the column to be normalized.
    - column_name (str): The name of the column to normalize.
    - norm_method (str): The normalization method to apply. Supported methods are:
        'min-max' - Rescales data to the [0, 1] range.
        'standard' - Standardizes data to have a mean of 0 and a standard deviation of 1.
        'robust' - Uses the interquartile range, making it robust to outliers.
        'l1' - Normalizes data using the L1 norm, making the sum of absolute values 1 in each column.
        'l2' - Normalizes data using the L2 norm, making the sum of squares 1 in each column.
    - return_tensor (bool, optional): If True, returns a PyTorch tensor instead of a DataFrame. Default is False.

    Returns:
    - pandas.DataFrame or torch.Tensor: The DataFrame with the normalized column if return_tensor is False, or the normalization tensor if return_tensor is True.

    Raises:
    - ValueError: If an unknown normalization method is specified.
    """
    try:
        # Copy the input DataFrame to avoid modifying the original data
        working_df = incoming_df.copy()
        # Convert the column data to a PyTorch tensor
        tensor_data = torch.tensor(working_df[column_name].values, dtype=torch.float32).view(-1, 1)
        
        # Apply the selected normalization method
        if norm_method == 'min-max':
            scaler = (tensor_data - torch.min(tensor_data)) / (torch.max(tensor_data) - torch.min(tensor_data))
        elif norm_method == 'standard':
            scaler = (tensor_data - torch.mean(tensor_data)) / torch.std(tensor_data)
        elif norm_method == 'robust':
            qHigh, qLow = torch.quantile(tensor_data, 0.75), torch.quantile(tensor_data, 0.25)
            scaler = (tensor_data - qLow) / (qHigh - qLow)
        elif norm_method == 'l1':
            scaler = tensor_data / torch.norm(tensor_data, p=1, dim=0)
        elif norm_method == 'l2':
            scaler = tensor_data / torch.norm(tensor_data, p=2, dim=0)
        else:
            # Raise an error for an unsupported normalization method
            raise ValueError(f"Unknown normalize_dataframe_column_torch method specified:{norm_method}")
        # Decide whether to return a DataFrame or a PyTorch tensor
        if return_tensor:
            return scaler
        else:
            # Convert the tensor back to numpy and update the DataFrame
            normalized_df = incoming_df.copy()
            normalized_df[column_name] = scaler.numpy().flatten()
            return normalized_df
    except Exception as e:
        logging.error(f"Error normalize_dataframe_column_torch {column_name} with method {norm_method}:{e}")
        raise 
