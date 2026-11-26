import pandas as pd
def apply_cost(sec_costs_bps: float, finra_costs_bps: float, spread_costs_dollar: float, trade_log: pd.DataFrame):
    spread_cost = spread_costs_dollar * (abs(trade_log["GOOG Shares"]) + abs(trade_log["GOOGL Shares"]))
    finra_regulatory_cost = finra_costs_bps / 10000  * (trade_log["GOOG Exit Price"] * abs(trade_log["GOOG Shares"]) + trade_log["GOOGL Exit Price"] * abs(trade_log["GOOGL Shares"])) 
    sec_regulatory_cost = sec_costs_bps / 10000 * (trade_log["GOOG Shares"] + trade_log["GOOGL Shares"])
    net_pnl = pd.Series(trade_log["PnL"] - spread_cost * 2 - sec_regulatory_cost - finra_regulatory_cost)
    per_trade_costs_list = pd.Series(finra_regulatory_cost + spread_cost * 2 + sec_regulatory_cost)
    trade_log["Net Pnl"] = net_pnl
    trade_log["Cost"] = per_trade_costs_list
    return trade_log