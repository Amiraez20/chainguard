from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from web3 import Web3

from src.common.alert import Alert
from src.live.listener import score_contract

try:
    from src.models.wallet import score_wallet  # fourni par Aya (semaine 3)
except ImportError:
    def score_wallet(address: str) -> Alert:  # remplacée dès qu'Aya livre son module
        raise ValueError("score_wallet() bientôt disponible")

app = FastAPI(title="ChainGuard API", version="1.0")


class ScoreRequest(BaseModel):
    address: str
    entity_type: str  # "wallet" ou "contract"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/score", response_model=Alert)
def score(req: ScoreRequest):
    if not Web3.is_address(req.address):
        raise HTTPException(422, "adresse Ethereum invalide")
    addr = Web3.to_checksum_address(req.address)
    try:
        if req.entity_type == "contract":
            return score_contract(addr)
        if req.entity_type == "wallet":
            return score_wallet(addr)
    except ValueError as e:
        raise HTTPException(404, str(e))
    raise HTTPException(400, "entity_type doit valoir wallet ou contract")
