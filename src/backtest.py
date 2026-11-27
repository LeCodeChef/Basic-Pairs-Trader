import pandas as pd
from dataclasses import dataclass
from datetime import time
from src.alpha import rollingZ_score, signal_generator
from src.portfolio import portfolio_manager

def apply_cost(sec_per_share: float, finra_per_share: float, spread_costs_dollar: float, trade_log: pd.DataFrame):
    trade_log = trade_log.copy()
    spread_cost = spread_costs_dollar * (abs(trade_log["GOOG Shares"]) + abs(trade_log["GOOGL Shares"]))
    sec_regulatory_cost = sec_per_share / 10000  * (trade_log["GOOG Exit Price"] * abs(trade_log["GOOG Shares"]) + trade_log["GOOGL Exit Price"] * abs(trade_log["GOOGL Shares"])) 
    finra_regulatory_cost = finra_per_share / 10000 * (abs(trade_log["GOOG Shares"]) + abs(trade_log["GOOGL Shares"]))
    net_pnl = trade_log["PnL"] - spread_cost * 2 - sec_regulatory_cost - finra_regulatory_cost
    per_trade_costs_list = pd.Series(finra_regulatory_cost + spread_cost * 2 + sec_regulatory_cost)
    trade_log["Net Pnl"] = net_pnl
    trade_log["Cost"] = per_trade_costs_list
    return trade_log

@dataclass(frozen=True)
class backtest_config():
    window: int
    hedge_ratio: float
    max_hold_bars: int
    entry: float
    exit_threshold: float
    stop: float
    sec_fee: float
    finra_fee: float
    spread: float
    end_of_day: time
    entry_cutoff: time
    notional: int
    risk_free_rate: float

def net_equity(bars: pd.DataFrame, trade_log: pd.DataFrame):
    bars = bars.copy()
    trade_log_new = trade_log.groupby("Exit Time")["Cost"].sum()
    bars["Cumulative Cost"] = trade_log_new.reindex(bars.index, fill_value=0).cumsum()
    bars["Net Equity"] = bars["Equity"] - bars["Cumulative Cost"]
    return bars

def backtest(data: pd.DataFrame, config):
    z = rollingZ_score(data["GOOG"], data["GOOGL"], config.hedge_ratio, config.window)
    signals = signal_generator(z, config.entry, config.exit_threshold, config.stop)
    bars, trade_log = portfolio_manager(signals, data, config.hedge_ratio, config.notional, config.max_hold_bars, config.end_of_day, config.entry_cutoff)
    trade_log = apply_cost(config.sec_fee, config.finra_fee, config.spread, trade_log)
    bars = net_equity(bars, trade_log)
    return bars, trade_log


