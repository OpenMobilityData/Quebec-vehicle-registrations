"""Yearly growth in automobiles and light trucks, three periods, Montréal beside four other large cities and the
rest of Québec. 2023-2024 counts are inferred. Reads type_by_municipality.csv; writes derived/tables/growth_by_city.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/growth-by-city/growth_by_city.py"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

t = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str}); a = t[t.vtype == "AU"]
G = {"Montréal": "66023", "Laval": "65005", "Longueuil": "58227", "Gatineau": "81017", "Québec (city)": "23027"}
w = pd.DataFrame({k: a[a.muni_code == v].groupby("year").n.sum() for k, v in G.items()})
allq = a.groupby("year").n.sum()
w["Rest of Québec"] = allq - w[list(G)].sum(axis=1); w["All of Québec"] = allq
P = [(2011, 2016), (2016, 2021), (2021, 2024)]
r = pd.DataFrame({f"{a_}-{b_}": 100 * ((w.loc[b_] / w.loc[a_]) ** (1 / (b_ - a_)) - 1) for a_, b_ in P}).round(2)
out = r.copy(); out.columns = [f"pct_per_year_{c.replace('-', '_')}" for c in r.columns]
for y in (2011, 2016, 2021, 2024):
    out[f"vehicles_{y}"] = w.loc[y].round(0).astype(int)
out.index.name = "place"; out.to_csv(paths.TABLES / "growth_by_city.csv")
FR = {"Québec (city)": "Québec (ville)", "Rest of Québec": "Reste du Québec", "All of Québec": "Ensemble du Québec"}
COL = ["#9ec5f4", "#2a78d6", "#0d366b"]                     # one hue, light to dark, in time order
T = {
    "en": dict(title="Growth in automobiles and light trucks, by period", sub="Average change per year in the number registered; the last period ends with inferred counts (2024)",
               per=lambda c: c.replace("-", "–"),
               note="Compound yearly rate between the files of December 31 of the two years. 2011 to 2022 are published counts; 2024 is inferred from make, model and model year "
                    "(within 0.2 % on published years). « Rest of Québec » is the province less the five cities shown. The cause of the slower growth after 2021 is not established."),
    "fr": dict(title="Croissance du nombre d’automobiles et de camions légers, selon la période", sub="Variation annuelle moyenne du nombre immatriculé ; la dernière période se termine par des nombres inférés (2024)",
               per=lambda c: c.replace("-", "–"),
               note="Taux annuel composé entre les fichiers du 31 décembre des deux années. Les nombres de 2011 à 2022 sont publiés ; ceux de 2024 sont inférés de la marque, du modèle et de l’année du modèle "
                    "(à 0,2 % près sur les années publiées). « Reste du Québec » : la province moins les cinq villes montrées. La cause du ralentissement après 2021 n’est pas établie."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    x = np.arange(len(r)); bw = 0.26
    for i, c in enumerate(r.columns):
        xs = x + (i - 1) * (bw + 0.02)
        ax.bar(xs, r[c], width=bw, color=COL[i], label=L["per"](c), zorder=3)
        for xi, v in zip(xs, r[c]):
            ax.text(xi, v + (0.03 if v >= 0 else -0.03), num(v, lang, 2).replace("-", "−"), ha="center", va="bottom" if v >= 0 else "top", fontsize=8, color=INK)
    ax.axhline(0, color=INK, lw=0.9, zorder=4)
    ax.set_xticks(x); ax.set_xticklabels([FR.get(k, k) if lang == "fr" else k for k in r.index], fontsize=9.5, color=INK)
    ax.set_ylim(-0.25, 1.75); ax.set_yticks([0, 0.5, 1.0, 1.5]); ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: pct(v, lang, 1, sign=False)))
    ax.axvline(4.5, color=AXIS, lw=0.8)
    ax.legend(loc="upper left", fontsize=9, ncol=3, bbox_to_anchor=(0.0, 1.06))
    finish(fig, HERE, "growth_by_city", lang, L["title"], L["sub"], L["note"], bottom=0.17)
print(out.iloc[:, :3].to_string())
