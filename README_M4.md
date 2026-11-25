# ChainGuard · Module M4 (Laila) — graphe Bitcoin, dérive, dashboard SOC

Branche : `m4-graph-soc`

## Fichiers
```
src/common/alert.py           schéma d'alerte commun (identique pour les 4 membres)
src/common/metrics.py         evaluate() commun
src/common/elastic.py         index chainguard-alerts : setup_index, index_alert, bulk_index   → utilisé par Amira
src/m4/elliptic.py            chargement Elliptic + split temporel 1–34 / 35–49
src/m4/seed.py                modèle btc-xgb-v1 + alertes Bitcoin avec SHAP
src/m4/demo_alert.py          envoie une alerte critique « maintenant » (démo de la règle)
notebooks/m4_baselines.ipynb  S1 : 6 baselines + 2 contre-expériences de fuite
notebooks/m4_gnn.ipynb        S2 : GCN, GraphSAGE, hybride, dérive temporelle
notebooks/m4_seed_kibana.ipynb S3 : remplir Kibana
elastic/docker-compose.m4.yml Elasticsearch + Kibana 8.15 pour tester seule
elastic/setup_kibana.py       data view + recherche sauvegardée + règle critique
elastic/README_kibana.md      construction du dashboard, export ndjson
dashboard/app.py              plan B Streamlit (alertes depuis ES + appel à l'API)
requirements/m4.txt
```

## Ordre d'exécution
```bash
# 0. Environnement (une fois)
python -m venv .venv && source .venv/bin/activate      # Windows : .venv\Scripts\Activate.ps1
pip install -r requirements/base.txt
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements/m4.txt

# 1. Données (une fois)
kaggle datasets download -d ellipticco/elliptic-data-set -p data/raw/elliptic --unzip

# 2. Semaine 1 puis 2 (dans cet ordre : m4_gnn lit les prédictions de m4_baselines)
jupyter lab      # exécuter notebooks/m4_baselines.ipynb, puis notebooks/m4_gnn.ipynb

# 3. Semaine 3
docker compose -f elastic/docker-compose.m4.yml up -d   # attendre 1–2 min
# exécuter notebooks/m4_seed_kibana.ipynb
python elastic/setup_kibana.py
# construire le dashboard : elastic/README_kibana.md
python -m src.m4.demo_alert                              # vérifier que la règle se déclenche
streamlit run dashboard/app.py                           # plan B
```

## Résultats produits (dossier results/)
| Fichier | Contenu |
|---|---|
| `m4_*.json` | métriques de chaque modèle (format commun) |
| `m4_baselines_summary.csv` | tableau des 6 baselines + 3 variantes |
| `m4_leak_comparison.png` | **figure-clé** : bon protocole / split aléatoire / rééquilibrage avant split |
| `m4_illicit_share.png` | part d'illicites par période |
| `m4_models_summary.csv`, `m4_models_comparison.png` | tabulaire vs GNN vs hybride |
| `m4_drift.csv`, `m4_drift.png` | **courbe de dérive** avec la période 43 |

## Temps de calcul attendus (CPU portable)
m4_baselines : 5–15 min (ADASYN + TomekLinks est l'étape la plus lente) · m4_gnn : 10–25 min (dont ≈ 30 réentraînements RF pour la dérive) · m4_seed_kibana : < 1 min.

## Pour l'équipe
- **Amira** : `from src.common.elastic import index_alert` dans le listener et l'API ; `models/btc-xgb-v1.joblib` (dict `model`, `features`) si l'API doit scorer des transactions Bitcoin. Ajouter la variable `XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY` au service Kibana du docker-compose commun, sinon la règle critique ne peut pas être créée.
- **Aya** : le champ `explanation_text` des alertes Bitcoin utilise un gabarit simple (`src/m4/seed.py::explanation`) ; à remplacer par `to_text()` quand il est prêt.
