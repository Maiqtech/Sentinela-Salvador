# Sentinela Salvador — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web platform that predicts climate disaster risk per neighborhood in Salvador using ML + resilience scoring, with a React map frontend and Django REST backend.

**Architecture:** Django backend with scikit-learn Random Forest trained on INMET historical data (2015-2021); neighborhood resilience scores pre-calculated from historical events + mocked IBGE social data; template-based alert generation (Claude API-ready); React + Leaflet frontend with clickable neighborhood map and dossier panel.

**Tech Stack:** Python 3.11, Django 4.2, DRF, scikit-learn, pandas, joblib, React 18, Vite, Leaflet.js, SQLite

---

## Project Structure

```
sentinela-salvador/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── README.md
│   ├── sentinela/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── apps/
│   │   ├── neighborhoods/
│   │   │   ├── models.py
│   │   │   ├── serializers.py
│   │   │   ├── views.py
│   │   │   ├── urls.py
│   │   │   └── management/commands/seed_neighborhoods.py
│   │   └── climate/
│   │       ├── models.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── services/
│   │           ├── data_loader.py
│   │           ├── predictor.py
│   │           └── alert_generator.py
│   └── ml/
│       ├── train.py
│       ├── features.py
│       └── saved_models/  (rf_model.pkl saved here)
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── data/
│       │   └── neighborhoods.geojson
│       ├── components/
│       │   ├── SalvadorMap.jsx
│       │   ├── Dossier.jsx
│       │   ├── AlertPanel.jsx
│       │   └── Legend.jsx
│       └── services/
│           └── api.js
└── README.md
```

---

### Task 1: Backend — Django Project Setup

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/sentinela/settings.py`
- Create: `backend/sentinela/urls.py`
- Create: `backend/manage.py`

- [ ] Create `backend/requirements.txt`:
```
Django==4.2.13
djangorestframework==3.14.0
django-cors-headers==4.3.1
pandas==2.1.4
scikit-learn==1.3.2
numpy==1.26.2
joblib==1.3.2
python-dotenv==1.0.0
```

- [ ] Create `backend/sentinela/settings.py`:
```python
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'apps.neighborhoods',
    'apps.climate',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'sentinela.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
}

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ML_MODEL_PATH = BASE_DIR / 'ml' / 'saved_models' / 'rf_model.pkl'
DATA_CSV_PATH = BASE_DIR.parent.parent / '01_DADOS_OFICIAIS-20260520T181803Z-3-001' / '01_DADOS_OFICIAIS' / 'clima_bahia_hackathon(1).csv'
```

- [ ] Create `backend/sentinela/urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    path('api/neighborhoods/', include('apps.neighborhoods.urls')),
    path('api/climate/', include('apps.climate.urls')),
]
```

- [ ] Create `backend/manage.py`:
```python
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinela.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

- [ ] Create `backend/sentinela/__init__.py` (empty)

- [ ] Run setup:
```bash
cd backend
pip install -r requirements.txt
```

---

### Task 2: Neighborhood Model

**Files:**
- Create: `backend/apps/__init__.py`
- Create: `backend/apps/neighborhoods/__init__.py`
- Create: `backend/apps/neighborhoods/models.py`

- [ ] Create `backend/apps/neighborhoods/models.py`:
```python
from django.db import models

class Neighborhood(models.Model):
    name = models.CharField(max_length=100)
    lat = models.FloatField()
    lon = models.FloatField()
    resilience_score = models.IntegerField()  # 0-100
    slope_risk = models.BooleanField(default=False)
    drainage_quality = models.CharField(max_length=20)  # poor/medium/good
    income_level = models.CharField(max_length=20)  # low/medium/high
    historical_events = models.IntegerField(default=0)
    slope_percentage = models.IntegerField(default=0)

    RISK_LOW = 0
    RISK_MEDIUM = 1
    RISK_HIGH = 2
    RISK_CRITICAL = 3

    current_risk_level = models.IntegerField(default=0)
    current_risk_probability = models.FloatField(default=0.0)
    current_precip_6h = models.FloatField(default=0.0)
    current_pressure_trend = models.FloatField(default=0.0)
    current_humidity = models.FloatField(default=0.0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def risk_label(self):
        labels = {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}
        return labels[self.current_risk_level]

    def risk_color(self):
        colors = {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}
        return colors[self.current_risk_level]
```

- [ ] Create `backend/apps/neighborhoods/migrations/__init__.py` (empty)

- [ ] Create initial migration:
```bash
cd backend
python manage.py makemigrations neighborhoods
python manage.py migrate
```

---

### Task 3: Neighborhood Seed Data

**Files:**
- Create: `backend/apps/neighborhoods/management/__init__.py`
- Create: `backend/apps/neighborhoods/management/commands/__init__.py`
- Create: `backend/apps/neighborhoods/management/commands/seed_neighborhoods.py`

