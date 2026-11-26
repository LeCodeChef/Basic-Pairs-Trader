import numpy as np
from alpaca.data import StockHistoricalDataClient
from dotenv import load_dotenv
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import time

def load_data(ticker1: str, ticker2: str, secret_key: str, public_key: str, start_date: time, end_date: time, adjustments: str):
    dataClient = StockHistoricalDataClient(public_key, secret_key)
    request_params = StockBarsRequest(
        symbol_or_symbols=[ticker1, ticker2],
        timeframe = TimeFrame.Minute,
        start = start_date,
        end = end_date,
        adjustment=adjustments
    )
    name_dataset = f"IntradayMarketData{ticker1}_{ticker2}"
    bars = dataClient.get_stock_bars(request_params)
    bars = bars.df.reset_index()
    bars = bars[["symbol", "timestamp", "close"]].copy()
    bars["close"] = np.log(bars["close"])
    bars.to_parquet(name_dataset, engine="pyarrow", index=False)
    return bars
