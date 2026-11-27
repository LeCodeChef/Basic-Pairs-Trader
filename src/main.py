import pandas as pd
from src.metrics import summary
from datetime import time
from src.backtest import backtest, backtest_config

out_sample_data = pd.read_parquet("data/market_data/IntradayMarketDataOOS_GOOG_GOOGL")
in_sample_data = pd.read_parquet("data/market_data/IntradayMarketDataGOOG_GOOGL_V2")

out_sample_data["timestamp"] = out_sample_data["timestamp"].dt.tz_convert("America/New_York")

prices_out_sample = (
    out_sample_data.pivot(index="timestamp", columns="symbol", values="close")
        .between_time("09:30", "15:59") # Normalizes time to regular business hours
        .dropna()
)

in_sample_data["timestamp"] = in_sample_data["timestamp"].dt.tz_convert("America/New_York")

prices_in_sample = (
    in_sample_data.pivot(index="timestamp", columns="symbol", values="close")
        .between_time("09:30", "15:59")
        .dropna()
)

window = 500
hedge_ratio = 0.9940650232687545
max_hold_bars = 390
entry = 2 
exit_threshold = 0
stop = 5
sec_bps = 0.206
finra_bps = 1.95
spread = 0.005
end_of_day = time(15, 58)
entry_cutoff = time(10, 58)
notional = 10000
risk_free_rate = 0
config = backtest_config(window=window, hedge_ratio=hedge_ratio, max_hold_bars=max_hold_bars, entry=entry, exit_threshold=exit_threshold, stop=stop, sec_fee=sec_bps, finra_fee=finra_bps, spread=spread, end_of_day=end_of_day, entry_cutoff=entry_cutoff, notional=notional, risk_free_rate=risk_free_rate)

def main():
    oos_or_in_sample = input("Out of sample? (Enter only True/False) ")
    if oos_or_in_sample == "True":
        bars, trade_log = backtest(prices_out_sample, config)
        print("OUT OF SAMPLE")
    else:
        bars, trade_log = backtest(prices_in_sample, config)
        print("IN SAMPLE")
    summary(bars, trade_log, config.notional, config.risk_free_rate)


if __name__ == "__main__":
    main()
