"""Regression tests for the intraday-session guard (strictly end-of-day feed).

A manual mid-day pipeline run must NOT publish an unclosed (intraday) bar; it
scores the last COMPLETED session instead. The scheduled run fires after the
4 PM ET close, so a real end-of-day bar is always kept.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from compute import loader

ET = ZoneInfo("America/New_York")


def _frame(dates):
    rows = []
    for t in ("AAPL", "NTDOY"):
        for d in dates:
            rows.append({"ticker": t, "date": pd.Timestamp(d), "close": 1.0})
    return pd.DataFrame(rows)


def _maxdate(df):
    return str(pd.to_datetime(df["date"]).max())[:10]


def test_midday_run_drops_unclosed_bar():
    df = _frame(["2026-06-22", "2026-06-23", "2026-06-24"])
    out = loader._drop_unclosed_session(df, now=datetime(2026, 6, 24, 11, 0, tzinfo=ET))
    assert _maxdate(out) == "2026-06-23"        # intraday 06-24 dropped
    assert len(out) == 4


def test_postclose_run_keeps_todays_bar():
    df = _frame(["2026-06-22", "2026-06-23", "2026-06-24"])
    out = loader._drop_unclosed_session(df, now=datetime(2026, 6, 24, 17, 0, tzinfo=ET))
    assert _maxdate(out) == "2026-06-24"        # session closed -> kept
    assert len(out) == 6


def test_exactly_at_close_keeps_bar():
    df = _frame(["2026-06-23", "2026-06-24"])
    out = loader._drop_unclosed_session(df, now=datetime(2026, 6, 24, 16, 0, tzinfo=ET))
    assert _maxdate(out) == "2026-06-24"        # 16:00 ET == closed


def test_prior_session_cache_untouched():
    df = _frame(["2026-06-22", "2026-06-23"])
    out = loader._drop_unclosed_session(df, now=datetime(2026, 6, 24, 11, 0, tzinfo=ET))
    assert _maxdate(out) == "2026-06-23"        # newest already a prior session
    assert len(out) == 4


def test_empty_frame_is_safe():
    out = loader._drop_unclosed_session(pd.DataFrame(), now=datetime(2026, 6, 24, 11, 0, tzinfo=ET))
    assert out.empty
