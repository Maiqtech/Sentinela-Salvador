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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
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
