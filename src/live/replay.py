import pandas as pd

from src.live.listener import score_contract

ponzi = pd.read_csv("data/processed/test_ponzi_addresses.csv")["address"]
hits, errors = 0, 0
for addr in ponzi:
    try:
        hits += score_contract(addr).label == "suspicious"
    except ValueError:
        errors += 1  # contrat détruit (selfdestruct)
print(f"Recall en conditions réelles : {hits}/{len(ponzi) - errors} "
      f"({errors} contrats introuvables)")
