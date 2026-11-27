"""Crée le dashboard « ChainGuard — SOC » dans Kibana 8.15 puis l'exporte dans elastic/dashboard.ndjson.

    python elastic/create_dashboard.py          (après setup_kibana.py : la data view doit exister)

Idempotent (overwrite). Affiche l'erreur exacte de chaque objet refusé.
"""
import json
import os
import pathlib
import sys

import requests

KIBANA = os.environ.get("KIBANA_URL", "http://localhost:5601").rstrip("/")
DV = "chainguard-alerts"
SEARCH_ID = "chainguard-alerts-table"
DASH_ID = "chainguard-soc"
OUT = pathlib.Path(__file__).resolve().parent / "dashboard.ndjson"
MIG = {"coreMigrationVersion": "8.8.0", "typeMigrationVersion": "8.9.0"}


def terms(field, label, size, order_by="y"):
    return {"label": label, "customLabel": True, "dataType": "string", "operationType": "terms",
            "sourceField": field, "isBucketed": True, "scale": "ordinal",
            "params": {"size": size, "orderBy": {"type": "column", "columnId": order_by},
                       "orderDirection": "desc", "otherBucket": False, "missingBucket": False}}


COUNT = {"label": "Alertes", "customLabel": True, "dataType": "number", "operationType": "count",
         "sourceField": "___records___", "isBucketed": False, "scale": "ratio", "params": {}}


def lens(obj_id, title, x_col, series, split_col=None):
    cols = {"x": x_col, "y": COUNT}
    order = ["x", "y"]
    layer = {"layerId": "l1", "layerType": "data", "seriesType": series, "xAccessor": "x", "accessors": ["y"]}
    if split_col:
        cols["s"] = split_col
        order = ["x", "s", "y"]
        layer["splitAccessor"] = "s"
    return {
        "type": "lens", "id": obj_id, **MIG,
        "attributes": {
            "title": title, "description": "", "visualizationType": "lnsXY",
            "state": {
                "datasourceStates": {"formBased": {"layers": {"l1": {
                    "columns": cols, "columnOrder": order, "incompleteColumns": {}}}}},
                "visualization": {"preferredSeriesType": series, "layers": [layer],
                                  "legend": {"isVisible": bool(split_col), "position": "right"},
                                  "valueLabels": "hide", "fittingFunction": "None"},
                "query": {"query": "", "language": "kuery"}, "filters": [],
                "internalReferences": [], "adHocDataViews": {}},
        },
        "references": [{"type": "index-pattern", "id": DV, "name": "indexpattern-datasource-layer-l1"}],
    }


