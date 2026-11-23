import json
import pathlib
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)


def evaluate(y_true, y_pred, y_score, name, out_dir="results"):
    """Métriques de la classe fraude (=1), enregistrées dans results/<name>.json."""
    res = {
        "model": name,
        "recall": recall_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred),
        "pr_auc": average_precision_score(y_true, y_score),
        "roc_auc": roc_auc_score(y_true, y_score),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    pathlib.Path(out_dir).mkdir(exist_ok=True)
    with open(f"{out_dir}/{name}.json", "w") as f:
        json.dump(res, f, indent=2)
    print({k: round(v, 3) for k, v in res.items() if isinstance(v, float)})
    return res
