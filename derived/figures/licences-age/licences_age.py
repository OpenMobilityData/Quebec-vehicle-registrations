"""Holders of a passenger-vehicle licence on the island of Montréal by age group, 2011-2022.
Reads derived/tables/licence_holders_by_age.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/licences-age/licences_age.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

a = pd.read_csv(paths.TABLES / "licence_holders_by_age.csv")
a = a[a.scope.str.startswith("Island")]
G = {"16-19": "16–24", "20-24": "16–24", "25-34": "25–44", "35-44": "25–44", "45-54": "45–64", "55-64": "45–64", "65 ans ou plus": "65+"}
a["g"] = a.age_band.map(G)
w = a.dropna(subset=["g"]).pivot_table(index="year", columns="g", values="car_licence_holders", aggfunc="sum")
ORDER = ["25–44", "45–64", "65+", "16–24"]; COL = dict(zip(ORDER, [BLUE, ORANGE, VIOLET, AQUA]))
T = {
    "en": dict(title="Licence holders on the island of Montréal by age, 2011–2022", sub="Holders of a passenger-vehicle licence (regular class 5 or probationary) on June 1, by age group",
               lab={"16–24": "16 to 24", "25–44": "25 to 44", "45–64": "45 to 64", "65+": "65 and over"},
               note="Counts of holders, not rates: no population is used. The licence files give the MRC, not the municipality: the island is the City of Montréal and the fifteen other municipalities. "
                    "SAAQ, open data « Permis de conduire », 2011–2022."),
    "fr": dict(title="Titulaires de permis de l’île de Montréal selon l’âge, 2011–2022", sub="Titulaires d’un permis de véhicule de promenade (régulier de classe 5 ou probatoire) au 1er juin, selon le groupe d’âge",
               lab={"16–24": "16 à 24 ans", "25–44": "25 à 44 ans", "45–64": "45 à 64 ans", "65+": "65 ans ou plus"},
               note="Nombres de titulaires, non des taux : aucune population n’est utilisée. Les fichiers des permis donnent la MRC, non la municipalité : l’île comprend la Ville de Montréal et les quinze autres municipalités. "
                    "SAAQ, données ouvertes « Permis de conduire », 2011–2022."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for g in ORDER:
        s = w[g]
        ax.plot(s.index, s.values, color=COL[g], lw=2, marker="o", ms=4.5)
        ch = 100 * (s[2022] / s[2011] - 1)
        ax.annotate(f"{L['lab'][g]}\n{num(s[2022], lang)} ({pct(ch, lang, 0)})", (2022, s[2022]), xytext=(9, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        ax.annotate(num(s[2011], lang), (2011, s[2011]), xytext=(0, -16 if g == "45–64" else 8), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_ylim(0, w.max().max() * 1.15); ax.set_xlim(2010.5, 2024.6); ax.set_xticks(range(2011, 2023)); thousands(ax, lang)
    finish(fig, HERE, "licences_age", lang, L["title"], L["sub"], L["note"], bottom=0.16)
print(w.loc[[2011, 2022]].T.assign(change_pct=lambda d: (100 * (d[2022] / d[2011] - 1)).round(1)).to_string())
