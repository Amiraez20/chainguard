"""Envoie une alerte critique « maintenant » pour déclencher la règle Kibana pendant la démo.

    python -m src.m4.demo_alert            (depuis la racine du dépôt)
"""
import random

from src.common.alert import Alert, FeatureContribution
from src.common.elastic import check, index_alert

if __name__ == "__main__":
    check()
    a = Alert(chain="ethereum", entity_type="contract",
              address="0x" + "".join(random.choices("0123456789abcdef", k=40)),
              score=0.97, label="suspicious", fraud_type="ponzi",
              top_features=[FeatureContribution(name="op_CALLDATALOAD", value=0.081, shap=1.42),
                            FeatureContribution(name="op_MULMOD", value=0.012, shap=0.66),
                            FeatureContribution(name="n_instr", value=3120, shap=0.31)],
              explanation_text="Contrat déployé à l'instant, profil d'opcodes typique d'un schéma de Ponzi.",
              model_version="demo")
    index_alert(a)
    print("alerte critique envoyée :", a.address)
