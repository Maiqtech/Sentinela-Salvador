import pandas as pd
import numpy as np

def load_and_filter_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=',', encoding='latin-1')
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'DATA (YYYY-MM-DD)': 'date',
        'HORA (UTC)': 'hour',
        'PRECIPITACAO TOTAL HORARIO (mm)': 'precip',
        'PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)': 'pressure',
        'UMIDADE RELATIVA DO AR, HORARIA (%)': 'humidity',
        'VENTO, VELOCIDADE HORARIA (m/s)': 'wind_speed',
        'TEMPERATURA DO AR - BULBO SECO, HORARIA (C)': 'temperature',
    })
    df['datetime'] = pd.to_datetime(
        df['date'].astype(str) + ' ' + df['hour'].astype(str).str.zfill(4),
        format='%Y-%m-%d %H%M', errors='coerce'
    )
    df = df.dropna(subset=['datetime'])
    df = df[df['datetime'].dt.year >= 2015].copy()
    df = df.sort_values('datetime').reset_index(drop=True)
    for col in ['precip', 'pressure', 'humidity', 'wind_speed']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['precip_1h'] = df['precip']
    df['precip_3h'] = df['precip'].rolling(3, min_periods=1).sum()
    df['precip_6h'] = df['precip'].rolling(6, min_periods=1).sum()
    df['precip_12h'] = df['precip'].rolling(12, min_periods=1).sum()
    df['precip_24h'] = df['precip'].rolling(24, min_periods=1).sum()
    df['pressure_trend'] = df['pressure'].diff(3).fillna(0)
    df['month'] = df['datetime'].dt.month
    df['hour_of_day'] = df['datetime'].dt.hour
    return df

def label_risk(precip_6h: float) -> int:
    if precip_6h >= 50:
        return 3  # critical
    elif precip_6h >= 30:
        return 2  # high
    elif precip_6h >= 10:
        return 1  # medium
    return 0  # low

def get_feature_columns():
    return ['precip_1h', 'precip_3h', 'precip_6h', 'precip_12h', 'precip_24h',
            'pressure_trend', 'humidity', 'wind_speed', 'month', 'hour_of_day']

def build_current_features(precip_1h, precip_3h, precip_6h, precip_12h, precip_24h,
                            pressure_trend, humidity, wind_speed, month, hour_of_day) -> dict:
    return {
        'precip_1h': precip_1h,
        'precip_3h': precip_3h,
        'precip_6h': precip_6h,
        'precip_12h': precip_12h,
        'precip_24h': precip_24h,
        'pressure_trend': pressure_trend,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'month': month,
        'hour_of_day': hour_of_day,
    }
