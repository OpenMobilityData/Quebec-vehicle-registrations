"""Share of automobiles and light trucks present at age 3 that are still registered at each later age,
Québec, three periods. Reads derived/tables/cohort_survival.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/cohort-survival/cohort_survival.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

s = pd.read_csv(paths.TABLES / "cohort_survival.csv")
q = s[s.scope == "Québec"].pivot(index="age", columns="period", values="pct_still_registered")
P = list(q.columns)
COL = dict(zip(P, ["#9ec5f4", "#2a78d6", "#0d366b"]))     # one hue, light to dark, in time order
half = {c: int(q.index[(q[c] <= 50).values.argmax()]) for c in P}
T = {
    "en": dict(title="How long automobiles and light trucks stay registered in Québec",
               sub="Of the vehicles of a model year registered at age 3, the share still registered at each later age, by period",
               x="Age of the vehicle (year of the file minus model year)", lab=lambda c: c.replace(" to ", "–"),
               half="half remain", fifteen="At 15 years:",
               note="Each step compares one model year's count in two consecutive yearly files. Counts for 2023 and 2024 are inferred (type from make, model and model year), "
                    "so the last period carries that method's error, under 0.2 % on published years. A vehicle that leaves Québec counts as a departure; one that arrives used counts as an arrival."),
    "fr": dict(title="Combien de temps les automobiles et camions légers restent immatriculés au Québec",
               sub="Des véhicules d’une année de modèle immatriculés à 3 ans, la part encore immatriculée à chaque âge ultérieur, selon la période",
               x="Âge du véhicule (année du fichier moins année du modèle)", lab=lambda c: c.replace(" to ", "–"),
               half="il en reste la moitié", fifteen="À 15 ans :",
               note="Chaque pas compare le nombre d’une année de modèle dans deux fichiers annuels consécutifs. Les nombres de 2023 et 2024 sont inférés (type déduit de la marque, du modèle et de l’année), "
                    "de sorte que la dernière période porte l’erreur de cette méthode, inférieure à 0,2 % sur les années publiées. Un véhicule qui quitte le Québec compte comme un départ ; un véhicule d’occasion qui y arrive, comme une arrivée."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.axhline(50, color=MUTED, lw=1, ls=(0, (2, 2)))
    ax.text(3.1, 51.5, L["half"], fontsize=8.5, color=MUTED)
    for c in P:
        ax.plot(q.index, q[c], color=COL[c], lw=2.2)
        ax.annotate(f"{L['lab'](c)}  {pct(q[c][25], lang, 0, sign=False)}", (25, q[c][25]), xytext=(8, {0: -7, 1: 4, 2: 6}[P.index(c)]), textcoords="offset points", va="center", fontsize=9, color=INK)
        ax.plot([15], [q[c][15]], marker="o", ms=7, color=COL[c], mec=SURFACE, mew=1.5)
    ax.text(15.4, 78, L["fifteen"] + "\n" + "\n".join(f"{L['lab'](c)}  {pct(q[c][15], lang, 0, sign=False)}" for c in P), fontsize=9, color=INK, va="top")
    ax.set_ylim(0, 105); ax.set_xlim(3, 29.5); ax.set_xticks(range(3, 26, 2)); ax.set_xlabel(L["x"])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: pct(v, lang, 0, sign=False)))
    finish(fig, HERE, "cohort_survival", lang, L["title"], L["sub"], L["note"], bottom=0.2)
