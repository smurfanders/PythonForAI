# ml/plotly_functions.py

from data_fetching import exchange_data
from utils.setup_project import setup_logging  # Configures logging via YAML for standardized settings across the application.
from db.database_operations import fetch_db_historical_data_ordered, fetch_greed_db_historical_data_ordered
from data_fetching.fear_greed_data import db_data_to_dataframe, greed_db_data_to_dataframe, aggregate_data, decompose_time_series
import plotly.graph_objects as pl_go
from plotly.subplots import make_subplots
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas
import logging  # Provides a flexible framework for logging in Python applications.

setup_logging() 
logger = logging.getLogger(__name__)

async def plot_crypto_candlestick(exchange_name: str, symbol_name: str):
    """
    Plots a candlestick chart for the specified cryptocurrency symbol and exchange.

    This function fetches historical trading data, converts it into a pandas DataFrame,
    and then uses Plotly to plot a candlestick chart visualizing the price movements.

    Args:
        exchange_name (str): The name of the cryptocurrency exchange.
        symbol_name (str): The symbol for the cryptocurrency.

    Raises:
        Exception: Propagates exceptions from data fetching or plotting operations.
    """
    try:
        # Fetch historical trading data for the specified symbol and exchange.
        crypto_data = await fetch_db_historical_data_ordered(exchange_name, symbol_name)
        if not crypto_data:
            logger.warning(f"No plot_crypto_candlestick data found for {exchange_name}:{symbol_name}.")
            return
        # Convert the fetched data into a pandas DataFrame.
        crypto_df = await db_data_to_dataframe(crypto_data)
        # Use Plotly to create a candlestick chart.{datetime.datetime.fromtimestamp(adjusted_start_date / 1000)}
        fig = pl_go.Figure(data=[pl_go.Candlestick(
                    x=crypto_df['timestamp'], 
                    open=crypto_df['open'],
                    high=crypto_df['high'],
                    low=crypto_df['low'],
                    close=crypto_df['close'])])
        # Update layout of the figure.
        fig.update_layout(title=f'{exchange_name}:{symbol_name} Price Movements', 
                        xaxis_title='Time', yaxis_title='Price')
        fig.update_layout(title=f'{exchange_name}:{symbol_name} Price Movements',
                        xaxis_title='Time', yaxis_title='Price',
                        xaxis=dict(type='category'))  # This line may help improve date label formatting
        # Display the figure.
        fig.show()
    except Exception as e:
        logger.error(f"Failed to plot_crypto_candlestick chart for {exchange_name}:{symbol_name}: {e}", exc_info=True)
        # Optionally, raise the exception to signal failure to callers.
        raise

async def plot_crypto_time_series(exchange_name: str, symbol_name: str):
    """
    Plots a time series of the closing prices for a specified cryptocurrency symbol
    and exchange.

    Args:
        exchange_name (str): The name of the cryptocurrency exchange.
        symbol_name (str): The symbol for the cryptocurrency.
    """
    # Assuming crypto_df is a DataFrame obtained as before,
    # with columns including 'timestamp' and 'close'.
    crypto_data = await fetch_db_historical_data_ordered(exchange_name, symbol_name)
    if not crypto_data:
            logger.warning(f"No plot_crypto_time_series data found for {exchange_name}:{symbol_name}.")
            return
    crypto_df = await db_data_to_dataframe(crypto_data)

    # Create a time series plot.
    fig = pl_go.Figure()

    # Add the time series data.
    fig.add_trace(pl_go.Scatter(x=crypto_df['timestamp'], y=crypto_df['close'], mode='lines', name='Close Price'))

    # Update the layout to add titles and axis labels.
    fig.update_layout(title=f'Time Series of Closing Prices for {exchange_name}:{symbol_name}',
                      xaxis_title='Time',
                      yaxis_title='Closing Price',
                      xaxis=dict(type='date'))  # Ensure x-axis is treated as date

    # Show the figure.
    fig.show()

async def plot_fear_greed_index(greed_sources, start_date, end_date):
    """
    Plots the Fear and Greed Index (FGI) from multiple sources over time.

    This function fetches the FGI data for the specified time range from multiple sources,
    consolidates the data into a pandas DataFrame, and plots it using Plotly to visualize
    the differences and correlations between these indices.

    Args:
    greed_sources (list): A list of greed source names.
    start_date (str): The start date for the data range in 'YYYY-MM-DD' format.
    end_date (str): The end date for the data range in 'YYYY-MM-DD' format.

    Raises:
        Exception: If data fetching fails or if there are issues during plotting.
    """
    # Initialize a figure
    fig = pl_go.Figure()

    for greed_source_name in greed_sources:
        try:
            # Fetch FGI data for the source within the specified date range
            greed_data = await fetch_greed_db_historical_data_ordered(greed_source_name, start_date, end_date)
            if not greed_data:
                logger.warning(f"plot_fear_greed_index No data found: {greed_source_name} within the specified date range.")
                continue
            
            # Convert data into a DataFrame
            greed_df = await greed_db_data_to_dataframe(greed_data)

            # Plot line chart for this FGI source
            fig.add_trace(pl_go.Scatter(x=greed_df['timestamp'], y=greed_df['greed_value'],
                                        mode='lines', name=greed_source_name))
        except Exception as e:
            logger.error(f"plot_fear_greed_index Failed:{greed_source_name}:{e}", exc_info=True)
            # Optionally, raise the exception to signal failure to callers.
            raise

    # Update the layout to add titles and axis labels.
    fig.update_layout(title='Fear and Greed Index Over Time',
                      xaxis_title='Time',
                      yaxis_title='Greed Value',
                      xaxis=dict(type='date'))  # Ensure x-axis is treated as date for better readability

    # Show the figure.
    fig.show()

