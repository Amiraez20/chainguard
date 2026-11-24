"""Réentraîne la baseline de Chen (3 configurations) et sauvegarde le modèle « code seul »."""
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from src.common.metrics import evaluate

df = pd.read_csv("data/processed/contracts_features.csv")
y = df["label"]
acc = [c for c in df.columns if c.startswith("acc_")]
op = [c for c in df.columns if c.startswith("op_")]
for name, cols in {"account": acc, "code": op, "account+code": acc + op}.items():
    X_tr, X_te, y_tr, y_te = train_test_split(df[cols], y, test_size=0.2, stratify=y, random_state=42)
    rf = RandomForestClassifier(n_estimators=120, criterion="entropy", class_weight="balanced",
                                n_jobs=-1, random_state=42).fit(X_tr, y_tr)
    print(name, end=" ")
    evaluate(y_te, rf.predict(X_te), rf.predict_proba(X_te)[:, 1], f"m1_rf_{name}")
    if name == "code":
        joblib.dump({"model": rf, "features": cols}, "models/contract-rf-code-v1.joblib")
