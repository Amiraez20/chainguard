"""Démo : rejoue N Ponzi connus et les envoie dans Elasticsearch (Kibana)."""
import sys
import time

import pandas as pd

from src.live.listener import publish, score_contract

n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ponzi = pd.read_csv("data/processed/test_ponzi_addresses.csv")["address"]
sent = 0
for addr in ponzi:
    if sent >= n:
        break
    try:
        alert = score_contract(addr)
    except ValueError:
        continue  # contrat détruit
    if alert.label != "suspicious":
        continue
    ok = publish(alert)
    print(f"{alert.address} score={alert.score:.2f} indexé={ok}")
    sent += 1
    time.sleep(1)
