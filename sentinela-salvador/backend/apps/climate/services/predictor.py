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