def objects():
    hist = {"label": "Score", "customLabel": True, "dataType": "number", "operationType": "range",
            "sourceField": "score", "isBucketed": True, "scale": "interval",
            "params": {"type": "histogram", "maxBars": 10, "includeEmptyRows": True,
                       "ranges": [{"from": 0, "to": 1, "label": ""}]}}
    date = {"label": "Temps", "customLabel": True, "dataType": "date", "operationType": "date_histogram",
            "sourceField": "timestamp", "isBucketed": True, "scale": "interval",
            "params": {"interval": "auto", "includeEmptyRows": True, "dropPartials": False}}
    viz = [
        lens("cg-lens-fraud-type", "Alertes par type de fraude",
             terms("fraud_type", "Type de fraude", 10), "bar"),
        lens("cg-lens-score", "Distribution des scores", hist, "bar"),
        lens("cg-lens-top-feature", "Top 10 des features explicatives (SHAP)",
             terms("top_feature", "Feature", 10), "bar_horizontal"),
        lens("cg-lens-timeline", "Alertes dans le temps, par sévérité", date, "bar_stacked",
             split_col=terms("severity", "Sévérité", 4, order_by="y")),
    ]

    grid = [
        ("p1", "lens", "cg-lens-fraud-type", 0, 0, 16, 13),
        ("p2", "lens", "cg-lens-score", 16, 0, 16, 13),
        ("p3", "lens", "cg-lens-top-feature", 32, 0, 16, 13),
        ("p4", "lens", "cg-lens-timeline", 0, 13, 48, 14),
        ("p5", "search", SEARCH_ID, 0, 27, 48, 18),
    ]
    panels, refs = [], []
    for pid, typ, oid, x, y, w, h in grid:
        panels.append({"type": typ, "panelIndex": pid, "panelRefName": f"panel_{pid}",
                       "gridData": {"x": x, "y": y, "w": w, "h": h, "i": pid},
                       "embeddableConfig": {"enhancements": {}}})
        refs.append({"name": f"{pid}:panel_{pid}", "type": typ, "id": oid})

    controls = {}
    for i, (cid, field, title) in enumerate([("c1", "entity_type", "Type d'entité"),
                                             ("c2", "severity", "Sévérité")]):
        controls[cid] = {"order": i, "width": "medium", "grow": True, "type": "optionsListControl",
                         "explicitInput": {"id": cid, "fieldName": field, "title": title,
                                           "searchTechnique": "prefix", "selectedOptions": []}}
        refs.append({"name": f"controlGroup_{cid}:optionsListDataView", "type": "index-pattern", "id": DV})

    dash = {
        "type": "dashboard", "id": DASH_ID, **MIG,
        "attributes": {
            "title": "ChainGuard — SOC",
            "description": "Alertes ChainGuard : types de fraude, scores, features SHAP, chronologie, détail.",
            "panelsJSON": json.dumps(panels),
            "optionsJSON": json.dumps({"useMargins": True, "syncColors": False, "syncCursor": True,
                                       "syncTooltips": False, "hidePanelTitles": False}),
            "timeRestore": True, "timeFrom": "now-7d", "timeTo": "now",
            "refreshInterval": {"pause": True, "value": 60000},
            "controlGroupInput": {
                "controlStyle": "oneLine", "chainingSystem": "HIERARCHICAL",
                "panelsJSON": json.dumps(controls),
                "ignoreParentSettingsJSON": json.dumps({"ignoreFilters": False, "ignoreQuery": False,
                                                        "ignoreTimerange": False, "ignoreValidations": False})},
            "kibanaSavedObjectMeta": {"searchSourceJSON": json.dumps(
                {"query": {"query": "", "language": "kuery"}, "filter": []})},
        },
        "references": refs,
    }
    return viz + [dash]


def main():
    payload = "\n".join(json.dumps(o, ensure_ascii=False) for o in objects()) + "\n"
    r = requests.post(f"{KIBANA}/api/saved_objects/_import?overwrite=true",
                      headers={"kbn-xsrf": "true"},
                      files={"file": ("chainguard.ndjson", payload.encode("utf-8"), "application/ndjson")},
                      timeout=60)
    if not r.ok:
        sys.exit(f"ERREUR HTTP {r.status_code}\n{r.text[:1500]}")
    res = r.json()
    for s in res.get("successResults", []):
        print("OK", s["type"], s["id"])
    for e in res.get("errors", []):
        print("ECHEC", e.get("type"), e.get("id"), json.dumps(e.get("error"), ensure_ascii=False))
    if not res.get("success"):
        sys.exit("Import incomplet : copier les lignes ECHEC ci-dessus.")

    ex = requests.post(f"{KIBANA}/api/saved_objects/_export", headers={"kbn-xsrf": "true"},
                       json={"objects": [{"type": "dashboard", "id": DASH_ID}],
                             "includeReferencesDeep": True, "excludeExportDetails": False}, timeout=60)
    if not ex.ok:
        sys.exit(f"Dashboard cree, mais export refuse ({ex.status_code}) : {ex.text[:500]}")
    OUT.write_bytes(ex.content)
    print(f"\nTermine : {KIBANA}/app/dashboards#/view/{DASH_ID}")
    print("Export :", OUT)


if __name__ == "__main__":
    main()
