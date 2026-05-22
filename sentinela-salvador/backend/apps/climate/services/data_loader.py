import os
import math
import datetime
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinela.settings')

import pandas as pd
from django.conf import settings
from ml.features import load_and_filter_csv, build_features

def _safe_float(val, default=0.0):
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f) or f < -1000) else f
    except (TypeError, ValueError):
        return default

_df_cache = None

def get_dataframe():
    global _df_cache
    if _df_cache is None:
        df = load_and_filter_csv(str(settings.DATA_CSV_PATH))
        _df_cache = build_features(df)
    return _df_cache

def get_current_climate_snapshot(reference_date: str = '2016-01-17'):
    df = get_dataframe()
    mask = df['datetime'].dt.date == pd.to_datetime(reference_date).date()
    day_df = df[mask]
    if day_df.empty:
        day_df = df.tail(24)
    # use peak-precip hour so the snapshot reflects worst moment of the day
    peak_idx = day_df['precip_6h'].idxmax()
    last_row = day_df.loc[peak_idx]
    return {
        'datetime': str(last_row['datetime']),
        'precip_1h': round(_safe_float(last_row['precip_1h']), 2),
        'precip_3h': round(_safe_float(last_row['precip_3h']), 2),
        'precip_6h': round(_safe_float(last_row['precip_6h']), 2),
        'precip_12h': round(_safe_float(last_row['precip_12h']), 2),
        'precip_24h': round(_safe_float(last_row['precip_24h']), 2),
        'pressure': round(_safe_float(last_row.get('pressure', 1013), 1013.0), 2),
        'pressure_trend': round(_safe_float(last_row['pressure_trend']), 2),
        'humidity': round(_safe_float(last_row.get('humidity', 80), 80.0), 2),
        'wind_speed': round(_safe_float(last_row.get('wind_speed', 2), 2.0), 2),
        'month': int(last_row['month']),
        'hour_of_day': int(last_row['hour_of_day']),
        'temperature': round(_safe_float(last_row.get('temperature', 28), 28.0), 2),
    }

def simulate_climate_snapshot(precip_mm: float, hours: int):
    # Builds a synthetic storm snapshot — no CSV loading needed
    rate = precip_mm / max(hours, 1)
    now = datetime.datetime.now()
    return {
        'datetime': str(now),
        'precip_1h':  round(rate, 2),
        'precip_3h':  round(rate * min(hours, 3), 2),
        'precip_6h':  round(rate * min(hours, 6), 2),
        'precip_12h': round(rate * min(hours, 12), 2),
        'precip_24h': round(precip_mm, 2),
        'pressure': 1006.5,
        'pressure_trend': -4.2,
        'humidity': 93.0,
        'wind_speed': 3.8,
        'temperature': 26.5,
        'month': now.month,
        'hour_of_day': now.hour,
    }
