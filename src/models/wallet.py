import os
from functools import lru_cache

import joblib
import pandas as pd

from src.common.alert import Alert
from src.features.wallets import features_from_txlist
from src.live.etherscan import get_txlist
from src.xai.explain import explain_one
from src.xai.text import to_text

THRESHOLD = 0.5


@lru_cache(maxsize=1)
def _bundle():
    b = joblib.load("models/wallet-xgb-live-v1.joblib")
    return b["pipeline"], b["features"]


def score_wallet(address: str) -> Alert:
    pipe, features = _bundle()
    txs = get_txlist(address, os.environ["ETHERSCAN_API_KEY"])
    if not txs:
        raise ValueError("aucune transaction trouvée pour cette adresse")
    feats = features_from_txlist(txs, address)
    if not feats:
        raise ValueError("aucune transaction valide pour cette adresse")
    x = pd.DataFrame([feats]).reindex(columns=features)
    p = float(pipe.predict_proba(x)[0, 1])
    contribs = explain_one(pipe, x, features)
    suspicious = p >= THRESHOLD
    return Alert(chain="ethereum", entity_type="wallet", address=address, score=p,
                 label="suspicious" if suspicious else "normal",
                 fraud_type="scam" if suspicious else "unknown",
                 top_features=contribs,
                 explanation_text=to_text(contribs) if suspicious else "",
                 model_version="wallet-xgb-live-v1")