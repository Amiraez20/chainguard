"""Mesure de latence de l'écouteur (guide, section 3.3).

Usage : python -m src.live.latency [minutes]     (30 par défaut ; Ctrl+C arrête et sauvegarde)

Décomposition de la latence totale d'un contrat :
  attente    = détection du bloc par l'écouteur - horodatage du bloc
  rpc        = get_block + reçu + get_code (appels réseau vers le nœud, retries inclus)
  extraction = désassemblage + fréquences d'opcodes
  prediction = predict_proba du modèle
  total      = fin du score - horodatage du bloc
Les erreurs réseau sont réessayées puis comptées, jamais fatales : les mesures sont toujours
sauvegardées dans results/m1_latency.json et results/m1_latency_details.csv.
"""
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd
from web3 import Web3

from src.features.opcodes import opcode_features
from src.live import listener as L


def with_retry(fn, *args, tries: int = 4, pause: float = 2.0, stats: dict | None = None, **kwargs):
    """Appelle fn ; en cas d'erreur réseau, réessaie (pause croissante). Lève après `tries` échecs."""
    for attempt in range(1, tries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # timeouts, 429, coupures...
            if stats is not None:
                stats["retries"] = stats.get("retries", 0) + 1
            print(f"  (erreur réseau {type(e).__name__}, essai {attempt}/{tries})")
            if attempt == tries:
                raise
            time.sleep(pause * attempt)


def collect(minutes: float = 30, poll_seconds: int = 12, stats: dict | None = None) -> list[dict]:
    stats = stats if stats is not None else {}
    stats.setdefault("retries", 0)
    stats.setdefault("blocks_skipped", 0)
    stats.setdefault("contracts_skipped", 0)
    rows = []
    end = time.time() + minutes * 60
    last = with_retry(lambda: L.w3.eth.block_number)
    try:
        while time.time() < end:
            try:
                head = with_retry(lambda: L.w3.eth.block_number, stats=stats)
            except Exception:
                time.sleep(poll_seconds)
                continue
            detected = time.time()
            for n in range(last + 1, head + 1):
                try:
                    t0 = time.perf_counter()
                    block = with_retry(L.w3.eth.get_block, n, full_transactions=True, stats=stats)
                    t_block = time.perf_counter() - t0
                except Exception:
                    stats["blocks_skipped"] += 1
                    print(f"  bloc {n} ignoré (échecs répétés)")
                    continue
                wait = detected - block.timestamp
                for tx in block.transactions:
                    if tx["to"] is not None:
                        continue
                    try:
                        t0 = time.perf_counter()
                        rcpt = with_retry(L.w3.eth.get_transaction_receipt, tx["hash"], stats=stats)
                        addr = rcpt["contractAddress"]
                        code = with_retry(L.w3.eth.get_code, Web3.to_checksum_address(addr),
                                          stats=stats)
                        t_rpc = t_block + (time.perf_counter() - t0)
                    except Exception:
                        stats["contracts_skipped"] += 1
                        continue
                    if len(code) == 0:
                        continue
                    t0 = time.perf_counter()
                    feats = opcode_features(code, L.VOCAB)
                    x = pd.DataFrame([feats]).reindex(columns=L.FEATURES, fill_value=0)
                    t_ext = time.perf_counter() - t0
                    t0 = time.perf_counter()
                    p = float(L.MODEL.predict_proba(x)[0, 1])
                    t_pred = time.perf_counter() - t0
                    total = time.time() - block.timestamp
                    rows.append({"block": n, "address": addr, "score": p,
                                 "attente": wait, "rpc": t_rpc, "extraction": t_ext,
                                 "prediction": t_pred, "total": total})
                    print(f"[bloc {n}] {addr} score={p:.2f} total={total:.1f}s "
                          f"(attente {wait:.1f} | rpc {t_rpc:.2f} | extraction {t_ext:.3f} "
                          f"| prédiction {t_pred:.3f})  [{len(rows)} contrats]")
            last = max(last, head)
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("\nArrêt demandé : sauvegarde des mesures.")
    return rows


def summarize(rows: list[dict], stats: dict | None = None, out_dir: str = "results") -> dict:
    stats = stats or {}
    if not rows:
        print("Aucun contrat détecté : laissez tourner plus longtemps.")
        return {}
    df = pd.DataFrame(rows)
    res = {"n_contracts": len(df), "network_errors": stats}
    for col in ["attente", "rpc", "extraction", "prediction", "total"]:
        res[col] = {"median_s": float(np.percentile(df[col], 50)),
                    "p95_s": float(np.percentile(df[col], 95))}
    pathlib.Path(out_dir).mkdir(exist_ok=True)
    with open(f"{out_dir}/m1_latency.json", "w") as f:
        json.dump(res, f, indent=2)
    df.to_csv(f"{out_dir}/m1_latency_details.csv", index=False)
    print(f"\n{len(df)} contrats mesurés. Erreurs réseau : {stats}")
    for col in ["attente", "rpc", "extraction", "prediction", "total"]:
        print(f"{col:11s} médiane={res[col]['median_s']:.3f}s  p95={res[col]['p95_s']:.3f}s")
    return res


if __name__ == "__main__":
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 30
    print(f"Mesure pendant {minutes:g} minutes (Ctrl+C pour arrêter plus tôt)...")
    stats: dict = {}
    rows: list[dict] = []
    try:
        rows = collect(minutes, stats=stats)
    finally:
        summarize(rows, stats)
