"""Configure Kibana pour ChainGuard : data view, recherche sauvegardée, connecteur et règle critique.

    python elastic/setup_kibana.py                (Kibana sur http://localhost:5601)
    KIBANA_URL=http://autre:5601 python elastic/setup_kibana.py

Idempotent : on peut le relancer sans créer de doublons.
Le dashboard (visualisations Lens) se construit ensuite à la main : voir elastic/README_kibana.md.
"""
import json
import os
import sys
import time

import requests

KIBANA = os.environ.get("KIBANA_URL", "http://localhost:5601").rstrip("/")
H = {"kbn-xsrf": "true", "Content-Type": "application/json"}
INDEX = "chainguard-alerts"
DATA_VIEW_ID = "chainguard-alerts"
RULE_NAME = "ChainGuard — alerte critique (score >= 0.9)"
CONNECTOR_NAME = "ChainGuard server log"


def call(method, path, **kw):
    r = requests.request(method, KIBANA + path, headers=H, timeout=30, **kw)
    if not r.ok:
        sys.exit(f"ERREUR {r.status_code} sur {method} {path}\n{r.text[:800]}")
    return r.json() if r.text else {}


def wait_kibana(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            r = requests.get(KIBANA + "/api/status", timeout=5)
            if r.ok and r.json().get("status", {}).get("overall", {}).get("level") == "available":
                return
        except requests.RequestException:
            pass
        print("  Kibana pas encore prêt, nouvelle tentative dans 5 s…")
        time.sleep(5)
    sys.exit(f"Kibana injoignable sur {KIBANA} après {timeout} s.")


def data_view():
    call("POST", "/api/data_views/data_view", json={"override": True, "data_view": {
        "id": DATA_VIEW_ID, "name": "chainguard-alerts", "title": f"{INDEX}*", "timeFieldName": "timestamp"}})
    print("✓ data view chainguard-alerts*")


def saved_search():
    source = {"query": {"query": "", "language": "kuery"}, "filter": [],
              "indexRefName": "kibanaSavedObjectMeta.searchSourceJSON.index"}
    call("POST", "/api/saved_objects/search/chainguard-alerts-table?overwrite=true", json={
        "attributes": {"title": "ChainGuard — alertes",
                       "columns": ["address", "score", "severity", "fraud_type", "explanation_text"],
                       "sort": [["timestamp", "desc"]],
                       "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(source)}},
        "references": [{"name": "kibanaSavedObjectMeta.searchSourceJSON.index",
                        "type": "index-pattern", "id": DATA_VIEW_ID}]})
    print("✓ recherche sauvegardée « ChainGuard — alertes »")


def connector():
    for c in call("GET", "/api/actions/connectors"):
        if c["name"] == CONNECTOR_NAME:
            print("✓ connecteur server log (existant)")
            return c["id"]
    c = call("POST", "/api/actions/connector", json={"name": CONNECTOR_NAME, "connector_type_id": ".server-log"})
    print("✓ connecteur server log (créé)")
    return c["id"]


def rule(connector_id):
    found = call("GET", "/api/alerting/rules/_find", params={"search": "ChainGuard", "search_fields": "name"})
    for r in found.get("data", []):
        if r["name"] == RULE_NAME:
            print("✓ règle critique (existante) :", r["id"])
            return
    r = call("POST", "/api/alerting/rule", json={
        "name": RULE_NAME, "rule_type_id": ".es-query", "consumer": "stackAlerts",
        "schedule": {"interval": "1m"}, "tags": ["chainguard"],
        "params": {"searchType": "esQuery", "index": [INDEX], "timeField": "timestamp",
                   "esQuery": json.dumps({"query": {"range": {"score": {"gte": 0.9}}}}),
                   "size": 100, "threshold": [0], "thresholdComparator": ">",
                   "timeWindowSize": 5, "timeWindowUnit": "m",
                   "excludeHitsFromPreviousRun": True, "aggType": "count", "groupBy": "all"},
        "actions": [{"id": connector_id, "group": "query matched",
                     "params": {"level": "warn",
                                "message": "ChainGuard : {{context.hits.length}} alerte(s) critique(s) "
                                           "(score >= 0.9) sur les 5 dernières minutes. {{context.date}}"},
                     "frequency": {"summary": False, "notify_when": "onActiveAlert", "throttle": None}}]})
    print("✓ règle critique (créée) :", r["id"])


if __name__ == "__main__":
    print("Kibana :", KIBANA)
    wait_kibana()
    data_view()
    saved_search()
    rule(connector())
    print("\nTerminé. Kibana → Analytics → Discover → « ChainGuard — alertes » pour vérifier.")
    print("Tester la règle : python -m src.m4.demo_alert, puis Stack Management → Rules (1 minute).")
