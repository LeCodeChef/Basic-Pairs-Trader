# Su Industries VOC Mk 888 Mod 0
AUTHOR: BEN SU, CHILL MAN IN CHARGE OF SU INDUSTRIES

This is my trading bot, VOC, named after after the Dutch East Indies Trading Corporation.   

## Hypothesis
My hypothesis is that the two classes of a company's stock can be used in a statistical arbitrage algorithm using cointegration. I believe this is so, because shares of different classes in the same company should move in the same general direction over time (fitting cointegration), and maintain a stationary spread. 

I'm targeting shares of companies that have two different publicly listed classes, e.g. $BRK.A and $BRK.B or $GOOG and $GOOGL.

The timeframe of the algorithm has been set to 1 minute intervals, i.e. intraday trading. 

## Data Sources and Pipeline
Our data vendor was the platform Alpaca, I requested the data using their Python SDK. The data was in the OHLCV format.
I sourced our market training data from 11/21/2020 to 11/21/2024, our backtest data is from 11/22/2024 to 11/21/2026.

Since I focused on a limited number of securities (limited to two), there is no risk of survivorship bias, as I'm only trading assets that are still alive and kicking. 

Prior to modeling my data, I went through several preprocessing steps:
1. Convert the data into a pandas dataframe
2. Resetted the index of the dataframe
3. Duplicated the dataframe with only the company ticker, timestamp, and closing price
4. Applied ln() to the closing prices in order to make calculating price changes easier
5. Stored the data in a Parquet format for storage

## Research 
In R&D, I tested each basket of securities using the Engle Granger two-step test, to verify cointegration, and an Augmented Dickey-Fuller test to verify the stationarity of the spread between the securities.
The signal I relied on was a divergence from the mean spread between securities. When a divergence was detected, the model would buy the underperforming stock and sell the outperforming asset. Underperformance is defined as when the price of a securities basket member went down, and overperformance is defined as when a basket member increased in price. 

## Model Execution

## Backtest Assumptions

## Results, Sources of Error, Room for Improvement


