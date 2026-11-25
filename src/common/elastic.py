"""Index Elasticsearch des alertes ChainGuard (membre 4).

Utilisé par : le listener et l'API (Amira), le notebook de pré-remplissage, le dashboard.
"""
import os

from elasticsearch import Elasticsearch, helpers

try:                                   # .env facultatif
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

INDEX = "chainguard-alerts"
ES_URL = os.environ.get("ES_URL", "http://localhost:9200")
es = Elasticsearch(ES_URL, request_timeout=30)

MAPPING = {"properties": {
    "timestamp": {"type": "date"},
    "chain": {"type": "keyword"},
    "entity_type": {"type": "keyword"},
    "address": {"type": "keyword"},
    "score": {"type": "float"},
    "severity": {"type": "keyword"},
    "label": {"type": "keyword"},
    "fraud_type": {"type": "keyword"},
    "top_feature": {"type": "keyword"},
    "top_features": {"properties": {               # objet simple : Lens ne lit pas « nested »
        "name": {"type": "keyword"}, "value": {"type": "float"}, "shap": {"type": "float"}}},
    "explanation_text": {"type": "text"},
    "model_version": {"type": "keyword"},
}}


def check() -> None:
    """Lève une erreur lisible si Elasticsearch ne répond pas."""
    if not es.ping():
        raise ConnectionError(f"Elasticsearch injoignable sur {ES_URL} : lancer "
                              "`docker compose up -d elasticsearch kibana` et attendre 1 minute.")


def setup_index(reset: bool = False) -> None:
    check()
    if reset and es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
    if not es.indices.exists(index=INDEX):
        es.indices.create(index=INDEX, mappings=MAPPING)


def severity(score: float) -> str:
    return ("critical" if score >= 0.9 else "high" if score >= 0.7
            else "medium" if score >= 0.5 else "low")


def to_doc(alert) -> dict:
    doc = alert.model_dump(mode="json")
    doc["severity"] = severity(doc["score"])
    doc["top_feature"] = doc["top_features"][0]["name"] if doc["top_features"] else None
    return doc


def index_alert(alert) -> None:
    """Une alerte (listener temps réel, API)."""
    es.index(index=INDEX, document=to_doc(alert))


def bulk_index(alerts) -> int:
    """Plusieurs alertes d'un coup ; renvoie le nombre indexé."""
    ok, _ = helpers.bulk(es, ({"_index": INDEX, "_source": to_doc(a)} for a in alerts), refresh=True)
    return ok


def count() -> int:
    return es.count(index=INDEX)["count"]
