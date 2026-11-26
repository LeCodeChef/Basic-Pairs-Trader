import pandas as pd
import numpy as np
from datetime import time

def portfolio_manager(signals: pd.DataFrame, ln_price: pd.DataFrame, hedge_ratio: float, notional: float, max_hold_bars: int, closing_time: time, entry_cutoff: time):
    
    assert signals.index.equals(ln_price.index)
    assert closing_time > entry_cutoff
    raw_price = np.exp(ln_price)
    side = 0
    hold_bars = 0
    trade_log = []
    pnl = 0
    trades = []
    bars = []
    realized_pnl = 0
    dates = pd.Series(signals.index.date, index=signals.index)
    same_day_as_prev = dates == dates.shift(1)
    is_last_bar = dates != dates.shift(-1)
    goog_share_count = 0
    googl_share_count = 0
    trading = False
    lagged_signals = signals["Event"].shift(1)
    for idx, event, GOOG_Price, GOOGL_Price, idx_prev, idx_last in zip(signals.index, lagged_signals, raw_price["GOOG"], raw_price["GOOGL"], same_day_as_prev, is_last_bar):
        if not trading:
            if event == "Short Entry" and idx.time() < entry_cutoff and idx_prev:
                hold_bars = 0
                goog_share_count = hedge_ratio * notional / GOOG_Price
                googl_share_count = -1 * notional / GOOGL_Price
                entryGOOGPrice = GOOG_Price
                entryGOOGLPrice = GOOGL_Price
                entry_goog_position = goog_share_count * entryGOOGPrice
                entry_googl_position = googl_share_count * entryGOOGLPrice
                entry_time = idx
                side = -1
                trading = True
            elif event == "Long Entry" and idx.time() < entry_cutoff and idx_prev:
                hold_bars = 0
                goog_share_count = -1 * hedge_ratio * notional / GOOG_Price
                googl_share_count = notional / GOOGL_Price
                entryGOOGPrice = GOOG_Price
                entryGOOGLPrice = GOOGL_Price
                entry_goog_position = goog_share_count * entryGOOGPrice
                entry_googl_position = googl_share_count * entryGOOGLPrice
                entry_time = idx
                side = 1
                trading = True

        else:
            hold_bars += 1
            if event == "Exit":
                current_goog_position = goog_share_count * GOOG_Price
                current_googl_position = googl_share_count * GOOGL_Price
                pnl = current_goog_position - entry_goog_position + current_googl_position - entry_googl_position
                realized_pnl += pnl
                exit_time = idx
                trades.append(({"GOOG Shares": goog_share_count, "GOOGL Shares": googl_share_count, 
                              "GOOG Entry Price": entryGOOGPrice, "GOOGL Entry Price": entryGOOGLPrice,
                              "GOOG Exit Price": GOOG_Price, "GOOGL Exit Price": GOOGL_Price,
                              "Reason":"Hit exit", 
                              "Side":side,
                              "Hold Bars":hold_bars,
                              "PnL":pnl,
                              "Entry Time":entry_time,
                              "Exit Time":exit_time}))
                hold_bars = 0
                side = 0
                goog_share_count = googl_share_count = 0
                trading = False
            elif event == "Hit stop":
                current_goog_position = goog_share_count * GOOG_Price
                current_googl_position = googl_share_count * GOOGL_Price
                pnl = current_goog_position - entry_goog_position + current_googl_position - entry_googl_position
                realized_pnl += pnl
                exit_time = idx
                trades.append(({"GOOG Shares": goog_share_count, "GOOGL Shares": googl_share_count, 
                              "GOOG Entry Price": entryGOOGPrice, "GOOGL Entry Price": entryGOOGLPrice,
                              "GOOG Exit Price": GOOG_Price, "GOOGL Exit Price": GOOGL_Price,
                              "Reason":"Hit stop", 
                              "Side":side,
                              "Hold Bars":hold_bars,
                              "PnL":pnl,
                              "Entry Time":entry_time,
                              "Exit Time":exit_time}))
                hold_bars = 0
                side = 0
                goog_share_count = googl_share_count = 0
                trading = False

            elif idx_last or idx.time() >= closing_time:
                current_goog_position = goog_share_count * GOOG_Price
                current_googl_position = googl_share_count * GOOGL_Price
                pnl = current_goog_position - entry_goog_position + current_googl_position - entry_googl_position 
                realized_pnl += pnl
                exit_time = idx           
                trades.append(({"GOOG Shares": goog_share_count, "GOOGL Shares": googl_share_count, 
                              "GOOG Entry Price": entryGOOGPrice, "GOOGL Entry Price": entryGOOGLPrice,
                              "GOOG Exit Price": GOOG_Price, "GOOGL Exit Price": GOOGL_Price,
                              "Reason":"End Of Day Close", 
                              "Side":side,
                              "Hold Bars":hold_bars,
                              "PnL":pnl,
                              "Entry Time":entry_time,
                              "Exit Time":exit_time}))
                hold_bars = 0
                side = 0
                goog_share_count = googl_share_count = 0
                trading = False
            elif hold_bars >= max_hold_bars:
                current_goog_position = goog_share_count * GOOG_Price
                current_googl_position = googl_share_count * GOOGL_Price
                pnl = current_goog_position - entry_goog_position + current_googl_position - entry_googl_position
                realized_pnl += pnl
                exit_time = idx
                trades.append(({"GOOG Shares": goog_share_count, "GOOGL Shares": googl_share_count, 
                              "GOOG Entry Price": entryGOOGPrice, "GOOGL Entry Price": entryGOOGLPrice,
                              "GOOG Exit Price": GOOG_Price, "GOOGL Exit Price": GOOGL_Price,
                              "Reason":"Maximum Bars Threshold Reached", 
                              "Side":side,
                              "Hold Bars":hold_bars,
                              "PnL":pnl,
                              "Entry Time":entry_time,
                              "Exit Time":exit_time}))
                hold_bars = 0
                side = 0
                goog_share_count = googl_share_count = 0
                trading = False
        current_goog_position = goog_share_count * GOOG_Price
        current_googl_position = googl_share_count * GOOGL_Price
        open_pnl = current_goog_position - entry_goog_position + current_googl_position - entry_googl_position if trading else 0
        bars.append({"Side":side, 
                     "GOOG Shares":goog_share_count, 
                     "GOOGL Shares":googl_share_count, 
                     "Equity":realized_pnl + open_pnl})
           
         
    trade_log = pd.DataFrame(trades, columns=["Side", 
                                              "Entry Time", 
                                              "Exit Time", 
                                              "Hold Bars", 
                                              "GOOG Shares", 
                                              "GOOGL Shares", 
                                              "GOOG Entry Price",
                                              "GOOGL Entry Price",
                                              "GOOG Exit Price",
                                              "GOOGL Exit Price",
                                              "PnL",
                                              "Reason"])
    bars = pd.DataFrame(bars, index=signals.index)
    return bars, trade_log
    
           
        


            
        
