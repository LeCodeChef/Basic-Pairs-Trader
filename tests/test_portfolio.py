"""
Unit tests for src/portfolio.py :: portfolio_manager

These tests encode the agreed design (see backtest plan):
  * Signals are lagged one bar: an event on bar t is FILLED at the close of bar t+1.
    A lagged signal that crosses a day boundary is ignored.
  * The portfolio owns its own flat/long/short state. It opens only on a lagged
    "Short Entry"/"Long Entry" while flat, and ignores "Holding"/"Exit"/"Hit stop" while flat.
  * At most one exit per bar, priority: Hit stop > Hit exit > End Of Day Close > Maximum Bars Threshold Reached.
  * End Of Day Close fires on the last bar of each session OR at/after closing_time.
  * A trade still open at the end of the data is closed with reason "End of data".
  * entry_cutoff is checked against the FILL bar's time (strictly earlier than cutoff).

Return contract:
    bars, trades = portfolio_manager(...)
    bars   : DataFrame indexed by signals.index with columns
             "Side" (0/+1/-1 after this bar's fills), "GOOG Shares", "GOOGL Shares",
             "Equity" (realized + unrealized P/L in $ at this bar's close)
    trades : one row per round trip with columns
             "Side", "Entry Time", "Exit Time", "GOOG Shares", "GOOGL Shares",
             "GOOG Entry Price", "GOOG Exit Price", "GOOGL Entry Price", "GOOGL Exit Price",
             "Reason", "Hold Bars", "PnL"

Rename columns/reasons here if you pick different names; the behaviour is what matters.
Run from the project root:  uv run --with pytest pytest tests -q
"""

import sys
from datetime import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from portfolio import portfolio_manager  # noqa: E402

TZ = "America/New_York"
NOTIONAL = 10_000.0
CLOSE = time(15, 59)
CUTOFF = time(14, 0)


# ---------------------------------------------------------------- helpers
def make_index(start="2024-01-02 10:00", n=8):
    return pd.date_range(start, periods=n, freq="min", tz=TZ)


def make_inputs(events, goog, googl, index=None):
    """Build (signals, ln_price) the same shape signal_generator / the notebook produce."""
    index = make_index(n=len(events)) if index is None else index
    assert len(events) == len(goog) == len(googl) == len(index)
    pos, cur = [], 0
    for e in events:
        if e == "Short Entry":
            cur = -1
        elif e == "Long Entry":
            cur = 1
        elif e in ("Exit", "Hit stop", "N/A"):
            cur = 0
        pos.append(cur)
    signals = pd.DataFrame({"Positions": pos, "Event": events}, index=index)
    ln_price = pd.DataFrame(
        {"GOOG": np.log(np.asarray(goog, float)), "GOOGL": np.log(np.asarray(googl, float))},
        index=index,
    )
    return signals, ln_price


def run(signals, ln_price, hedge_ratio=1.0, max_hold_bars=1_000, closing_time=CLOSE, entry_cutoff=CUTOFF):
    return portfolio_manager(signals, ln_price, hedge_ratio, NOTIONAL, max_hold_bars, closing_time, entry_cutoff)


# Standard round trip. Prices at the SIGNAL bars differ from the FILL bars,
# so a same-bar fill (lookahead) gives a different answer.
#            0      1              2          3          4       5      6      7
EVENTS = ["N/A", "Short Entry", "Holding", "Holding", "Exit", "N/A", "N/A", "N/A"]
GOOG = [99, 99, 100, 101, 102, 103, 103, 103]
GOOGL = [101, 101, 100, 99, 98, 97, 97, 97]
# Short spread = long GOOG $N*beta, short GOOGL $N. Fill entry at bar 2 (100/100), exit at bar 5 (103/97).
# GOOG shares = +100, GOOGL shares = -100  ->  P/L = 100*(103-100) + (-100)*(97-100) = 600


# ---------------------------------------------------------------- core behaviour
def test_round_trip_fills_one_bar_after_signal():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    bars, trades = run(signals, lp)
    idx = signals.index

    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["Side"] == -1
    assert t["Entry Time"] == idx[2]
    assert t["Exit Time"] == idx[5]
    assert t["GOOG Entry Price"] == pytest.approx(100)
    assert t["GOOGL Entry Price"] == pytest.approx(100)
    assert t["GOOG Exit Price"] == pytest.approx(103)
    assert t["GOOGL Exit Price"] == pytest.approx(97)
    assert t["Reason"] == "Hit exit"
    assert t["PnL"] == pytest.approx(600)


