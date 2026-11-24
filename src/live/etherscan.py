import requests

BASE = "https://api.etherscan.io/v2/api"  # API V2 (la V1 est désactivée)


def get_txlist(address: str, api_key: str, chainid: int = 1) -> list[dict]:
    """Transactions normales d'une adresse (10 000 max par appel)."""
    params = dict(chainid=chainid, module="account", action="txlist", address=address,
                  startblock=0, endblock=99999999, page=1, offset=10000, sort="asc",
                  apikey=api_key)
    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "1":  # "No transactions found" ou erreur
        return []
    return data["result"]
