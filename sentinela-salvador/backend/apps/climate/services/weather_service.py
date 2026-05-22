import math
import datetime
import json
import urllib.request
import urllib.parse
from django.conf import settings

SALVADOR_LAT = -12.97
SALVADOR_LON = -38.49
OWM_BASE = 'https://api.openweathermap.org/data/2.5'

HORIZONS = [
    {'key': 'now',  'label': 'Agora',  'hours': 0},
    {'key': '+6h',  'label': '+6h',    'hours': 6},
    {'key': '+12h', 'label': '+12h',   'hours': 12},
    {'key': '+24h', 'label': '+24h',   'hours': 24},
    {'key': '+48h', 'label': '+48h',   'hours': 48},
]


def _s(val, default=0.0):
    try:
        f = float(val)
        return default if (math.isnan(f) or math.isinf(f)) else f
    except (TypeError, ValueError):
        return default


def _owm_get(endpoint, params):
    url = f'{OWM_BASE}/{endpoint}?' + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=6) as resp:
        return json.loads(resp.read().decode())


def _owm_snapshots(api_key):
    base_params = {
        'lat': SALVADOR_LAT, 'lon': SALVADOR_LON,
        'appid': api_key, 'units': 'metric',
    }
    cur = _owm_get('weather', base_params)
    fcast = _owm_get('forecast', base_params)
    fcast_list = fcast.get('list', [])
    now = datetime.datetime.now()

    base_pressure = _s(cur.get('main', {}).get('pressure', 1013))
    precip_1h = _s(cur.get('rain', {}).get('1h', 0))

    def cumul_precip(h_from, h_to):
        total = 0.0
        for e in fcast_list:
            dt_e = datetime.datetime.fromtimestamp(e['dt'])
            delta_h = (dt_e - now).total_seconds() / 3600
            if h_from <= delta_h <= h_to:
                total += _s(e.get('rain', {}).get('3h', 0))
        return round(total, 2)

    now_snap = {
        'precip_1h': precip_1h,
        'precip_3h': round(precip_1h * 3, 2),
        'precip_6h': round(precip_1h * 6 + cumul_precip(0, 6), 2),
        'precip_12h': round(precip_1h * 6 + cumul_precip(0, 12), 2),
        'precip_24h': round(precip_1h * 6 + cumul_precip(0, 24), 2),
        'pressure': base_pressure,
        'pressure_trend': 0.0,
        'humidity': _s(cur.get('main', {}).get('humidity', 80)),
        'wind_speed': _s(cur.get('wind', {}).get('speed', 2)),
        'temperature': _s(cur.get('main', {}).get('temp', 28)),
        'month': now.month,
        'hour_of_day': now.hour,
        'datetime': str(now),
    }

    snapshots = [now_snap]
    for horizon in HORIZONS[1:]:
        h = horizon['hours']
        target_dt = now + datetime.timedelta(hours=h)
        closest = min(
            fcast_list,
            key=lambda e: abs(datetime.datetime.fromtimestamp(e['dt']) - target_dt),
            default=None,
        )
        if closest:
            main = closest.get('main', {})
            future_press = _s(main.get('pressure', base_pressure))
            future_precip_3h = _s(closest.get('rain', {}).get('3h', 0))
            snap = {
                'precip_1h': round(future_precip_3h / 3, 2),
                'precip_3h': round(future_precip_3h, 2),
                'precip_6h': cumul_precip(h - 3, h + 3),
                'precip_12h': cumul_precip(h - 3, h + 9),
                'precip_24h': cumul_precip(h - 3, h + 21),
                'pressure': future_press,
                'pressure_trend': round((future_press - base_pressure) / h, 2),
                'humidity': _s(main.get('humidity', 80)),
                'wind_speed': _s(closest.get('wind', {}).get('speed', 2)),
                'temperature': _s(main.get('temp', 28)),
                'month': target_dt.month,
                'hour_of_day': target_dt.hour,
                'datetime': str(target_dt),
            }
        else:
            snap = dict(now_snap)
            snap['datetime'] = str(target_dt)
        snapshots.append(snap)

    return snapshots


def _mock_snapshots():
    """Seasonal mock for Salvador. Storm builds to +12h then subsides."""
    now = datetime.datetime.now()
    month = now.month
    is_rainy = month in (4, 5, 6, 12, 1, 2)

    base_p1h = 9.0 if is_rainy else 0.8
    base_hum = 89.0 if is_rainy else 68.0
    base_press = 1007.5 if is_rainy else 1016.0
    ptend = -3.8 if is_rainy else 0.2

    storm_factors = [1.0, 1.35, 1.7, 1.25, 0.65]
    snapshots = []
    for i, horizon in enumerate(HORIZONS):
        h = horizon['hours']
        sf = storm_factors[i]
        p1h = round(base_p1h * sf, 2)
        snap = {
            'precip_1h': p1h,
            'precip_3h': round(p1h * 2.8, 2),
            'precip_6h': round(p1h * 5.4, 2),
            'precip_12h': round(p1h * 9.2, 2),
            'precip_24h': round(p1h * 15.5, 2),
            'pressure': round(base_press - (i * 1.3 if i <= 2 else (4 - i) * 0.7), 2),
            'pressure_trend': round(ptend * (1.0 if i <= 2 else -0.4), 2),
            'humidity': round(min(base_hum + i * 2.2, 97.0), 2),
            'wind_speed': round(2.0 + sf * 1.5, 2),
            'temperature': round(28.5 - sf * 0.9, 2),
            'month': (now + datetime.timedelta(hours=h)).month,
            'hour_of_day': (now + datetime.timedelta(hours=h)).hour,
            'datetime': str(now + datetime.timedelta(hours=h)),
        }
        snapshots.append(snap)

    return snapshots


def get_forecast_snapshots():
    """Returns 5 climate snapshots (one per horizon). OWM first, mock fallback."""
    api_key = getattr(settings, 'OWM_API_KEY', None)
    if api_key:
        try:
            return _owm_snapshots(api_key)
        except Exception:
            pass
    return _mock_snapshots()