def test_short_entry_leg_signs_and_sizes():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    _, trades = run(signals, lp, hedge_ratio=0.5)
    t = trades.iloc[0]
    assert t["GOOG Shares"] == pytest.approx(0.5 * NOTIONAL / 100)  # long GOOG, beta * N
    assert t["GOOGL Shares"] == pytest.approx(-NOTIONAL / 100)  # short GOOGL, N


def test_long_entry_leg_signs_and_sizes():
    events = ["N/A", "Long Entry", "Holding", "Holding", "Exit", "N/A", "N/A", "N/A"]
    signals, lp = make_inputs(events, GOOG, GOOGL)
    _, trades = run(signals, lp, hedge_ratio=0.5)
    t = trades.iloc[0]
    assert t["Side"] == 1
    assert t["GOOG Shares"] == pytest.approx(-0.5 * NOTIONAL / 100)  # short GOOG
    assert t["GOOGL Shares"] == pytest.approx(NOTIONAL / 100)  # long GOOGL
    # GOOG +3 on -50 shares = -150 ; GOOGL -3 on +100 shares = -300
    assert t["PnL"] == pytest.approx(-450)


def test_stop_exit_reason():
    events = ["N/A", "Short Entry", "Holding", "Hit stop", "N/A", "N/A", "N/A", "N/A"]
    signals, lp = make_inputs(events, GOOG, GOOGL)
    _, trades = run(signals, lp)
    assert len(trades) == 1
    assert trades.iloc[0]["Reason"] == "Hit stop"
    assert trades.iloc[0]["Exit Time"] == signals.index[4]


# ---------------------------------------------------------------- bars output
def test_bars_output_shape_position_and_equity():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    bars, trades = run(signals, lp)

    assert bars.index.equals(signals.index)
    assert list(bars["Side"]) == [0, 0, -1, -1, -1, 0, 0, 0]
    # mark-to-market at bar 3: 100*(101-100) + (-100)*(99-100) = 200
    assert bars["Equity"].iloc[3] == pytest.approx(200)
    assert bars["Equity"].iloc[1] == pytest.approx(0)
    assert bars["Equity"].iloc[-1] == pytest.approx(trades["PnL"].sum())
    assert bars["GOOG Shares"].iloc[0] == 0 and bars["GOOG Shares"].iloc[3] == pytest.approx(100)


def test_no_signals_returns_empty_trades_without_crashing():
    signals, lp = make_inputs(["N/A"] * 8, GOOG, GOOGL)
    bars, trades = run(signals, lp)
    assert len(trades) == 0
    assert (bars["Side"] == 0).all()
    assert (bars["Equity"] == 0).all()


def test_pnl_column_is_numeric():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    _, trades = run(signals, lp)
    assert pd.api.types.is_numeric_dtype(trades["PnL"])


# ---------------------------------------------------------------- overlays / state desync
def test_entry_after_cutoff_is_ignored_and_no_phantom_position():
    # cutoff 14:00, signal at 14:05 -> fill would be 14:06 -> rejected.
    # The following "Holding" events must NOT open a position.
    idx = make_index("2024-01-02 14:04", n=8)
    events = ["N/A", "Short Entry", "Holding", "Holding", "Holding", "Exit", "N/A", "N/A"]
    signals, lp = make_inputs(events, GOOG, GOOGL, index=idx)
    bars, trades = run(signals, lp)
    assert len(trades) == 0
    assert (bars["Side"] == 0).all()


def test_eod_exit_then_no_reentry_next_day():
    day1 = pd.date_range("2024-01-02 15:54", periods=6, freq="min", tz=TZ)  # 15:54..15:59
    day2 = pd.date_range("2024-01-03 09:30", periods=4, freq="min", tz=TZ)
    idx = day1.append(day2)
    events = ["N/A", "Short Entry", "Holding", "Holding", "Holding", "Holding",  # day 1
              "Holding", "Holding", "Exit", "N/A"]  # day 2: generator still thinks it's short
    goog = [100] * 10
    googl = [100] * 10
    signals, lp = make_inputs(events, goog, googl, index=idx)
    bars, trades = run(signals, lp, entry_cutoff=time(15, 57))

    assert len(trades) == 1
    assert trades.iloc[0]["Reason"] == "End Of Day Close"
    assert trades.iloc[0]["Exit Time"] == idx[5]  # 15:59 day 1
    assert (bars.loc[day2, "Side"] == 0).all()