async def analyze_plot_fgi_market_data(crypto_exchange_name, crypto_symbol_name, greed_sources, start_date, end_date, time_units=['D', 'W', 'M']):
    # Fetch and prepare the cryptocurrency market data
    market_data = await fetch_db_historical_data_ordered(crypto_exchange_name, crypto_symbol_name)
    market_df = await db_data_to_dataframe(market_data)

    # Loop through each time unit for market data analysis
    for unit in time_units:
        period = 365 if unit == 'D' else 52 if unit == 'W' else 12
        aggregated_market_df = aggregate_data(market_df, unit)
        fig_market = pl_go.Figure(data=[pl_go.Scatter(x=aggregated_market_df.index, y=aggregated_market_df['close'], mode='lines', name=crypto_symbol_name)])
        fig_market.update_layout(title=f'{crypto_exchange_name}:{crypto_symbol_name} Closing Prices ({unit})', xaxis_title='Time', yaxis_title='Closing Price', xaxis=dict(type='date'))
        fig_market.show()

    # Loop through each FGI source and time unit for FGI data analysis
    for fgi_source in greed_sources:
        fgi_data = await fetch_greed_db_historical_data_ordered(fgi_source, start_date, end_date)
        fgi_df = await greed_db_data_to_dataframe(fgi_data)
        
        for unit in time_units:
            aggregated_fgi_df = aggregate_data(fgi_df, unit)
            if len(aggregated_fgi_df) < 2:
                print(f"Not enough data for {unit} aggregation for source {fgi_source}.")
                continue
            
            period = {'D': 365, 'W': 52, 'M': 12}.get(unit, 365)
            decomposition_result = seasonal_decompose(aggregated_fgi_df['greed_value'], model='additive', extrapolate_trend='freq', period=period)
            await plot_decomposition(decomposition_result, f'FGI Decomposition ({unit}) for {fgi_source}')

async def plot_decomposition(decomposition, title='Time Series Decomposition'):
    """
    Plots the trend, seasonal, and residual components of a time series decomposition using Plotly.
    
    Args:
        decomposition (DecomposeResult): The result from seasonal_decompose method.
        title (str): The plot title.
    """
    # Extract components
    trend = decomposition.trend.dropna()
    seasonal = decomposition.seasonal.dropna()
    resid = decomposition.resid.dropna()
    
    # Create subplots
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, subplot_titles=('Trend', 'Seasonal', 'Residuals'))
    
    # Trend
    fig.add_trace(pl_go.Scatter(x=trend.index, y=trend, name='Trend'), row=1, col=1)
    
    # Seasonal
    fig.add_trace(pl_go.Scatter(x=seasonal.index, y=seasonal, name='Seasonal'), row=2, col=1)
    
    # Residual
    fig.add_trace(pl_go.Scatter(x=resid.index, y=resid, name='Residuals'), row=3, col=1)
    
    # Update layout
    fig.update_layout(height=600, width=800, title_text=title)
    
    fig.show()

# Assuming already performed decomposition on time series:
# plot_decomposition(btc_decomposition, title='BTC/USDT Decomposition')
# plot_decomposition(fgi_decomposition, title='FGI Decomposition')


# def plot_scatter_matrix(df):
#     """
#     Plots a scatter plot matrix (SPLOM) to visualize potential relationships
#     between multiple variables in the dataset.
    
#     Args:
#         df (pandas.DataFrame): The pandas DataFrame containing the dataset.
#     """
#     fig = pl_px.scatter_matrix(df)
#     fig.update_layout(title='Scatter Plot Matrix')
#     fig.show()

# def plot_trend_lines(df, x_col, y_col, color_col=None):
#     """
#     Plots scatter plots with trend lines for the specified x and y columns,
#     optionally colored by another column.
    
#     Args:
#         df (pandas.DataFrame): The pandas DataFrame containing the dataset.
#         x_col (str): The column name to be plotted on the x-axis.
#         y_col (str): The column name to be plotted on the y-axis.
#         color_col (str, optional): The column name to color data points by. Defaults to None.
#     """
#     fig = pl_px.scatter(df, x=x_col, y=y_col, trendline="ols", color=color_col)
#     fig.update_layout(title=f'Trend Lines: {y_col} vs. {x_col}')
#     fig.show()

# def plot_box(df, y_col, x_col=None):
#     """
#     Creates a box plot to identify potential outliers in the dataset.
    
#     Args:
#         df (pandas.DataFrame): The pandas DataFrame containing the dataset.
#         y_col (str): The column name to be analyzed for outliers.
#         x_col (str, optional): The column name to group data points by. Defaults to None.
#     """
#     fig = pl_px.box(df, y=y_col, x=x_col)
#     fig.update_layout(title=f'Box Plot for {y_col}')
#     fig.show()

