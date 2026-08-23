"""Short-term forecasting of weekly media-tone series.

Primary engine: statsmodels ARIMA. Secondary engine: Exponential Smoothing (ETS).
Falls back to a linear-trend projection (numpy) when statsmodels is unavailable or
the series is too short/degenerate, so the feature never hard-fails.

REMINDER: forecasts project the TREND OF NEWS-COVERAGE TONE, not future public
opinion or real-world events. Short news series are noisy — treat projections
as indicative, and note the confidence band.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MIN_POINTS_ARIMA = 8   # below this, ARIMA is unreliable -> linear fallback
MIN_POINTS_ETS = 10    # ETS requires slightly more history for meaningful smoothing


@dataclass
class ForecastResult:
    history: pd.DataFrame     # week_start, tone
    forecast: pd.DataFrame    # week_start, forecast, lower, upper
    method: str               # 'arima' | 'ets' | 'linear' | 'none'
    note: str = ""
    ets_forecast: pd.DataFrame = field(default_factory=pd.DataFrame)  # second estimator when available
    preferred_method: str = ""  # which of arima/ets is preferred (empty if only one)


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


def _ets_forecast(weeks: pd.Series, values: np.ndarray, periods: int) -> pd.DataFrame | None:
    """Holt-Winters Exponential Smoothing forecast. Returns None on failure."""
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ExponentialSmoothing(
                values,
                trend="add",
                damped_trend=True,
                initialization_method="estimated",
            )
            fit = model.fit(optimized=True)
            mean = fit.forecast(periods)
            # Use in-sample residual std for confidence bands
            resid_std = float(np.std(fit.resid)) if len(fit.resid) > 2 else 1.0
            fweeks = _future_weeks(weeks.iloc[-1], periods)
            return pd.DataFrame({
                "week_start": fweeks,
                "forecast": mean,
                "lower": mean - 1.96 * resid_std,
                "upper": mean + 1.96 * resid_std,
            })
    except Exception:
        return None


def forecast_tone(history: pd.DataFrame, *, periods: int = 4) -> ForecastResult:
    """Forecast the next `periods` weeks of tone.

    history: DataFrame with columns week_start (datetime) and avg_tone.

    Returns a ForecastResult with:
    - `forecast`: primary ARIMA or linear forecast
    - `ets_forecast`: ETS alternative (empty DataFrame when unavailable)
    - `preferred_method`: 'arima' | 'ets' (which model has lower AIC when both run)
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

    # Attempt ARIMA
    arima_fc: pd.DataFrame | None = None
    arima_aic: float = float("inf")
    try:
        from statsmodels.tsa.arima.model import ARIMA
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = ARIMA(values, order=(1, 1, 1),
                          enforce_stationarity=False,
                          enforce_invertibility=False)
            fit = model.fit()
            arima_aic = fit.aic
            pred = fit.get_forecast(steps=periods)
            mean = np.asarray(pred.predicted_mean, dtype=float)
            ci = np.asarray(pred.conf_int(alpha=0.05), dtype=float)
        fweeks = _future_weeks(hist["week_start"].iloc[-1], periods)
        arima_fc = pd.DataFrame({
            "week_start": fweeks, "forecast": mean,
            "lower": ci[:, 0], "upper": ci[:, 1],
        })
    except Exception as exc:
        arima_note = f"ARIMA unavailable ({type(exc).__name__})"
    else:
        arima_note = "ARIMA(1,1,1) projection."

    # Attempt ETS (requires more data)
    ets_fc: pd.DataFrame | None = None
    ets_aic: float = float("inf")
    if len(values) >= MIN_POINTS_ETS:
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _fit = ExponentialSmoothing(
                    values, trend="add", damped_trend=True,
                    initialization_method="estimated"
                ).fit(optimized=True)
                ets_aic = _fit.aic
        except Exception:
            pass
        ets_fc = _ets_forecast(hist["week_start"], values, periods)

    # Determine preferred method by AIC
    if arima_fc is not None and ets_fc is not None:
        preferred = "arima" if arima_aic <= ets_aic else "ets"
        primary_fc = arima_fc if preferred == "arima" else ets_fc
        note = f"ARIMA(1,1,1) + ETS(Holt-Winters) dual forecast. Preferred: {preferred} (lower AIC)."
        return ForecastResult(
            hist, primary_fc, preferred, note,
            ets_forecast=ets_fc if preferred == "arima" else arima_fc,
            preferred_method=preferred,
        )
    elif arima_fc is not None:
        return ForecastResult(hist, arima_fc, "arima", arima_note,
                              ets_forecast=pd.DataFrame(), preferred_method="arima")
    elif ets_fc is not None:
        return ForecastResult(hist, ets_fc, "ets", "ETS (Holt-Winters) projection.",
                              ets_forecast=pd.DataFrame(), preferred_method="ets")
    else:
        fc = _linear_forecast(hist["week_start"], values, periods)
        return ForecastResult(hist, fc, "linear",
                              "ARIMA and ETS both unavailable; used linear-trend projection.")