- [ ] Create `backend/apps/neighborhoods/management/commands/seed_neighborhoods.py`:
```python
from django.core.management.base import BaseCommand
from apps.neighborhoods.models import Neighborhood

NEIGHBORHOODS = [
    {"name": "Subúrbio Ferroviário", "lat": -12.9100, "lon": -38.4800,
     "resilience_score": 18, "slope_risk": True, "drainage_quality": "poor",
     "income_level": "low", "historical_events": 8, "slope_percentage": 42},
    {"name": "Castelo Branco", "lat": -12.9476, "lon": -38.4611,
     "resilience_score": 22, "slope_risk": True, "drainage_quality": "poor",
     "income_level": "low", "historical_events": 6, "slope_percentage": 38},
    {"name": "Sete de Abril", "lat": -12.9503, "lon": -38.4529,
     "resilience_score": 25, "slope_risk": True, "drainage_quality": "poor",
     "income_level": "low", "historical_events": 5, "slope_percentage": 30},
    {"name": "São Caetano", "lat": -12.9600, "lon": -38.4400,
     "resilience_score": 28, "slope_risk": False, "drainage_quality": "poor",
     "income_level": "low", "historical_events": 4, "slope_percentage": 15},
    {"name": "Liberdade", "lat": -12.9700, "lon": -38.5050,
     "resilience_score": 30, "slope_risk": True, "drainage_quality": "poor",
     "income_level": "low", "historical_events": 5, "slope_percentage": 35},
    {"name": "Cajazeiras", "lat": -12.9285, "lon": -38.4388,
     "resilience_score": 35, "slope_risk": False, "drainage_quality": "medium",
     "income_level": "low", "historical_events": 3, "slope_percentage": 10},
    {"name": "Bonfim", "lat": -12.9244, "lon": -38.5088,
     "resilience_score": 40, "slope_risk": True, "drainage_quality": "medium",
     "income_level": "low", "historical_events": 4, "slope_percentage": 25},
    {"name": "Itapuã", "lat": -12.9309, "lon": -38.3541,
     "resilience_score": 45, "slope_risk": False, "drainage_quality": "medium",
     "income_level": "medium", "historical_events": 3, "slope_percentage": 8},
    {"name": "Rio Vermelho", "lat": -12.9983, "lon": -38.4827,
     "resilience_score": 62, "slope_risk": False, "drainage_quality": "medium",
     "income_level": "medium", "historical_events": 2, "slope_percentage": 5},
    {"name": "Ondina", "lat": -13.0108, "lon": -38.5195,
     "resilience_score": 65, "slope_risk": False, "drainage_quality": "medium",
     "income_level": "medium", "historical_events": 2, "slope_percentage": 8},
    {"name": "Campo Grande", "lat": -12.9800, "lon": -38.5200,
     "resilience_score": 70, "slope_risk": False, "drainage_quality": "good",
     "income_level": "high", "historical_events": 1, "slope_percentage": 3},
    {"name": "Barra", "lat": -13.0101, "lon": -38.5258,
     "resilience_score": 72, "slope_risk": False, "drainage_quality": "good",
     "income_level": "high", "historical_events": 1, "slope_percentage": 2},
    {"name": "Pituba", "lat": -13.0020, "lon": -38.4592,
     "resilience_score": 78, "slope_risk": False, "drainage_quality": "good",
     "income_level": "high", "historical_events": 1, "slope_percentage": 2},
    {"name": "Vitória", "lat": -13.0000, "lon": -38.5100,
     "resilience_score": 80, "slope_risk": False, "drainage_quality": "good",
     "income_level": "high", "historical_events": 1, "slope_percentage": 3},
    {"name": "Graça", "lat": -12.9900, "lon": -38.5100,
     "resilience_score": 82, "slope_risk": False, "drainage_quality": "good",
     "income_level": "high", "historical_events": 0, "slope_percentage": 2},
]

class Command(BaseCommand):
    help = 'Seed neighborhoods with resilience data'

    def handle(self, *args, **options):
        Neighborhood.objects.all().delete()
        for data in NEIGHBORHOODS:
            Neighborhood.objects.create(**data)
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(NEIGHBORHOODS)} neighborhoods'))
```

- [ ] Run seed:
```bash
python manage.py seed_neighborhoods
```

---

### Task 4: ML Feature Engineering

**Files:**
- Create: `backend/ml/__init__.py`
- Create: `backend/ml/features.py`

- [ ] Create `backend/ml/features.py`:
```python
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
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['hour'].astype(str).str.zfill(4), format='%Y-%m-%d %H%M', errors='coerce')
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
```

---

### Task 5: ML Model Training Script

**Files:**
- Create: `backend/ml/train.py`
- Create: `backend/ml/saved_models/.gitkeep`

- [ ] Create `backend/ml/train.py`:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from ml.features import load_and_filter_csv, build_features, label_risk, get_feature_columns

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '01_DADOS_OFICIAIS-20260520T181803Z-3-001',
    '01_DADOS_OFICIAIS',
    'clima_bahia_hackathon(1).csv'
)

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'saved_models', 'rf_model.pkl')

