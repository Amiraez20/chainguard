# Kibana — construire le dashboard ChainGuard (≈ 15 min)

Prérequis : Elasticsearch et Kibana démarrés, `notebooks/m4_seed_kibana.ipynb` exécuté, puis :

    python elastic/setup_kibana.py

Ce script crée la data view `chainguard-alerts*`, la recherche sauvegardée « ChainGuard — alertes » et la règle critique. Il reste le dashboard, à faire à la main.

## 1. Dashboard
Kibana → **Analytics → Dashboards → Create dashboard**. Plage de temps en haut à droite : **Last 7 days**.
Pour chaque panneau : **Create visualization** (Lens), data view `chainguard-alerts`.

| # | Panneau | Type Lens | Configuration |
|---|---|---|---|
| a | Alertes par type de fraude | Bar vertical | Axe horizontal : Top values de `fraud_type` ; vertical : Count |
| b | Distribution des scores | Bar vertical | Horizontal : Intervals de `score` (intervalle 0.1) ; vertical : Count |
| c | Top 10 des features | Bar horizontal | Vertical : Top 10 values de `top_feature` ; horizontal : Count |
| d | Alertes dans le temps | Bar vertical stacked | Horizontal : `timestamp` (date histogram) ; vertical : Count ; Breakdown : `severity` |
| e | Tableau des alertes | — | **Add from library** → « ChainGuard — alertes » |
| f | (option) Compteurs | Metric | Count, un par sévérité via un filtre `severity : "critical"` etc. |

**Contrôles** : Add panel → **Controls** → Options list sur `entity_type`, puis sur `severity`.

Couleurs conseillées pour `severity` (panneau d) : critical rouge brique, high orange, medium jaune, low gris. Éviter la palette par défaut.

Enregistrer le dashboard sous le nom **ChainGuard — SOC**.

## 2. Règle critique (si le script a échoué)
**Stack Management → Rules → Create rule → Elasticsearch query**
- Index : `chainguard-alerts`, champ de temps `timestamp`
- Requête (KQL) : `score >= 0.9`
- Condition : « is above 0 » sur les 5 dernières minutes ; vérification chaque minute
- Action : **Server log**, niveau warn

Tester : `python -m src.m4.demo_alert` envoie une alerte critique « maintenant » ; la règle passe à *Active* en ≤ 1 minute (Stack Management → Rules → la règle → onglet Alerts). C'est aussi le geste de démo.

Les alertes pré-remplies ont des dates passées : elles alimentent le dashboard mais ne déclenchent pas la règle (fenêtre de 5 minutes). Seules les alertes en direct la déclenchent, ce qui est le comportement voulu.

## 3. Exporter pour l'équipe et la machine de démo
**Stack Management → Saved Objects** → cocher le dashboard « ChainGuard — SOC » → **Export** (Include related objects) → enregistrer sous `elastic/dashboard.ndjson`, puis commit.

Réimporter sur une autre machine :

    curl -X POST "http://localhost:5601/api/saved_objects/_import?overwrite=true" \
         -H "kbn-xsrf: true" --form file=@elastic/dashboard.ndjson

La règle n'est pas exportée avec le dashboard : relancer `python elastic/setup_kibana.py` sur la machine de démo.

## Dépannage
| Symptôme | Solution |
|---|---|
| Aucune donnée | Élargir la plage de temps à 7 ou 30 jours |
| Lens n'affiche pas `top_features.name` | Utiliser `top_feature` (keyword, première feature) |
| Rules : « encryption key » manquante | Utiliser `elastic/docker-compose.m4.yml` (la clé y est définie) ou l'ajouter au compose commun |
| `max virtual memory areas too low` | `sudo sysctl -w vm.max_map_count=262144` (WSL2 : dans la distribution Linux) |
| BadRequestError à la création de l'index | Index existant avec un autre mapping : `setup_index(reset=True)` |
