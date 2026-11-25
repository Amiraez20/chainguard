"""Chargement d'Elliptic et split temporel, partagés par les notebooks du membre 4."""
import pathlib
from dataclasses import dataclass

import pandas as pd

DEFAULT_BASE = pathlib.Path(__file__).resolve().parents[2] / "data/raw/elliptic/elliptic_bitcoin_dataset"
TRAIN_LAST, TEST_FIRST = 34, 35     # coupure de Weber et al. (2019)


@dataclass
class Elliptic:
    df: pd.DataFrame          # toutes les transactions (y = -1 si non étiquetée)
    edges: pd.DataFrame       # colonnes txId1, txId2
    feat_cols: list
    local_cols: list
    lab: pd.DataFrame         # transactions étiquetées
    train: pd.DataFrame       # étiquetées, périodes 1..34
    test: pd.DataFrame        # étiquetées, périodes 35..49


def load_elliptic(base=DEFAULT_BASE) -> Elliptic:
    base = pathlib.Path(base)
    feat = pd.read_csv(base / "elliptic_txs_features.csv", header=None)
    cls = pd.read_csv(base / "elliptic_txs_classes.csv")
    edges = pd.read_csv(base / "elliptic_txs_edgelist.csv")
    edges.columns = ["txId1", "txId2"]          # noms normalisés quelle que soit la version du CSV

    feat.columns = (["txId", "time_step"] + [f"local_{i}" for i in range(93)]
                    + [f"agg_{i}" for i in range(72)])
    df = feat.merge(cls, on="txId", how="left")
    y = df["class"].astype(str).map({"1": 1, "2": 0, "unknown": -1})
    if y.isna().any():
        raise ValueError("valeurs de classe inattendues dans elliptic_txs_classes.csv")
    df = pd.concat([df, y.astype(int).rename("y")], axis=1)

    feat_cols = [c for c in df.columns if c.startswith(("local_", "agg_"))]
    local_cols = [c for c in feat_cols if c.startswith("local_")]
    lab = df[df.y != -1]
    return Elliptic(df, edges, feat_cols, local_cols, lab,
                    lab[lab.time_step <= TRAIN_LAST], lab[lab.time_step >= TEST_FIRST])