def train():
    print("Loading data...")
    df = load_and_filter_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows from 2015-2021")

    print("Building features...")
    df = build_features(df)
    df['risk_label'] = df['precip_6h'].apply(label_risk)

    feature_cols = get_feature_columns()
    X = df[feature_cols].values
    y = df['risk_label'].values

    print(f"Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    print("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Baixo', 'Médio', 'Alto', 'Crítico']))

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

if __name__ == '__main__':
    train()
```

- [ ] Run training:
```bash
cd backend
python ml/train.py
```

---

### Task 6: Prediction & Alert Services

**Files:**
- Create: `backend/apps/climate/__init__.py`
- Create: `backend/apps/climate/services/__init__.py`
- Create: `backend/apps/climate/services/data_loader.py`
- Create: `backend/apps/climate/services/predictor.py`
- Create: `backend/apps/climate/services/alert_generator.py`

- [ ] Create `backend/apps/climate/services/data_loader.py`:
```python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentinela.settings')

import pandas as pd
from django.conf import settings
from ml.features import load_and_filter_csv, build_features

_df_cache = None

def get_dataframe():
    global _df_cache
    if _df_cache is None:
        df = load_and_filter_csv(str(settings.DATA_CSV_PATH))
        _df_cache = build_features(df)
    return _df_cache

def get_current_climate_snapshot(reference_date: str = '2021-12-25'):
    df = get_dataframe()
    mask = df['datetime'].dt.date == pd.to_datetime(reference_date).date()
    day_df = df[mask]
    if day_df.empty:
        day_df = df.tail(24)
    last_row = day_df.iloc[-1]
    return {
        'datetime': str(last_row['datetime']),
        'precip_1h': round(float(last_row['precip_1h']), 2),
        'precip_3h': round(float(last_row['precip_3h']), 2),
        'precip_6h': round(float(last_row['precip_6h']), 2),
        'precip_12h': round(float(last_row['precip_12h']), 2),
        'precip_24h': round(float(last_row['precip_24h']), 2),
        'pressure': round(float(last_row.get('pressure', 1013)), 2),
        'pressure_trend': round(float(last_row['pressure_trend']), 2),
        'humidity': round(float(last_row.get('humidity', 80)), 2),
        'wind_speed': round(float(last_row.get('wind_speed', 2)), 2),
        'month': int(last_row['month']),
        'hour_of_day': int(last_row['hour_of_day']),
        'temperature': round(float(last_row.get('temperature', 28)), 2),
    }

def simulate_climate_snapshot(precip_mm: float, hours: int):
    base = get_current_climate_snapshot()
    base['precip_1h'] = precip_mm / hours
    base['precip_3h'] = precip_mm if hours <= 3 else precip_mm * 3 / hours
    base['precip_6h'] = precip_mm if hours <= 6 else precip_mm * 6 / hours
    base['precip_12h'] = precip_mm if hours <= 12 else precip_mm * 12 / hours
    base['precip_24h'] = precip_mm
    base['pressure_trend'] = -3.5
    base['humidity'] = 92.0
    return base
```

- [ ] Create `backend/apps/climate/services/predictor.py`:
```python
import joblib
import numpy as np
from django.conf import settings
from ml.features import get_feature_columns

_model_cache = None

def get_model():
    global _model_cache
    if _model_cache is None:
        _model_cache = joblib.load(str(settings.ML_MODEL_PATH))
    return _model_cache

def predict_risk(climate_snapshot: dict) -> dict:
    model = get_model()
    feature_cols = get_feature_columns()
    features = np.array([[climate_snapshot[col] for col in feature_cols]])
    risk_level = int(model.predict(features)[0])
    probabilities = model.predict_proba(features)[0]
    return {
        'risk_level': risk_level,
        'probability': round(float(probabilities[risk_level]) * 100, 1),
        'probabilities': {
            'low': round(float(probabilities[0]) * 100, 1),
            'medium': round(float(probabilities[1]) * 100, 1),
            'high': round(float(probabilities[2]) * 100, 1),
            'critical': round(float(probabilities[3]) * 100, 1),
        }
    }
```

- [ ] Create `backend/apps/climate/services/alert_generator.py`:
```python
RISK_LABELS = {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}
RISK_COLORS = {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}

DRAINAGE_PT = {'poor': 'deficiente', 'medium': 'regular', 'good': 'boa'}
INCOME_PT = {'low': 'baixa', 'medium': 'média', 'high': 'alta'}

def generate_alert(neighborhood, climate_snapshot: dict, risk_prediction: dict) -> str:
    name = neighborhood.name
    risk = risk_prediction['risk_level']
    prob = risk_prediction['probability']
    precip_6h = climate_snapshot['precip_6h']
    score = neighborhood.resilience_score

    if risk == 3:
        return (
            f"ALERTA CRÍTICO — {name} apresenta risco máximo de alagamento e deslizamento "
            f"nas próximas horas. Precipitação acumulada de {precip_6h:.1f}mm nas últimas 6h "
            f"combinada com score de resiliência de {score}/100. "
            f"Probabilidade de evento grave: {prob}%. Acionar equipes imediatamente."
        )
    elif risk == 2:
        return (
            f"ALERTA ALTO — {name} com risco elevado de alagamento. "
            f"{precip_6h:.1f}mm acumulados nas últimas 6h. "
            f"Score de resiliência: {score}/100. Monitorar e pré-posicionar equipes."
        )
    elif risk == 1:
        return (
            f"ATENÇÃO — {name} em nível de atenção. {precip_6h:.1f}mm nas últimas 6h. "
            f"Score de resiliência: {score}/100. Monitorar evolução."
        )
    return (
        f"{name} — Situação normal. {precip_6h:.1f}mm nas últimas 6h. "
        f"Score de resiliência: {score}/100. Sem ação necessária."
    )

def generate_dossier_text(neighborhood, climate_snapshot: dict, risk_prediction: dict) -> dict:
    risk = risk_prediction['risk_level']
    precip_6h = climate_snapshot['precip_6h']
    pressure_trend = climate_snapshot['pressure_trend']
    humidity = climate_snapshot['humidity']
    score = neighborhood.resilience_score

    threshold_status = "ACIMA" if precip_6h >= 50 else ("PRÓXIMO" if precip_6h >= 35 else "ABAIXO")
    pressure_desc = "em queda" if pressure_trend < -2 else ("estável" if pressure_trend > -1 else "levemente em queda")

    recommendation = {
        3: f"Acionar equipes preventivas imediatamente. Prioridade máxima sobre outros bairros com score mais alto.",
        2: f"Pré-posicionar equipes. Emitir alerta para moradores de encostas.",
        1: f"Monitorar evolução. Verificar pontos históricos de alagamento.",
        0: f"Nenhuma ação necessária. Manter monitoramento padrão.",
    }[risk]

    return {
        'situacao_atual': {
            'precip_6h': f"{precip_6h:.1f}mm (limiar crítico: 50mm) — {threshold_status} do limiar",
            'pressure_trend': f"{pressure_trend:+.1f}mB nas últimas 3h — pressão {pressure_desc}",
            'humidity': f"{humidity:.0f}%",
        },
        'projecao': {
            'risco': RISK_LABELS[risk],
            'probabilidade': f"{risk_prediction['probability']}%",
        },
        'vulnerabilidade': {
            'score_resiliencia': f"{score}/100",
            'drenagem': DRAINAGE_PT.get(neighborhood.drainage_quality, neighborhood.drainage_quality),
            'renda': INCOME_PT.get(neighborhood.income_level, neighborhood.income_level),
            'percentual_encosta': f"{neighborhood.slope_percentage}% dos domicílios em área de encosta",
            'eventos_historicos': f"{neighborhood.historical_events} eventos graves registrados (2000-2021)",
        },
        'recomendacao': recommendation,
    }
```

---

### Task 7: API Endpoints

**Files:**
- Create: `backend/apps/neighborhoods/serializers.py`
- Create: `backend/apps/neighborhoods/views.py`
- Create: `backend/apps/neighborhoods/urls.py`
- Create: `backend/apps/climate/models.py`
- Create: `backend/apps/climate/views.py`
- Create: `backend/apps/climate/urls.py`

- [ ] Create `backend/apps/neighborhoods/serializers.py`:
```python
from rest_framework import serializers
from .models import Neighborhood

class NeighborhoodSerializer(serializers.ModelSerializer):
    risk_label = serializers.SerializerMethodField()
    risk_color = serializers.SerializerMethodField()

    class Meta:
        model = Neighborhood
        fields = [
            'id', 'name', 'lat', 'lon', 'resilience_score',
            'current_risk_level', 'current_risk_probability',
            'current_precip_6h', 'risk_label', 'risk_color',
        ]

    def get_risk_label(self, obj):
        return obj.risk_label()

    def get_risk_color(self, obj):
        return obj.risk_color()
```

- [ ] Create `backend/apps/neighborhoods/views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Neighborhood
from .serializers import NeighborhoodSerializer
from apps.climate.services.data_loader import get_current_climate_snapshot, simulate_climate_snapshot
from apps.climate.services.predictor import predict_risk
from apps.climate.services.alert_generator import generate_alert, generate_dossier_text

class NeighborhoodListView(APIView):
    def get(self, request):
        reference_date = request.query_params.get('date', '2021-12-25')
        try:
            climate = get_current_climate_snapshot(reference_date)
            prediction = predict_risk(climate)
            neighborhoods = Neighborhood.objects.all()
            for n in neighborhoods:
                factor = 1 + (100 - n.resilience_score) / 200
                adjusted_prob = min(prediction['probability'] * factor, 99)
                if adjusted_prob >= 85:
                    risk = 3
                elif adjusted_prob >= 60:
                    risk = 2
                elif adjusted_prob >= 30:
                    risk = 1
                else:
                    risk = 0
                n.current_risk_level = risk
                n.current_risk_probability = round(adjusted_prob, 1)
                n.current_precip_6h = climate['precip_6h']
                n.current_pressure_trend = climate['pressure_trend']
                n.current_humidity = climate['humidity']
            Neighborhood.objects.bulk_update(
                neighborhoods,
                ['current_risk_level', 'current_risk_probability', 'current_precip_6h',
                 'current_pressure_trend', 'current_humidity']
            )
            serializer = NeighborhoodSerializer(neighborhoods, many=True)
            critical = [n for n in neighborhoods if n.current_risk_level == 3]
            top_alert = None
            if critical:
                priority = min(critical, key=lambda x: x.resilience_score)
                top_alert = generate_alert(priority, climate, prediction)
            return Response({
                'neighborhoods': serializer.data,
                'climate_snapshot': climate,
                'top_alert': top_alert,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NeighborhoodDossierView(APIView):
    def get(self, request, pk):
        try:
            neighborhood = Neighborhood.objects.get(pk=pk)
            reference_date = request.query_params.get('date', '2021-12-25')
            climate = get_current_climate_snapshot(reference_date)
            prediction = predict_risk(climate)
            factor = 1 + (100 - neighborhood.resilience_score) / 200
            adjusted_prob = min(prediction['probability'] * factor, 99)
            if adjusted_prob >= 85:
                risk_level = 3
            elif adjusted_prob >= 60:
                risk_level = 2
            elif adjusted_prob >= 30:
                risk_level = 1
            else:
                risk_level = 0
            prediction['risk_level'] = risk_level
            prediction['probability'] = round(adjusted_prob, 1)
            alert = generate_alert(neighborhood, climate, prediction)
            dossier = generate_dossier_text(neighborhood, climate, prediction)
            serializer = NeighborhoodSerializer(neighborhood)
            return Response({
                'neighborhood': serializer.data,
                'alert': alert,
                'dossier': dossier,
                'climate': climate,
                'prediction': prediction,
            })
        except Neighborhood.DoesNotExist:
            return Response({'error': 'Neighborhood not found'}, status=404)

class SimulateView(APIView):
    def post(self, request):
        precip_mm = float(request.data.get('precip_mm', 80))
        hours = int(request.data.get('hours', 6))
        climate = simulate_climate_snapshot(precip_mm, hours)
        prediction = predict_risk(climate)
        neighborhoods = Neighborhood.objects.all()
        results = []
        for n in neighborhoods:
            factor = 1 + (100 - n.resilience_score) / 200
            adjusted_prob = min(prediction['probability'] * factor, 99)
            if adjusted_prob >= 85:
                risk = 3
            elif adjusted_prob >= 60:
                risk = 2
            elif adjusted_prob >= 30:
                risk = 1
            else:
                risk = 0
            results.append({
                'id': n.id,
                'name': n.name,
                'risk_level': risk,
                'risk_label': {0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico'}[risk],
                'risk_color': {0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444'}[risk],
                'probability': round(adjusted_prob, 1),
                'resilience_score': n.resilience_score,
            })
        results.sort(key=lambda x: (x['risk_level'], -x['probability']), reverse=True)
        return Response({'simulation': results, 'climate_input': climate})
```

- [ ] Create `backend/apps/neighborhoods/urls.py`:
```python
from django.urls import path
from .views import NeighborhoodListView, NeighborhoodDossierView, SimulateView

urlpatterns = [
    path('', NeighborhoodListView.as_view()),
    path('<int:pk>/dossier/', NeighborhoodDossierView.as_view()),
    path('simulate/', SimulateView.as_view()),
]
```

- [ ] Create `backend/apps/climate/models.py` (empty, no models needed):
```python
# No models needed — climate data is loaded from CSV
```

- [ ] Create `backend/apps/climate/views.py`:
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.climate.services.data_loader import get_current_climate_snapshot

class CurrentClimateView(APIView):
    def get(self, request):
        reference_date = request.query_params.get('date', '2021-12-25')
        data = get_current_climate_snapshot(reference_date)
        return Response(data)
```

- [ ] Create `backend/apps/climate/urls.py`:
```python
from django.urls import path
from .views import CurrentClimateView

urlpatterns = [
    path('current/', CurrentClimateView.as_view()),
]
```

- [ ] Create `backend/apps/climate/migrations/__init__.py` (empty)

- [ ] Run migrations and test:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
# Test: curl http://localhost:8000/api/neighborhoods/
```

---

### Task 8: Frontend Setup

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`

- [ ] Create `frontend/package.json`:
```json
{
  "name": "sentinela-salvador",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "leaflet": "^1.9.4",
    "react-leaflet": "^4.2.1",
    "axios": "^1.6.2"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.1",
    "vite": "^5.0.8"
  }
}
```

- [ ] Create `frontend/vite.config.js`:
```js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

- [ ] Create `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentinela Salvador</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] Create `frontend/src/main.jsx`:
```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

- [ ] Install dependencies:
```bash
cd frontend
npm install
```

---

### Task 9: API Service & Neighborhoods GeoJSON

**Files:**
- Create: `frontend/src/services/api.js`
- Create: `frontend/src/data/neighborhoods.geojson`

- [ ] Create `frontend/src/services/api.js`:
```js
import axios from 'axios'

const BASE = '/api'

export const fetchNeighborhoods = (date = '2021-12-25') =>
  axios.get(`${BASE}/neighborhoods/?date=${date}`).then(r => r.data)

export const fetchDossier = (id, date = '2021-12-25') =>
  axios.get(`${BASE}/neighborhoods/${id}/dossier/?date=${date}`).then(r => r.data)

export const simulateRain = (precip_mm, hours) =>
  axios.post(`${BASE}/neighborhoods/simulate/`, { precip_mm, hours }).then(r => r.data)

export const fetchCurrentClimate = (date = '2021-12-25') =>
  axios.get(`${BASE}/climate/current/?date=${date}`).then(r => r.data)
```

- [ ] Create `frontend/src/data/neighborhoods.geojson`:
```json
{
  "type": "FeatureCollection",
  "features": [
    {"type":"Feature","properties":{"id":1,"name":"Subúrbio Ferroviário"},"geometry":{"type":"Polygon","coordinates":[[[-38.495,-12.905],[-38.465,-12.905],[-38.465,-12.920],[-38.495,-12.920],[-38.495,-12.905]]]}},
    {"type":"Feature","properties":{"id":2,"name":"Castelo Branco"},"geometry":{"type":"Polygon","coordinates":[[[-38.470,-12.942],[-38.450,-12.942],[-38.450,-12.957],[-38.470,-12.957],[-38.470,-12.942]]]}},
    {"type":"Feature","properties":{"id":3,"name":"Sete de Abril"},"geometry":{"type":"Polygon","coordinates":[[[-38.460,-12.945],[-38.442,-12.945],[-38.442,-12.958],[-38.460,-12.958],[-38.460,-12.945]]]}},
    {"type":"Feature","properties":{"id":4,"name":"São Caetano"},"geometry":{"type":"Polygon","coordinates":[[[-38.448,-12.954],[-38.430,-12.954],[-38.430,-12.968],[-38.448,-12.968],[-38.448,-12.954]]]}},
    {"type":"Feature","properties":{"id":5,"name":"Liberdade"},"geometry":{"type":"Polygon","coordinates":[[[-38.515,-12.964],[-38.495,-12.964],[-38.495,-12.978],[-38.515,-12.978],[-38.515,-12.964]]]}},
    {"type":"Feature","properties":{"id":6,"name":"Cajazeiras"},"geometry":{"type":"Polygon","coordinates":[[[-38.448,-12.922],[-38.428,-12.922],[-38.428,-12.937],[-38.448,-12.937],[-38.448,-12.922]]]}},
    {"type":"Feature","properties":{"id":7,"name":"Bonfim"},"geometry":{"type":"Polygon","coordinates":[[[-38.520,-12.918],[-38.500,-12.918],[-38.500,-12.932],[-38.520,-12.932],[-38.520,-12.918]]]}},
    {"type":"Feature","properties":{"id":8,"name":"Itapuã"},"geometry":{"type":"Polygon","coordinates":[[[-38.365,-12.925],[-38.343,-12.925],[-38.343,-12.939],[-38.365,-12.939],[-38.365,-12.925]]]}},
    {"type":"Feature","properties":{"id":9,"name":"Rio Vermelho"},"geometry":{"type":"Polygon","coordinates":[[[-38.493,-12.992],[-38.473,-12.992],[-38.473,-13.006],[-38.493,-13.006],[-38.493,-12.992]]]}},
    {"type":"Feature","properties":{"id":10,"name":"Ondina"},"geometry":{"type":"Polygon","coordinates":[[[-38.527,-13.005],[-38.510,-13.005],[-38.510,-13.018],[-38.527,-13.018],[-38.527,-13.005]]]}},
    {"type":"Feature","properties":{"id":11,"name":"Campo Grande"},"geometry":{"type":"Polygon","coordinates":[[[-38.528,-12.973],[-38.510,-12.973],[-38.510,-12.988],[-38.528,-12.988],[-38.528,-12.973]]]}},
    {"type":"Feature","properties":{"id":12,"name":"Barra"},"geometry":{"type":"Polygon","coordinates":[[[-38.533,-13.004],[-38.518,-13.004],[-38.518,-13.017],[-38.533,-13.017],[-38.533,-13.004]]]}},
    {"type":"Feature","properties":{"id":13,"name":"Pituba"},"geometry":{"type":"Polygon","coordinates":[[[-38.468,-12.995],[-38.450,-12.995],[-38.450,-13.009],[-38.468,-13.009],[-38.468,-12.995]]]}},
    {"type":"Feature","properties":{"id":14,"name":"Vitória"},"geometry":{"type":"Polygon","coordinates":[[[-38.518,-12.993],[-38.502,-12.993],[-38.502,-13.007],[-38.518,-13.007],[-38.518,-12.993]]]}},
    {"type":"Feature","properties":{"id":15,"name":"Graça"},"geometry":{"type":"Polygon","coordinates":[[[-38.518,-12.983],[-38.502,-12.983],[-38.502,-12.997],[-38.518,-12.997],[-38.518,-12.983]]]}},
    {"type":"Feature","properties":{"id":16,"name":"Itaigara"},"geometry":{"type":"Polygon","coordinates":[[[-38.475,-12.998],[-38.458,-12.998],[-38.458,-13.012],[-38.475,-13.012],[-38.475,-12.998]]]}}
  ]
}
```

---

### Task 10: Frontend Components

**Files:**
- Create: `frontend/src/index.css`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/components/SalvadorMap.jsx`
- Create: `frontend/src/components/AlertPanel.jsx`
- Create: `frontend/src/components/Dossier.jsx`
- Create: `frontend/src/components/Legend.jsx`

- [ ] Create `frontend/src/index.css`:
```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Inter', system-ui, sans-serif; background: #0f172a; color: #f1f5f9; }
.app { display: flex; flex-direction: column; height: 100vh; }
.header { background: #1e293b; padding: 12px 24px; display: flex; align-items: center; gap: 16px; border-bottom: 1px solid #334155; }
.header h1 { font-size: 1.25rem; font-weight: 700; color: #f1f5f9; }
.header .subtitle { font-size: 0.8rem; color: #94a3b8; }
.badge { background: #ef4444; color: white; font-size: 0.7rem; padding: 2px 8px; border-radius: 99px; font-weight: 600; }
.main { display: flex; flex: 1; overflow: hidden; }
.map-container { flex: 1; position: relative; }
.sidebar { width: 380px; background: #1e293b; overflow-y: auto; border-left: 1px solid #334155; display: flex; flex-direction: column; }
.alert-panel { padding: 16px; border-bottom: 1px solid #334155; }
.alert-box { border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; line-height: 1.5; }
.alert-critical { background: #450a0a; border: 1px solid #ef4444; color: #fca5a5; }
.alert-high { background: #431407; border: 1px solid #f97316; color: #fdba74; }
.alert-medium { background: #422006; border: 1px solid #eab308; color: #fde047; }
.alert-normal { background: #052e16; border: 1px solid #22c55e; color: #86efac; }
.dossier { flex: 1; padding: 16px; }
.dossier h2 { font-size: 1rem; font-weight: 700; margin-bottom: 4px; }
.dossier .risk-badge { display: inline-block; padding: 2px 10px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; margin-bottom: 12px; }
.section { margin-bottom: 14px; }
.section-title { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 6px; font-weight: 600; }
.metric { display: flex; justify-content: space-between; font-size: 0.82rem; padding: 4px 0; border-bottom: 1px solid #1e293b; }
.metric-label { color: #94a3b8; }
.metric-value { color: #f1f5f9; font-weight: 500; }
.recommendation { background: #0f172a; border-radius: 6px; padding: 10px 12px; font-size: 0.82rem; line-height: 1.5; color: #e2e8f0; }
.sim-panel { padding: 16px; border-top: 1px solid #334155; }
.sim-panel h3 { font-size: 0.85rem; font-weight: 600; margin-bottom: 10px; color: #94a3b8; }
.sim-controls { display: flex; gap: 8px; align-items: flex-end; }
.sim-input { flex: 1; }
.sim-input label { display: block; font-size: 0.72rem; color: #64748b; margin-bottom: 4px; }
.sim-input input { width: 100%; background: #0f172a; border: 1px solid #334155; color: #f1f5f9; padding: 6px 10px; border-radius: 6px; font-size: 0.85rem; }
.btn { background: #3b82f6; color: white; border: none; padding: 7px 14px; border-radius: 6px; font-size: 0.82rem; cursor: pointer; white-space: nowrap; }
.btn:hover { background: #2563eb; }
.legend { padding: 12px 16px; border-top: 1px solid #334155; }
.legend h4 { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 8px; }
.legend-items { display: flex; gap: 12px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 0.78rem; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; }
.empty-state { color: #64748b; font-size: 0.85rem; text-align: center; padding: 32px; }
.score-bar { height: 6px; background: #0f172a; border-radius: 3px; margin-top: 4px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 3px; transition: width 0.3s; }
.date-selector { padding: 12px 16px; border-bottom: 1px solid #334155; }
.date-selector label { font-size: 0.72rem; color: #64748b; display: block; margin-bottom: 4px; }
.date-selector input { background: #0f172a; border: 1px solid #334155; color: #f1f5f9; padding: 5px 10px; border-radius: 6px; font-size: 0.82rem; width: 100%; }
```

- [ ] Create `frontend/src/components/Legend.jsx`:
```jsx
export default function Legend() {
  const items = [
    { color: '#22c55e', label: 'Baixo' },
    { color: '#eab308', label: 'Médio' },
    { color: '#f97316', label: 'Alto' },
    { color: '#ef4444', label: 'Crítico' },
  ]
  return (
    <div className="legend">
      <h4>Nível de Risco</h4>
      <div className="legend-items">
        {items.map(i => (
          <div key={i.label} className="legend-item">
            <div className="legend-dot" style={{ background: i.color }} />
            <span>{i.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] Create `frontend/src/components/AlertPanel.jsx`:
```jsx
export default function AlertPanel({ alert, climate }) {
  if (!alert && !climate) return null
  const getClass = (text) => {
    if (!text) return 'alert-normal'
    if (text.includes('CRÍTICO')) return 'alert-critical'
    if (text.includes('ALTO')) return 'alert-high'
    if (text.includes('ATENÇÃO')) return 'alert-medium'
    return 'alert-normal'
  }
  return (
    <div className="alert-panel">
      <div style={{ fontSize: '0.7rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '8px' }}>
        Alerta Automático
      </div>
      {alert ? (
        <div className={`alert-box ${getClass(alert)}`}>{alert}</div>
      ) : (
        <div className="alert-box alert-normal">Sistema monitorando. Sem alertas ativos.</div>
      )}
      {climate && (
        <div style={{ marginTop: '8px', fontSize: '0.75rem', color: '#64748b', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <span>🌧 {climate.precip_6h?.toFixed(1)}mm/6h</span>
          <span>💧 {climate.humidity?.toFixed(0)}%</span>
          <span>📊 {climate.pressure?.toFixed(1)}mB</span>
          <span>💨 {climate.wind_speed?.toFixed(1)}m/s</span>
        </div>
      )}
    </div>
  )
}
```

- [ ] Create `frontend/src/components/Dossier.jsx`:
```jsx
export default function Dossier({ data, onClose }) {
  if (!data) return (
    <div className="dossier">
      <div className="empty-state">
        Clique em um bairro no mapa para ver o dossiê completo
      </div>
    </div>
  )

  const { neighborhood, alert, dossier, prediction } = data
  const riskColors = { 0: '#22c55e', 1: '#eab308', 2: '#f97316', 3: '#ef4444' }
  const riskLabels = { 0: 'Baixo', 1: 'Médio', 2: 'Alto', 3: 'Crítico' }
  const color = riskColors[prediction?.risk_level ?? 0]
  const label = riskLabels[prediction?.risk_level ?? 0]
  const score = neighborhood.resilience_score
  const scoreColor = score < 35 ? '#ef4444' : score < 60 ? '#f97316' : '#22c55e'

  return (
    <div className="dossier">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '4px' }}>
        <h2>{neighborhood.name}</h2>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '1.1rem' }}>✕</button>
      </div>
      <span className="risk-badge" style={{ background: color + '20', color, border: `1px solid ${color}` }}>
        Risco {label} — {prediction?.probability}%
      </span>

      <div className="section">
        <div className="section-title">Situação Atual</div>
        {dossier?.situacao_atual && Object.entries(dossier.situacao_atual).map(([k, v]) => (
          <div className="metric" key={k}>
            <span className="metric-label">{k.replace(/_/g,' ')}</span>
            <span className="metric-value" style={{ maxWidth: '55%', textAlign: 'right' }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="section">
        <div className="section-title">Score de Resiliência</div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          <span style={{ fontSize: '1.4rem', fontWeight: 700, color: scoreColor }}>{score}</span>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>/ 100</span>
        </div>
        <div className="score-bar">
          <div className="score-fill" style={{ width: `${score}%`, background: scoreColor }} />
        </div>
      </div>

      <div className="section">
        <div className="section-title">Vulnerabilidade do Bairro</div>
        {dossier?.vulnerabilidade && Object.entries(dossier.vulnerabilidade).map(([k, v]) => (
          <div className="metric" key={k}>
            <span className="metric-label">{k.replace(/_/g,' ')}</span>
            <span className="metric-value" style={{ maxWidth: '55%', textAlign: 'right' }}>{v}</span>
          </div>
        ))}
      </div>

      <div className="section">
        <div className="section-title">Recomendação da IA</div>
        <div className="recommendation">{dossier?.recomendacao}</div>
      </div>
    </div>
  )
}
```

- [ ] Create `frontend/src/components/SalvadorMap.jsx`:
```jsx
import { useEffect, useRef } from 'react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import geojsonData from '../data/neighborhoods.geojson'

export default function SalvadorMap({ neighborhoods, onNeighborhoodClick, simulationData }) {
  const mapRef = useRef(null)
  const mapInstance = useRef(null)
  const layerRef = useRef(null)

  useEffect(() => {
    if (mapInstance.current) return
    mapInstance.current = L.map(mapRef.current, {
      center: [-12.97, -38.50],
      zoom: 12,
      zoomControl: true,
    })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      opacity: 0.4,
    }).addTo(mapInstance.current)
  }, [])

  useEffect(() => {
    if (!mapInstance.current || !neighborhoods.length) return
    if (layerRef.current) layerRef.current.remove()

    const riskMap = {}
    const dataSource = simulationData || neighborhoods
    dataSource.forEach(n => {
      riskMap[n.id] = {
        risk_level: n.risk_level ?? n.current_risk_level,
        risk_color: n.risk_color,
        risk_label: n.risk_label,
        probability: n.probability ?? n.current_risk_probability,
        resilience_score: n.resilience_score,
      }
    })

    layerRef.current = L.geoJSON(geojsonData, {
      style: (feature) => {
        const id = feature.properties.id
        const data = riskMap[id]
        const color = data?.risk_color || '#334155'
        return {
          fillColor: color,
          fillOpacity: 0.75,
          color: '#1e293b',
          weight: 2,
        }
      },
      onEachFeature: (feature, layer) => {
        const id = feature.properties.id
        const data = riskMap[id]
        layer.bindTooltip(
          `<b>${feature.properties.name}</b><br/>Risco: ${data?.risk_label || '–'}<br/>Score: ${data?.resilience_score || '–'}/100`,
          { sticky: true, className: 'leaflet-tooltip-dark' }
        )
        layer.on('click', () => onNeighborhoodClick(id))
      },
    }).addTo(mapInstance.current)
  }, [neighborhoods, simulationData])

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
}
```

- [ ] Create `frontend/src/App.jsx`:
```jsx
import { useState, useEffect } from 'react'
import SalvadorMap from './components/SalvadorMap'
import AlertPanel from './components/AlertPanel'
import Dossier from './components/Dossier'
import Legend from './components/Legend'
import { fetchNeighborhoods, fetchDossier, simulateRain } from './services/api'

export default function App() {
  const [neighborhoods, setNeighborhoods] = useState([])
  const [topAlert, setTopAlert] = useState(null)
  const [climate, setClimate] = useState(null)
  const [dossier, setDossier] = useState(null)
  const [loading, setLoading] = useState(true)
  const [date, setDate] = useState('2021-12-25')
  const [simPrecip, setSimPrecip] = useState(80)
  const [simHours, setSimHours] = useState(6)
  const [simData, setSimData] = useState(null)

  const load = async (d) => {
    setLoading(true)
    try {
      const data = await fetchNeighborhoods(d)
      setNeighborhoods(data.neighborhoods)
      setTopAlert(data.top_alert)
      setClimate(data.climate_snapshot)
      setSimData(null)
    } catch (e) {
      console.error(e)
    }
    setLoading(false)
  }

  useEffect(() => { load(date) }, [])

  const handleDateChange = (e) => {
    setDate(e.target.value)
    load(e.target.value)
  }

  const handleNeighborhoodClick = async (id) => {
    try {
      const data = await fetchDossier(id, date)
      setDossier(data)
    } catch (e) {
      console.error(e)
    }
  }

  const handleSimulate = async () => {
    try {
      const data = await simulateRain(simPrecip, simHours)
      setSimData(data.simulation)
      setTopAlert(`SIMULAÇÃO: ${simPrecip}mm em ${simHours}h — ${data.simulation.filter(n => n.risk_level >= 2).length} bairros em risco alto/crítico`)
    } catch (e) {
      console.error(e)
    }
  }

  const criticalCount = (simData || neighborhoods).filter(n => (n.risk_level ?? n.current_risk_level) >= 2).length

  return (
    <div className="app">
      <div className="header">
        <div>
          <h1>Sentinela Salvador</h1>
          <div className="subtitle">Plataforma de Inteligência Climática</div>
        </div>
        {criticalCount > 0 && (
          <span className="badge">{criticalCount} bairro{criticalCount > 1 ? 's' : ''} em risco alto/crítico</span>
        )}
        {loading && <span style={{ fontSize: '0.8rem', color: '#64748b' }}>Carregando...</span>}
      </div>

      <div className="main">
        <div className="map-container">
          <SalvadorMap
            neighborhoods={neighborhoods}
            onNeighborhoodClick={handleNeighborhoodClick}
            simulationData={simData}
          />
        </div>

        <div className="sidebar">
          <div className="date-selector">
            <label>Data de referência</label>
            <input type="date" value={date} onChange={handleDateChange} min="2015-01-01" max="2021-12-31" />
          </div>

          <AlertPanel alert={topAlert} climate={climate} />

          <Dossier data={dossier} onClose={() => setDossier(null)} />

          <div className="sim-panel">
            <h3>Simulação de Cenário</h3>
            <div className="sim-controls">
              <div className="sim-input">
                <label>Precipitação (mm)</label>
                <input type="number" value={simPrecip} onChange={e => setSimPrecip(Number(e.target.value))} min="0" max="200" />
              </div>
              <div className="sim-input">
                <label>Em (horas)</label>
                <input type="number" value={simHours} onChange={e => setSimHours(Number(e.target.value))} min="1" max="24" />
              </div>
              <button className="btn" onClick={handleSimulate}>Simular</button>
            </div>
          </div>

          <Legend />
        </div>
      </div>
    </div>
  )
}
```

---

### Task 11: Documentation

**Files:**
- Create: `README.md`
- Create: `backend/README.md`
- Create: `frontend/README.md`

- [ ] Create root `README.md`:
```markdown
# Sentinela Salvador — Plataforma de Inteligência Climática

Sistema de predição de risco climático urbano para Salvador/BA, desenvolvido no Hackathon BaIA Week 2026.

## O Problema
Salvador registrou 360mm de chuva em dezembro de 2021 — 6x o esperado. A Defesa Civil (CODESAL) age durante o desastre, não antes. O sistema atual é baseado em monitoramento operacional e alertas amplos sem priorização por bairro.

## A Solução
Painel web para gestores da Defesa Civil com:
- **Predição de risco** por evento extremo de chuva por bairro (próximas 6h/12h/24h)
- **Score de resiliência** combinando histórico climático + vulnerabilidade social (IBGE)
- **Dossiê por bairro**: situação atual, projeção, vulnerabilidade e recomendação em linguagem natural
- **Simulação de cenário**: "E se cair 80mm em 6h?"

## Stack
- Backend: Python 3.11, Django 4.2, DRF, scikit-learn, pandas
- Frontend: React 18, Vite, Leaflet.js
- Dados: INMET (A401/Salvador, 2000–2021), IBGE BATER, Censo 2022, PNAD

## Como Rodar

### Backend
```bash
cd backend
pip install -r requirements.txt
python ml/train.py          # treinar o modelo (primeira vez)
python manage.py migrate
python manage.py seed_neighborhoods
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Acesse: http://localhost:3000

## Arquitetura
```
Dataset A401/INMET (2015-2021)
        ↓
  Feature Engineering (Pandas)
        ↓
  Random Forest Classifier → Risk Level (0-3)
        ↓
  + Score de Resiliência por Bairro (histórico + IBGE)
        ↓
  Template Alert Generator (Claude API-ready)
        ↓
  Django REST API → React + Leaflet
```

## Critério de Risco
| Precipitação/6h | Nível |
|---|---|
| < 10mm | Baixo |
| 10–30mm | Médio |
| 30–50mm | Alto |
| > 50mm | Crítico |

## Dados Utilizados
- Dataset oficial hackathon — estação A401/Salvador (INMET), 2000–2021
- IBGE BATER — áreas de risco cruzadas com dados socioeconômicos
- Censo 2022 + PNAD — indicadores por bairro (mockados com dados realistas)

## Equipe
Hackathon BaIA Week 2026 — UFBA
```

- [ ] Commit everything:
```bash
git init
git add .
git commit -m "feat: Sentinela Salvador — plataforma de inteligência climática"
```
