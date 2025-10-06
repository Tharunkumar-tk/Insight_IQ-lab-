import os
import logging
from typing import Tuple
import pandas as pd
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

logger = logging.getLogger("forecast")

# Prophet wrapper
try:
    from prophet import Prophet  # type: ignore
    _has_prophet = True
except Exception:
    try:
        from fbprophet import Prophet  # type: ignore
        _has_prophet = True
    except Exception:
        _has_prophet = False


def forecast_timeseries(df: pd.DataFrame, days: int = 30) -> Tuple[pd.DataFrame, bool]:
    """
    Takes a DataFrame with columns: date (YYYY-MM-DD) and value
    Returns (forecast_df, used_prophet)
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"]), False

    try:
        m = Prophet() if _has_prophet else None
        if m is None:
            # Fallback: naive moving average projection
            out = df.copy()
            out = out.rename(columns={"date": "ds", "value": "y"})
            out["ds"] = pd.to_datetime(out["ds"])  # ensure datetime
            # Simple projection: last value flatline with slight noise band
            last = float(out["y"].iloc[-1]) if not out.empty else 0.0
            future_dates = pd.date_range(out["ds"].max(), periods=days+1, inclusive="right")
            fdf = pd.DataFrame({"ds": future_dates})
            fdf["yhat"] = last
            fdf["yhat_lower"] = last * 0.98
            fdf["yhat_upper"] = last * 1.02
            return fdf[["ds", "yhat", "yhat_lower", "yhat_upper"]], False
        m.fit(df.rename(columns={"date": "ds", "value": "y"}))
        future = m.make_future_dataframe(periods=days)
        forecast = m.predict(future)
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(days), True
    except Exception as e:
        logger.exception("Forecasting failed: %s", e)
        # Fallback
        out = df.copy()
        out = out.rename(columns={"date": "ds", "value": "y"})
        out["ds"] = pd.to_datetime(out["ds"])  # ensure datetime
        last = float(out["y"].iloc[-1]) if not out.empty else 0.0
        future_dates = pd.date_range(out["ds"].max(), periods=days+1, inclusive="right")
        fdf = pd.DataFrame({"ds": future_dates})
        fdf["yhat"] = last
        fdf["yhat_lower"] = last * 0.98
        fdf["yhat_upper"] = last * 1.02
        return fdf[["ds", "yhat", "yhat_lower", "yhat_upper"]], False


def save_forecast_chart(forecast_df: pd.DataFrame, chart_path: str) -> str:
    """Generate a simple PNG line chart using matplotlib and save to chart_path."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    if forecast_df is None or forecast_df.empty:
        # Create an empty placeholder chart
        plt.figure(figsize=(8, 3))
        plt.title('Forecast')
        plt.savefig(chart_path, bbox_inches='tight')
        plt.close()
        return chart_path

    plt.figure(figsize=(8, 3))
    x = pd.to_datetime(forecast_df["ds"])  # type: ignore
    y = forecast_df["yhat"]
    yl = forecast_df.get("yhat_lower", y)
    yu = forecast_df.get("yhat_upper", y)
    plt.plot(x, y, label='yhat')
    try:
        plt.fill_between(x, yl, yu, color='blue', alpha=0.15, label='uncertainty')
    except Exception:
        pass
    plt.legend(loc='best')
    plt.grid(True, alpha=0.2)
    plt.tight_layout()
    os.makedirs(os.path.dirname(chart_path), exist_ok=True)
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()
    return chart_path
