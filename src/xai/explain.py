import shap
from src.common.alert import FeatureContribution


def explain_one(pipe, x, features, k=5) -> list[FeatureContribution]:
    """Top-k contributions SHAP pour UNE ligne (DataFrame d'une ligne, non imputée)."""
    xi = pipe.named_steps["impute"].transform(x[features])
    sv = shap.TreeExplainer(pipe.named_steps["clf"])(xi).values[0]
    order = abs(sv).argsort()[::-1][:k]
    return [FeatureContribution(name=features[j], value=float(xi[0, j]), shap=float(sv[j]))
            for j in order]