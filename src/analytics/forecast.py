"""Short-term forecasting of weekly media-tone series.

Primary engine: statsmodels ARIMA. Falls back to a linear-trend projection
(numpy) when statsmodels is unavailable or the series is too short/degenerate,
so the feature never hard-fails.

REMINDER: forecasts project the TREND OF NEWS-COVERAGE TONE, not future public
opinion or real-world events. Short news series are noisy — treat projections
as indicative, and note the confidence band.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

MIN_POINTS_ARIMA = 8   # below this, ARIMA is unreliable -> linear fallback


@dataclass
class ForecastResult:
    history: pd.DataFrame     # week_start, tone
    forecast: pd.DataFrame    # week_start, forecast, lower, upper
    method: str               # 'arima' | 'linear'
    note: str = ""


def _future_weeks(last_week: pd.Timestamp, periods: int) -> list[pd.Timestamp]:
    return [last_week + pd.Timedelta(weeks=i) for i in range(1, periods + 1)]


def _linear_forecast(weeks: pd.Series, values: np.ndarray,
                     periods: int) -> pd.DataFrame:
    x = np.arange(len(values))
    slope, intercept = np.polyfit(x, values, 1)
    resid = values - (slope * x + intercept)
    sigma = float(np.std(resid, ddof=1)) if len(values) > 2 else float(np.std(values))
    fx = np.arange(len(values), len(values) + periods)
    fy = slope * fx + intercept
    fweeks = _future_weeks(weeks.iloc[-1], periods)
    return pd.DataFrame({
        "week_start": fweeks,
        "forecast": fy,
        "lower": fy - 1.96 * sigma,
        "upper": fy + 1.96 * sigma,
    })


def forecast_tone(history: pd.DataFrame, *, periods: int = 4) -> ForecastResult:
    """Forecast the next `periods` weeks of tone.

    history: DataFrame with columns week_start (datetime) and avg_tone.
    """
    hist = history[["week_start", "avg_tone"]].dropna().sort_values("week_start")
    hist = hist.rename(columns={"avg_tone": "tone"}).reset_index(drop=True)
    values = hist["tone"].to_numpy(dtype=float)

    if len(values) < 3:
        empty = pd.DataFrame(columns=["week_start", "forecast", "lower", "upper"])
        return ForecastResult(hist, empty, "none",
                              "Not enough history to forecast (need ≥3 weeks).")

    if len(values) < MIN_POINTS_ARIMA:
        fc = _linear_forecast(hist["week_start"], values, periods)
        return ForecastResult(hist, fc, "linear",
                              "Short series — linear-trend projection.")

    try:
        from statsmodels.tsa.arima.model import ARIMA
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(values, order=(1, 1, 1),
                          enforce_stationarity=False,
                          enforce_invertibility=False)
            fit = model.fit()
            pred = fit.get_forecast(steps=periods)
            mean = np.asarray(pred.predicted_mean, dtype=float)
            ci = np.asarray(pred.conf_int(alpha=0.05), dtype=float)
        fweeks = _future_weeks(hist["week_start"].iloc[-1], periods)
        fc = pd.DataFrame({
            "week_start": fweeks, "forecast": mean,
            "lower": ci[:, 0], "upper": ci[:, 1],
        })
        return ForecastResult(hist, fc, "arima", "ARIMA(1,1,1) projection.")
    except Exception as exc:  # any statsmodels/LinAlg failure -> fallback
        fc = _linear_forecast(hist["week_start"], values, periods)
        return ForecastResult(hist, fc, "linear",
                              f"ARIMA unavailable ({type(exc).__name__}); "
                              "used linear-trend projection.")
