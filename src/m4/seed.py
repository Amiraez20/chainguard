"""Alertes Bitcoin (Elliptic, périodes de test) pour remplir Kibana avant la chaîne en direct."""
import pathlib
from datetime import datetime, timedelta, timezone

import joblib
import numpy as np
import shap
from xgboost import XGBClassifier

from src.common.alert import Alert, FeatureContribution

MODEL_VERSION = "btc-xgb-v1"
MODEL_PATH = pathlib.Path(__file__).resolve().parents[2] / "models" / f"{MODEL_VERSION}.joblib"


def train_btc_model(E):
    """XGBoost « xgb_none » de m4_baselines, réentraîné et sauvegardé dans models/."""
    clf = XGBClassifier(n_estimators=400, learning_rate=0.05, max_depth=6, eval_metric="logloss",
                        n_jobs=-1, random_state=42).fit(E.train[E.feat_cols], E.train.y)
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": clf, "features": E.feat_cols}, MODEL_PATH)
    return clf


def explanation(score, contribs):
    parts = [f"{c.name} = {c.value:.2f} ({'↑' if c.shap > 0 else '↓'} risque)" for c in contribs]
    return f"Transaction Bitcoin au score {score:.2f}. Facteurs principaux : " + " ; ".join(parts) + "."


def build_btc_alerts(E, clf, min_score=0.3, days=7, top_k=3):
    """Une alerte par transaction de test au score >= min_score.

    Les horodatages répartissent les périodes 35..49 sur les `days` derniers jours, dans l'ordre :
    la chronologie Kibana montre donc la même dérive que la courbe du notebook.
    """
    test = E.test
    X = test[E.feat_cols]
    p = clf.predict_proba(X)[:, 1]
    keep = np.where(p >= min_score)[0]
    sv = shap.TreeExplainer(clf).shap_values(X.iloc[keep])

    now = datetime.now(timezone.utc)
    t0, span = now - timedelta(days=days), timedelta(days=days) / 15
    rank = test.groupby("time_step").cumcount().values
    size = test.groupby("time_step").txId.transform("size").values

    alerts = []
    for j, i in enumerate(keep):
        order = np.argsort(-np.abs(sv[j]))[:top_k]
        contribs = [FeatureContribution(name=E.feat_cols[k], value=float(X.iat[i, k]), shap=float(sv[j][k]))
                    for k in order]
        score = float(p[i])
        ts = t0 + span * (test.time_step.iat[i] - 35 + rank[i] / size[i])
        alerts.append(Alert(timestamp=ts, chain="bitcoin", entity_type="btc_tx",
                            address=str(test.txId.iat[i]), score=round(score, 4),
                            label="suspicious" if score >= 0.5 else "normal",
                            fraud_type="illicit" if score >= 0.5 else "unknown",
                            top_features=contribs, explanation_text=explanation(score, contribs),
                            model_version=MODEL_VERSION))
    return alerts
