"""Réentraîne wallet-xgb-live-v1 (16 features calculables en direct).
Usage, depuis la racine du dépôt : python -m src.models.train_wallet_live
"""
import pathlib

import joblib
import pandas as pd
import sklearn
import xgboost
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.common.metrics import evaluate

LIVE_COLS = [
    "Avg min between sent tnx", "Avg min between received tnx",
    "Time Diff between first and last (Mins)", "Sent tnx", "Received Tnx",
    "Unique Received From Addresses", "Unique Sent To Addresses",
    "min value received", "max value received", "avg val received",
    "min val sent", "max val sent", "avg val sent",
    "total Ether sent", "total ether received", "total ether balance",
]


def main():
    df = pd.read_csv("data/raw/wallets/transaction_dataset.csv")
    df.columns = df.columns.str.strip()
    df = df.drop(columns=["Unnamed: 0", "Index"], errors="ignore").drop_duplicates(subset="Address")
    y = df["FLAG"]
    X = df.drop(columns=["FLAG", "Address"]).select_dtypes("number")
    X = X.loc[:, X.nunique(dropna=False) > 1]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

    pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("smote", SMOTE(random_state=42)),
        ("clf", XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.8,
                              colsample_bytree=0.8, eval_metric="logloss", random_state=42)),
    ]).fit(X_tr[LIVE_COLS], y_tr)

    p = pipe.predict_proba(X_te[LIVE_COLS])[:, 1]
    evaluate(y_te, (p >= 0.5).astype(int), p, "m3_xgb_live")

    pathlib.Path("models").mkdir(exist_ok=True)
    joblib.dump({"pipeline": pipe, "features": LIVE_COLS,
                 "versions": {"scikit-learn": sklearn.__version__, "xgboost": xgboost.__version__}},
                "models/wallet-xgb-live-v1.joblib")
    print("modèle sauvegardé avec scikit-learn", sklearn.__version__)


if __name__ == "__main__":
    main()