# Su Industries VOC Mk 888 Mod 0
AUTHOR: BEN SU, CHILL MAN IN CHARGE OF SU INDUSTRIES

This is my trading bot, VOC, named after after the Dutch East Indies Trading Corporation.   
The timeframe of the algorithm has been set to 1 minute intervals, i.e. intraday trading. 

## Hypothesis
My hypothesis is that the two classes of a company's stock can be used in a statistical arbitrage algorithm using cointegration. I believe this is so, because shares of different classes in the same company should move in the same general direction over time (fitting cointegration), and maintain a stationary spread. 

I'm targeting shares of companies that have two different publicly listed classes, e.g. $BRK.A and $BRK.B or $GOOG and $GOOGL.

In this case, we used $GOOG and $GOOGL

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
In R&D, I tested each basket of securities using the Engle Granger two-step test, to verify cointegration. I used an Augmented Dickey-Fuller test to verify the stationarity of the spread between the securities, which is valuable because that validated the possibility of mean reversion trading.
I used linear regression to find the appropriate hedge ratio between $GOOG and $GOOGL.

## Model Execution
** Signal Construction (alpha.py and portfolio.py) **
- The model relies on a z-score generator, which measures the # of standard deviations away from the mean spread between $GOOG and $GOOGL. 
- The z-scores were fed into a signal emitter, which emitted a rating of 0, 1, or -1 based on the z-score. 
- 0 = Neutral, 1 = Long, -1 = Short

In our model, our trade entry parameter was set to 2 standard deviations from the mean, our trade exit parameter was set to the mean spread, and our stop parameter was set to 5 standard deviations from the mean. 

We also barred any further trades from entering our books after 10:58 AM, to ensure we weren't trapped in toxic positions near the end of the day, and flattened our books at 3:58 PM, to avoid overnight movement risk.

**

## Backtest Assumptions

- I assumed there to be zero broker commissions, because the broker I used, Alpaca, charges no commission. 
- I assumed a zero percent risk free rate, because the risk free rate per bar is so tiny.
- I assumed that dividends weren't a factor in stock movement, because my strategy is intraday, thus dividends have little effect.
- I assumed a half cent ($0.0005) bid/ask spread for $GOOG and $GOOGl, respectively, due to their high liquidity.

## Results, Sources of Error, Room for Improvement
### In Sample Results:
- Average Trade Length: 74.65316718587746 minutes
- Median Trade Length: 20.0 minutes
- Number of Trades: 963
- Win Rate: 0.5555555555555556
- Average Gross PnL: $2.036343647819917
- Average Net PnL: -$0.0863016303467396
- Average Cost per Trade: $2.1226452781666563
- Exit Reasons; Exit: 885, Stop: 15, End of Day: 63, Max Bars Held: 0
- Max Drawdown: 0.04756465439660248
- Sharpe Ratio: -0.044362546575607474
### Out of Sample Results: 
- Average Trade Length: 135.57566765578636
- Median Trade Length: 78.0
- Number of Trades: 337
- Win Rate: 0.5816023738872403
- Average Gross PnL: $1.2301914406753767
- Average Net PnL: -$0.029203231973190347
- Average Cost per Trade: $1.2593946726485672 
- Exit Reasons; Exit: 283, Stop: 12, End of Day: 42, Max Bars Held: 0
- Max Drawdown: 0.019927546148282085
- Sharpe Ratio: -0.02499682320472754
### Sources of Error:
- I assumed a 0% risk free rate, which likely inflated the algorithm's Sharpe ratio.
- My bid/ask spread estimates for $GOOG and $GOOGL were likely inaccurate, making our PnL calculations rough.
### Room for Improvement:
The main reason this trading pair failed wasn't due to a flaw in signal generation, for we had a close to 58% win rate out of sample.
This trading pair failed because there simply was a very tight spread between $GOOG and $GOOGL, that was unprofitable to exploit once fees were involved. 
Thus, in the future, I will further improve this project by testing more varieties of stock pairs. 


