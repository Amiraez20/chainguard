"""ChainGuard — tableau de bord de secours (plan B si Kibana pose problème).

    streamlit run dashboard/app.py        (depuis la racine du dépôt) → http://localhost:8501

Onglet « Alertes » : lit l'index Elasticsearch chainguard-alerts (mêmes vues que le dashboard Kibana).
Onglet « Analyser une adresse » : appelle l'API d'Amira (POST /score sur API_URL).
"""
import os
import sys
import pathlib

import pandas as pd
import requests
import streamlit as st

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
from src.common.elastic import ES_URL, INDEX, es  # noqa: E402

API_URL = os.environ.get("API_URL", "http://localhost:8000")
SEV_ORDER = ["critical", "high", "medium", "low"]

st.set_page_config(page_title="ChainGuard", layout="wide")
st.title("ChainGuard — analyse de risque blockchain")
tab_alerts, tab_score = st.tabs(["Alertes", "Analyser une adresse"])


@st.cache_data(ttl=30)
def load_alerts(size=2000):
    res = es.search(index=INDEX, size=size, sort=[{"timestamp": "desc"}])
    rows = [h["_source"] for h in res["hits"]["hits"]]
    df = pd.DataFrame(rows)
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df


with tab_alerts:
    try:
        df = load_alerts()
    except Exception as e:                          # ES arrêté, index absent…
        st.warning(f"Impossible de lire l'index `{INDEX}` sur {ES_URL} : {type(e).__name__}. "
                   "Lancer Elasticsearch puis le notebook m4_seed_kibana.")
        df = pd.DataFrame()

    if not df.empty:
        c1, c2 = st.columns(2)
        ents = c1.multiselect("Type d'entité", sorted(df.entity_type.unique()), default=sorted(df.entity_type.unique()))
        sevs = c2.multiselect("Sévérité", SEV_ORDER, default=SEV_ORDER)
        f = df[df.entity_type.isin(ents) & df.severity.isin(sevs)]

        cols = st.columns(5)
        cols[0].metric("Alertes", len(f))
        for col, s in zip(cols[1:], SEV_ORDER):
            col.metric(s, int((f.severity == s).sum()))

        a, b = st.columns(2)
        a.subheader("Par type de fraude")
        a.bar_chart(f.fraud_type.value_counts())
        b.subheader("Distribution des scores")
        b.bar_chart(pd.cut(f.score, bins=[i / 10 for i in range(11)]).value_counts().sort_index()
                    .rename(lambda iv: f"{iv.left:.1f}–{iv.right:.1f}"))

        a, b = st.columns(2)
        a.subheader("Top 10 des features explicatives")
        a.bar_chart(f.top_feature.value_counts().head(10))
        b.subheader("Alertes dans le temps")
        b.bar_chart(f.set_index("timestamp").groupby([pd.Grouper(freq="6h"), "severity"]).size()
                    .unstack(fill_value=0).reindex(columns=[s for s in SEV_ORDER if s in sevs], fill_value=0))

        st.subheader("Dernières alertes")
        st.dataframe(f[["timestamp", "entity_type", "address", "score", "severity", "fraud_type",
                        "explanation_text"]].head(200), hide_index=True)
    elif "df" in locals():
        st.info("Aucune alerte pour l'instant.")

with tab_score:
    addr = st.text_input("Adresse Ethereum")
    kind = st.radio("Type", ["wallet", "contract"], horizontal=True)
    if st.button("Analyser") and addr:
        try:
            r = requests.post(f"{API_URL}/score", json={"address": addr, "entity_type": kind}, timeout=60)
        except requests.RequestException as e:
            st.error(f"API injoignable sur {API_URL} ({type(e).__name__}). L'API d'Amira doit tourner.")
        else:
            if r.ok:
                a = r.json()
                st.metric("Score de risque", f"{a['score']:.2f}", a["label"])
                st.write(a["explanation_text"])
                if a["top_features"]:
                    st.bar_chart(pd.DataFrame(a["top_features"]).set_index("name")["shap"])
            else:
                st.error(r.text)
