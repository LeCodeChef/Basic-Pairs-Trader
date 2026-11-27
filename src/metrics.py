import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def bar_returns(equity: pd.DataFrame, capital: float):
    bar_returns = equity.diff() / capital
    return bar_returns

def sharpe(returns: pd.DataFrame, risk_free_rate: float):
    standard_deviation = np.std(returns)
    sharpe_ratio = (returns.mean() - risk_free_rate) / standard_deviation
    annualized_sharpe_ratio = np.sqrt(252 * 390) * sharpe_ratio
    return annualized_sharpe_ratio

def max_drawdown(net_equity: pd.DataFrame, capital: float):
    max_drawdown = (net_equity["Net Equity"].cummax() - net_equity["Net Equity"]).max() / capital
    return max_drawdown

def plot_equity_curve(bars: pd.DataFrame, title: str):
    plt.plot(bars.index, bars["Equity"], label="Gross Equity Curve")
    plt.plot(bars.index, bars["Net Equity"], label="Net Equity Curve")
    plt.legend()
    plt.show()

def trade_stats(trade_log):
    average_trade_length = trade_log["Hold Bars"].mean()
    median_trade_length = trade_log["Hold Bars"].median()
    number_of_trades = len(trade_log)
    win_rate = (trade_log["Net Pnl"] > 0).sum() / trade_log["Net Pnl"].count()
    average_net_pnl = trade_log["Net Pnl"].mean()
    average_gross_pnl = trade_log["PnL"].mean()
    average_cost = trade_log["Cost"].mean()
    hit_exit_count = (trade_log["Reason"] == "Hit exit").sum()
    hit_stop_count = (trade_log["Reason"] == "Hit stop").sum()
    end_of_day_count = (trade_log['Reason'] == "End Of Day Close").sum()
    max_bars_count = (trade_log["Reason"] == "Maximum Bars Threshold Reached").sum()
    print(f"Average Trade Length: {average_trade_length}\n")
    print(f"Median Trade Length: {median_trade_length}\n")
    print(f"Number of Trades {number_of_trades}\n")
    print(f"Win Rate: {win_rate}\n")
    print(f"Average Gross PnL: {average_gross_pnl}\n")
    print(f"Average Net PnL: {average_net_pnl}\n")
    print(f"Average Cost per Trade: {average_cost}\n")
    print(f"Exit Reasons, Exit: {hit_exit_count}, Stop: {hit_stop_count}, End of Day: {end_of_day_count}, Max Bars Held: {max_bars_count}")

def summary(bars: pd.DataFrame, trade_log: pd.DataFrame, capital: float, risk_free_return: float):
    returns = bar_returns(bars["Net Equity"], capital)
    drawdown = max_drawdown(bars, capital)
    sharpe_ratio = sharpe(returns, risk_free_return)
    print(f"Max Drawdown: {drawdown}")
    print(f"Sharpe Ratio: {sharpe_ratio}")
    trade_stats(trade_log)
    plot_equity_curve(bars, "Equity Curve")
    