def test_eod_on_half_day_without_closing_bar():
    # Half day: last bar 12:59, never reaches closing_time 15:59. Must still flatten.
    day1 = pd.date_range("2024-11-29 12:54", periods=6, freq="min", tz=TZ)
    day2 = pd.date_range("2024-12-02 09:30", periods=3, freq="min", tz=TZ)
    idx = day1.append(day2)
    events = ["N/A", "Long Entry", "Holding", "Holding", "Holding", "Holding", "Holding", "Holding", "Exit"]
    signals, lp = make_inputs(events, [100] * 9, [100] * 9, index=idx)
    bars, trades = run(signals, lp)

    assert len(trades) == 1
    assert trades.iloc[0]["Exit Time"] == idx[5]  # 12:59
    assert trades.iloc[0]["Reason"] == "End Of Day Close"
    assert (bars.loc[day2, "Side"] == 0).all()


def test_signal_from_previous_day_is_not_filled_overnight():
    day1 = pd.date_range("2024-01-02 13:57", periods=3, freq="min", tz=TZ)  # last bar 13:59 (< cutoff 14:00)
    day2 = pd.date_range("2024-01-03 09:30", periods=4, freq="min", tz=TZ)
    idx = day1.append(day2)
    events = ["N/A", "N/A", "Short Entry", "Holding", "Holding", "Exit", "N/A"]
    signals, lp = make_inputs(events, [100] * 7, [100] * 7, index=idx)
    _, trades = run(signals, lp)
    assert len(trades) == 0


def test_time_stop_fires_at_exactly_max_hold_bars():
    events = ["N/A", "Short Entry"] + ["Holding"] * 6
    signals, lp = make_inputs(events, GOOG, GOOGL)
    _, trades = run(signals, lp, max_hold_bars=3)
    assert len(trades) == 1
    t = trades.iloc[0]
    assert t["Reason"] == "Maximum Bars Threshold Reached"
    assert t["Entry Time"] == signals.index[2]
    assert t["Exit Time"] == signals.index[5]
    assert t["Hold Bars"] == 3


def test_signal_exit_on_closing_bar_records_one_exit():
    idx = make_index("2024-01-02 15:52", n=8)  # 15:52..15:59
    events = ["N/A", "Short Entry", "Holding", "Holding", "Holding", "Holding", "Exit", "N/A"]
    signals, lp = make_inputs(events, [100] * 8, [100] * 8, index=idx)
    _, trades = run(signals, lp, entry_cutoff=time(15, 55))
    assert len(trades) == 1
    assert trades.iloc[0]["Reason"] == "Hit exit"  # signal exit outranks End of Day
    assert trades.iloc[0]["Exit Time"] == idx[7]


def test_open_trade_closed_at_end_of_data():
    events = ["N/A", "Short Entry", "Holding", "Holding"]
    idx = make_index("2024-01-02 10:00", n=4)
    signals, lp = make_inputs(events, [100] * 4, [100] * 4, index=idx)
    _, trades = run(signals, lp)
    assert len(trades) == 1
    # 10:03 is the session's last bar here, so End of Day and End of data coincide; either is acceptable
    assert trades.iloc[0]["Reason"] in ("End of data", "End Of Day Close")
    assert trades.iloc[0]["Exit Time"] == idx[-1]


def test_two_consecutive_trades():
    events = ["N/A", "Short Entry", "Holding", "Exit", "N/A", "Long Entry", "Holding", "Exit", "N/A", "N/A"]
    signals, lp = make_inputs(events, [100] * 10, [100] * 10, index=make_index(n=10))
    _, trades = run(signals, lp)
    assert list(trades["Side"]) == [-1, 1]
    assert list(trades["Reason"]) == ["Hit exit", "Hit exit"]


# ---------------------------------------------------------------- lookahead / hygiene
def test_no_lookahead_changing_future_prices_does_not_change_past():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    bars_a, _ = run(signals, lp)

    k = 3
    lp_b = lp.copy()
    lp_b.iloc[k + 1:] += 0.05  # shock every price after bar k
    bars_b, _ = run(signals, lp_b)

    pd.testing.assert_frame_equal(bars_a.iloc[: k + 1], bars_b.iloc[: k + 1])


def test_does_not_mutate_inputs():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    s_copy, lp_copy = signals.copy(), lp.copy()
    run(signals, lp)
    pd.testing.assert_frame_equal(signals, s_copy)
    pd.testing.assert_frame_equal(lp, lp_copy)


def test_mismatched_index_raises():
    signals, lp = make_inputs(EVENTS, GOOG, GOOGL)
    with pytest.raises(AssertionError):
        run(signals, lp.iloc[1:])
