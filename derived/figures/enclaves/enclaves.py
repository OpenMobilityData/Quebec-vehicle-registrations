"""All vehicles registered in Côte-Saint-Luc, Westmount, Hampstead and Montréal-Ouest, 2011-2024 (nothing
inferred). Reads derived/tables/vehicles_by_municipality.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/enclaves/enclaves.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

t = pd.read_csv(paths.TABLES / "vehicles_by_municipality.csv", dtype={"muni_code": str})
M = [("66058", "Côte-Saint-Luc"), ("66032", "Westmount"), ("66062", "Hampstead"), ("66047", "Montréal-Ouest")]
w = t[t.muni_code.isin([c for c, _ in M])].pivot_table(index="year", columns="muni_code", values="n", aggfunc="sum")
tot = w.sum(axis=1)
T = {
    "en": dict(title="Vehicles registered in four municipalities enclosed by Montréal, 2011–2024",
               sub=f"All vehicle types; together {num(tot[2011], 'en')} in 2011, {num(tot.max(), 'en')} in {tot.idxmax()} (the highest), {num(tot[2024], 'en')} in 2024",
               note="Nothing is inferred: the count needs no vehicle type. Each panel has its own scale, from zero.", mark="access\nrelease"),
    "fr": dict(title="Véhicules immatriculés dans quatre municipalités enclavées dans Montréal, 2011–2024",
               sub=f"Tous les types de véhicules ; ensemble {num(tot[2011], 'fr')} en 2011, {num(tot.max(), 'fr')} en {tot.idxmax()} (le maximum), {num(tot[2024], 'fr')} en 2024",
               note="Rien n’est inféré : le compte ne demande pas le type de véhicule. Chaque panneau a sa propre échelle, à partir de zéro.", mark="Loi sur\nl’accès"),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 4, figsize=(11, 4.6))
    for ax, (code, name) in zip(axes, M):
        s = w[code]
        ax.axvspan(2022.5, 2024.6, color="#eef1f4", lw=0, zorder=0)
        ax.plot(s.index, s.values, color=BLUE, lw=2, marker="o", ms=4)
        ax.set_ylim(0, s.max() * 1.22); ax.set_xlim(2010.4, 2024.6); ax.set_xticks([2011, 2015, 2019, 2023])
        ax.set_title(name, fontsize=10.5, color=INK, loc="left")
        thousands(ax, lang); ax.tick_params(labelsize=8.5)
        for yr in (2011, 2024):
            ax.annotate(num(s[yr], lang), (yr, s[yr]), xytext=(0, 8), textcoords="offset points", ha="left" if yr == 2011 else "right", fontsize=8.5, color=INK)
        ax.text(2023.55, s.max() * 1.2, L["mark"], fontsize=6.5, color=MUTED, ha="center", va="top")
    finish(fig, HERE, "enclaves", lang, L["title"], L["sub"], L["note"], bottom=0.17)
    fig.subplots_adjust(wspace=0.38)
