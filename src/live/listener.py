import os
import time

import joblib
import pandas as pd
from dotenv import load_dotenv
from web3 import Web3

from src.common.alert import Alert
from src.features.opcodes import opcode_features

load_dotenv()

w3 = Web3(Web3.HTTPProvider(os.environ.get("ETH_RPC_URL", "http://localhost:8545"), request_kwargs={"timeout": 30}))
MODEL_PATH = "models/contract-rf-code-v1.joblib"  # remplacé par le modèle de Sara
MODEL_VERSION = "contract-rf-code-v1"
BUNDLE = joblib.load(MODEL_PATH)
MODEL, FEATURES = BUNDLE["model"], BUNDLE["features"]
VOCAB = [f.removeprefix("op_") for f in FEATURES if f.startswith("op_")]
THRESHOLD = 0.5


def score_bytecode(code) -> float:
    """Probabilité Ponzi à partir du bytecode (sans accès réseau : testable hors ligne)."""
    x = pd.DataFrame([opcode_features(code, VOCAB)]).reindex(columns=FEATURES, fill_value=0)
    return float(MODEL.predict_proba(x)[0, 1])


def score_contract(address: str) -> Alert:
    code = w3.eth.get_code(Web3.to_checksum_address(address))
    if len(code) == 0:
        raise ValueError("pas de bytecode : adresse non contrat ou contrat détruit")
    p = score_bytecode(code)
    return Alert(chain="ethereum", entity_type="contract", address=address, score=p,
                 label="suspicious" if p >= THRESHOLD else "normal",
                 fraud_type="ponzi" if p >= THRESHOLD else "unknown",
                 model_version=MODEL_VERSION)


def watch(poll_seconds: int = 12):
    """Parcourt chaque nouveau bloc et score les contrats créés (tx.to == None)."""
    last = w3.eth.block_number
    while True:
        head = w3.eth.block_number
        for n in range(last + 1, head + 1):
            block = w3.eth.get_block(n, full_transactions=True)
            for tx in block.transactions:
                if tx["to"] is None:
                    rcpt = w3.eth.get_transaction_receipt(tx["hash"])
                    try:
                        alert = score_contract(rcpt["contractAddress"])
                    except ValueError:
                        continue  # contrat déjà détruit ou création échouée
                    latency = time.time() - block.timestamp
                    print(f"[bloc {n}] {alert.address} score={alert.score:.2f} "
                          f"latence={latency:.1f}s")
                    yield alert
        last = head
        time.sleep(poll_seconds)


if __name__ == "__main__":
    for alert in watch():
        if alert.label == "suspicious":
            print("ALERTE", alert.model_dump_json())
