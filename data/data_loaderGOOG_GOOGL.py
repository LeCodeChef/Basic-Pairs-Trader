import pandas as pd
import numpy as np
from alpaca.data import StockHistoricalDataClient
import os
from dotenv import load_dotenv
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime

load_dotenv("/Users/benjaminsumacbookm4/Desktop/Pairs Trading/.env")

ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
ALPACA_PUBLIC_KEY = os.environ.get("ALPACA_PUBLIC_KEY")

dataClient = StockHistoricalDataClient(ALPACA_PUBLIC_KEY, ALPACA_SECRET_KEY)
request_params = StockBarsRequest(
    symbol_or_symbols=["GOOG", "GOOGL"],
    timeframe = TimeFrame.Minute,
    start = datetime(2020, 11, 21),
    end = datetime(2024, 11, 21)
)

bars = dataClient.get_stock_bars(request_params)
bars = bars.df.reset_index()
bars = bars[["symbol", "timestamp", "close"]].copy()
bars["close"] = np.log(bars["close"])
bars.to_parquet("IntradayMarketDataGOOG_GOOGL", engine="pyarrow", index=False)
