"""Construit data/processed/contracts_features.csv à partir de X-SPIDE (bytecode déployé).

Convention : address, label (1 = Ponzi), acc_* (compte), op_* (fréquences d'opcodes),
n_instr (nombre total d'instructions = somme des comptes d'opcodes).
"""
import re
import pandas as pd

SRC = "data/raw/xspide/dataset/DS_deployed_bytecode.csv"
OUT = "data/processed/contracts_features.csv"


def clean(name: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()


def main():
    d = pd.read_csv(SRC)
    cols = list(d.columns)
    acc_src, op_src = cols[1:24], cols[24:-1]  # 23 features de compte, 76 opcodes
    counts = d[op_src]
    n_instr = counts.sum(axis=1)
    out = pd.DataFrame({"address": d["address"].str.lower(), "label": d["target"].astype(int)})
    for c in acc_src:
        out[f"acc_{clean(c)}"] = d[c]
    for c in op_src:
        out[f"op_{c}"] = counts[c] / n_instr
    out["n_instr"] = n_instr.astype(int)
    out.to_csv(OUT, index=False)
    print(out.shape, out.label.value_counts().to_dict())


if __name__ == "__main__":
    main()
