"""Redessine results/m4_drift.png à partir de results/m4_drift.csv (sans relancer m4_gnn).

    python -m src.m4.plot_drift        (depuis la racine du projet)
"""
import pathlib

import matplotlib.pyplot as plt
import pandas as pd

RESULTS = pathlib.Path(__file__).resolve().parents[2] / "results"
d = pd.read_csv(RESULTS / "m4_drift.csv")
K = [c for c in d.columns if c.startswith("rf_fenetre_")][0].split("_")[-1]
x = d.periode

fig, ax = plt.subplots(figsize=(9, 4.2))
small = d[d.n_illicites < 6].periode
for p in small:                                   # périodes non interprétables
    ax.axvspan(p - 0.5, p + 0.5, color="grey", alpha=0.10, lw=0)
if len(small):
    ax.text(small.mean(), 0.97, "< 6 illicites\n(non interprétable)", ha="center", va="top", fontsize=7, color="grey")

ax.plot(x, d.graphsage_fige, marker="^", color="#9c8f7a", ls=":", label="GraphSAGE figé")
ax.plot(x, d[f"rf_fenetre_{K}"], marker="s", color="#3d5a4c", label=f"RF réentraîné, fenêtre glissante ({K} périodes)")
ax.plot(x, d.rf_cumule, marker="D", color="#c9a227", ls="--", label="RF réentraîné, fenêtre cumulée")
ax.plot(x, d.rf_fige, marker="o", color="#b5523b", zorder=5, label="RF figé (entraîné sur 1–34)")

ax.axvline(42.5, ls="--", c="grey", lw=0.8)
ax.text(42.6, 0.62, "période 43 : fermeture d'un\nmarché du dark web\n(Weber et al., 2019)", fontsize=8, color="grey")

ax.set_xlabel("Période de test (nombre d'illicites)")
ax.set_xticks(x, [f"{p}\n({n})" for p, n in zip(x, d.n_illicites)], fontsize=8)
ax.set_ylabel("F1 classe illicite"); ax.set_ylim(0, 1.02)
ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig(RESULTS / "m4_drift.png", dpi=200, bbox_inches="tight")
print("écrit :", RESULTS / "m4_drift.png")
