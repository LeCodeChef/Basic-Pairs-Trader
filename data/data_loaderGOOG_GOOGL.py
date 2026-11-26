import pandas as pd
import numpy as np
from alpaca.data import StockHistoricalDataClient
import os
from dotenv import load_dotenv
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, time

ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
ALPACA_PUBLIC_KEY = os.environ.get("ALPACA_PUBLIC_KEY")
def load_data(ticker1: str, ticker2: str, secret_key: str, public_key: str, start_date: time, end_date: time, adjustments: str):
    load_dotenv("/Users/benjaminsumacbookm4/Desktop/Pairs Trading/.env")
    dataClient = StockHistoricalDataClient(public_key, secret_key)
    request_params = StockBarsRequest(
        symbol_or_symbols=[ticker1, ticker2],
        timeframe = TimeFrame.Minute,
        start = start_date,
        end = end_date,
        adjustment=adjustments
    )
    name_dataset = input("Please input a name for this dataset. ")
    bars = dataClient.get_stock_bars(request_params)
    bars = bars.df.reset_index()
    bars = bars[["symbol", "timestamp", "close"]].copy()
    bars["close"] = np.log(bars["close"])
    bars.to_parquet(name_dataset, engine="pyarrow", index=False)
    return bars

load_data("GOOG", "GOOGL", ALPACA_SECRET_KEY, ALPACA_PUBLIC_KEY, datetime(2020, 11, 21), datetime(2024, 11, 21), "split")