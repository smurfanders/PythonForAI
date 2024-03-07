# Personal Project: daeCrypto

## Instructions

**All the user interaction is implemented in a few jupyter notebooks in [/notebooks](https://github.com/smurfanders/PythonForAI/tree/main/EgetProjekt/notebooks), check them out.**

## Problem Statement

Despite the wealth of data available in the cryptocurrency market, there remains a significant challenge in accurately predicting market movements due to the volatile and complex nature of the market. Traditional predictive models often overlook the rich insights that can be derived from sentiment data and fail to provide intuitive, interactive visualizations that can aid in understanding market dynamics. **daeCrypto** aims to address these gaps by integrating market data with sentiment analysis and leveraging advanced visualization techniques to offer clearer predictive insights.

## Objectives

1. **Data Integration and Visualization**:

   - To collect historical market data from the Python Binance API and sentiment data from one CSV source (Alternative.me API).
   - To use Plotly for visualization of the data, facilitating a deeper understanding of market trends and sentiment influences on market movements.
2. **Sentiment Data Collection and Analysis**:

   - To utilize BeautifulSoup for web scraping and Tweepy for Twitter data collection, focusing on extracting sentiment data related to the cryptocurrency market.
   - To apply NLTK's Vader tool for sentiment analysis, converting qualitative data into quantifiable sentiment scores, and visualize these findings to uncover potential correlations with market movements.
3. **Data Cleaning and Storage**:

   - To use Pandas and NumPy for the cleaning and preprocessing of collected data, ensuring data quality and readiness for analysis.
   - To store processed data in MariaDB with ColumnStore for efficient data retrieval and in ChromaDB for sentiment data, leveraging the database's capabilities for vectorized sentiment analysis.
4. **Predictive Modeling**:

   - To develop a regression model using SciKit-Learn for predicting cryptocurrency prices based on historical market data and sentiment analysis outcomes.
   - Optionally (if time permits) explore the implementation of a simple reinforcement learning model using PyTorch, focusing on optimizing trading strategies based on the predictive insights.
5. **Interactive Visualization and Presentation**:

   - To create comprehensive, interactive visualizations using Plotly, illustrating the outcomes of data analysis, sentiment analysis, and predictive modeling.
   - To compile the entire analysis and model development process into a Jupyter Notebook or Google Colab if something doesn't work in Jupyter. Using Plotly visualizations for an intuitive understanding of the project findings.
6. **Scalability and Future Work**:

   - To design the project with scalability in mind, allowing for the future integration of additional data sources, more complex modeling techniques, and live data streaming capabilities.
   - To outline a roadmap for future enhancements, including the potential integration of MindsDB for automated machine learning and the use of TensorBoardX with PyTorch for more sophisticated model evaluation and visualization.
