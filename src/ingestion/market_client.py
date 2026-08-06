"""Market Ingestion Client: Global FX, Commodities, Sovereign Yields, and Defense Equities."""
from __future__ import annotations

from typing import Any
from datetime import date, timedelta
import hashlib
import numpy as np
import pandas as pd


GLOBAL_ASSET_REGISTRY: dict[str, dict[str, Any]] = {
    "brent_oil": {
        "id": "brent_oil",
        "name": "Brent Crude Oil",
        "symbol": "BZ=F",
        "category": "commodities",
        "unit": "$/bbl",
        "base_price": 78.5,
        "volatility": 0.04,
        "geopolitical_sensitivity": "high",
        "description": "Global energy benchmark responsive to Middle East tensions and OPEC+ quotas.",
    },
    "gold": {
        "id": "gold",
        "name": "Spot Gold",
        "symbol": "GC=F",
        "category": "commodities",
        "unit": "$/oz",
        "base_price": 2720.0,
        "volatility": 0.02,
        "geopolitical_sensitivity": "very_high",
        "description": "Safe-haven monetary metal hedging geopolitical escalation and currency debasement.",
    },
    "eur_usd": {
        "id": "eur_usd",
        "name": "EUR / USD Currency Pair",
        "symbol": "EURUSD=X",
        "category": "fx",
        "unit": "USD per EUR",
        "base_price": 1.055,
        "volatility": 0.015,
        "geopolitical_sensitivity": "medium",
        "description": "World's most liquid currency pair, reflective of European political stability and Fed/ECB rate differentials.",
    },
    "us_10y_yield": {
        "id": "us_10y_yield",
        "name": "US 10-Year Treasury Yield",
        "symbol": "^TNX",
        "category": "bonds",
        "unit": "%",
        "base_price": 4.45,
        "volatility": 0.035,
        "geopolitical_sensitivity": "high",
        "description": "Global risk-free rate pricing sovereign credit risk, fiscal deficit concerns, and inflation expectations.",
    },
    "defense_index": {
        "id": "defense_index",
        "name": "Global Aerospace & Defense ETF",
        "symbol": "ITA",
        "category": "equities",
        "unit": "$",
        "base_price": 142.0,
        "volatility": 0.025,
        "geopolitical_sensitivity": "very_high",
        "description": "Basket of defense contractors (Lockheed, RTX, BAE) pricing NATO defense procurement cycles.",
    },
    "sp500": {
        "id": "sp500",
        "name": "S&P 500 Index",
        "symbol": "^GSPC",
        "category": "equities",
        "unit": "pts",
        "base_price": 5950.0,
        "volatility": 0.018,
        "geopolitical_sensitivity": "medium",
        "description": "Global equity risk benchmark sensitive to trade tariffs and regulatory shifts.",
    },
}


def _seed(*parts: str) -> int:
    return int(hashlib.sha256("|".join(parts).encode()).hexdigest()[:8], 16)


def get_market_series(asset_id: str, weeks: int = 52) -> pd.DataFrame:
    """Generate or fetch realistic historical time series for a financial benchmark asset."""
    meta = GLOBAL_ASSET_REGISTRY.get(asset_id.lower())
    if not meta:
        raise ValueError(f"Asset '{asset_id}' not found in asset registry.")

    today = date.today()
    rng = np.random.default_rng(_seed("market", asset_id))

    dates = [(today - timedelta(weeks=i)) for i in range(weeks)][::-1]
    n = len(dates)

    # Generate geometric random walk with regime drift
    drift = rng.uniform(-0.001, 0.002)
    vol = meta["volatility"]
    returns = rng.normal(drift, vol, n)

    # Add macroeconomic shock cycle
    cycle = np.sin(np.linspace(0, 3 * np.pi, n)) * (vol * 1.5)
    total_returns = returns + cycle * 0.2

    prices = [meta["base_price"]]
    for r in total_returns[1:]:
        prices.append(max(0.01, prices[-1] * (1.0 + r)))

    df = pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "asset_id": asset_id,
        "symbol": meta["symbol"],
        "price": [round(float(p), 4 if meta["category"] == "fx" else 2) for p in prices],
        "weekly_return_pct": [round(float(r * 100), 2) for r in total_returns],
    })
    return df
