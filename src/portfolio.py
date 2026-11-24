import pandas as pd
import numpy as np
from datetime import time

def portfolio_manager(signals: pd.DataFrame, ln_price: pd.DataFrame, hedge_ratio: float, notional: float, max_hold_bars: int, closing_time: time, entry_cutoff: time):
    
    raw_price = np.exp(ln_price)
    holdings = {}
    entry = []
    exit = []
    entry_time = []
    exit_time = []
    stop_time = []
    hold_time = []
    hold_bars = 0
    side = []
    trade_log = []
    pnl = []

    assert signals.index.equals(ln_price.index)

    for idx, event, GOOG_Price, GOOGL_Price in zip(signals.index, signals["Event"], raw_price["GOOG"], raw_price["GOOGL"]):
        if event == "Short Entry" and idx.time() < entry_cutoff:
           hold_bars = 0
           holdings[idx] = {"GOOG":(hedge_ratio * notional / GOOG_Price, GOOG_Price), "GOOGL":(-1 * notional / GOOGL_Price, GOOGL_Price)}
           entry.append((GOOG_Price, GOOGL_Price))
           entry_time.append(idx)
           side.append(-1)

        elif event == "Long Entry" and idx.time() < entry_cutoff:
           hold_bars = 0
           holdings[idx] = {"GOOG":(-1 * hedge_ratio * notional / GOOG_Price, GOOG_Price), "GOOGL":(notional / GOOGL_Price, GOOGL_Price)}
           entry.append((GOOG_Price, GOOGL_Price))
           entry_time.append(idx)
           side.append(1)

        elif event == "Exit":
           hold_bars = 0
           exit.append((GOOG_Price, GOOGL_Price))
           exit_time.append(idx)
           pnl.append(exit[-1][0] - entry[-1][0] + exit[-1][1] - entry[-1][1])
        elif event == "Hit stop":
           hold_bars = 0
           exit.append((GOOG_Price, GOOGL_Price))
           exit_time.append(idx)
           pnl.append(exit[-1][0] - entry[-1][0] + exit[-1][1] - entry[-1][1])
 

        elif event == "Holding":
           hold_bars += 1
           hold_time.append(idx.time())


        if idx.time() >= closing_time:
           exit[idx] = (GOOG_Price, GOOGL_Price)
        if hold_bars >= max_hold_bars:
           exit[idx] = (GOOG_Price, GOOGL_Price)
           
         


    trade_log = pd.DataFrame({
       "Side":side, 
       "GOOG Shares":holdings["GOOG"][0],
       "GOOG Price":holdings["GOOG"][1],
       "GOOGL Shares":holdings["GOOGL"][0], 
       "GOOGL Price":holdings["GOOGL"][1],
       "P/L":pnl,
       "Entry Time":entry.keys(), 
       "Hold Time":hold_time,
       "Exit Time":exit.keys(), 
       "Hit Stop Time":stop_time}, 
       index=signals.index)
    return trade_log
    
           
        


            
        
