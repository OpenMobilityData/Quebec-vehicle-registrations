"""Net mass of automobiles and light trucks registered in the municipality of Montréal, 2011-2022.
Reads derived/tables/mass_automobiles.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/mass-automobiles/mass_automobiles.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

a = pd.read_csv(paths.TABLES / "mass_automobiles.csv")
m = a[a.scope == "Montréal"].set_index("year")
T = {
    "en": dict(title="Net mass of automobiles and light trucks registered in Montréal, 2011–2022",
               sub="Municipality of Montréal; net mass is the vehicle empty, as recorded by the SAAQ",
               l=("Net mass (kg)", ["90th percentile", "median", "10th percentile"]), r="Share at 2,000 kg or more (%)",
               note=f"Mean {num(m.mean_kg[2011], 'en')} kg in 2011, {num(m.mean_kg[2022], 'en')} kg in 2022. The 2023–2024 files carry no mass. "
                    f"Mass is recorded for {num(m.pct_with_mass.min(), 'en', 1)} % or more of these vehicles each year."),
    "fr": dict(title="Masse nette des automobiles et camions légers immatriculés à Montréal, 2011–2022",
               sub="Municipalité de Montréal ; la masse nette est celle du véhicule à vide, telle que consignée par la SAAQ",
               l=("Masse nette (kg)", ["90e centile", "médiane", "10e centile"]), r="Part à 2 000 kg ou plus (%)",
               note=f"Moyenne de {num(m.mean_kg[2011], 'fr')} kg en 2011, de {num(m.mean_kg[2022], 'fr')} kg en 2022. Les fichiers de 2023–2024 ne donnent pas la masse. "
                    f"La masse est consignée pour {num(m.pct_with_mass.min(), 'fr', 1)} % ou plus de ces véhicules chaque année."),
}
for lang, L in T.items():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 4.9), gridspec_kw=dict(width_ratios=[1.25, 1]))
    for col, c, lab in zip(("p90_kg", "median_kg", "p10_kg"), (ORANGE, BLUE, AQUA), L["l"][1]):
        ax.plot(m.index, m[col], color=c, lw=2, marker="o", ms=4.5)
        ax.annotate(f"{lab}\n{num(m[col][2022], lang)} kg", (2022, m[col][2022]), xytext=(9, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        ax.annotate(num(m[col][2011], lang), (2011, m[col][2011]), xytext=(0, 8), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_ylim(0, 2400); ax.set_xlim(2010.5, 2025.2); ax.set_xticks(range(2011, 2023, 2)); thousands(ax, lang)
    ax.set_title(L["l"][0], fontsize=10, color=MUTED, loc="left")
    bx.plot(m.index, m.pct_2000kg_or_more, color=VIOLET, lw=2, marker="o", ms=4.5)
    for yr in (2011, 2022):
        bx.annotate(pct(m.pct_2000kg_or_more[yr], lang, 1, sign=False), (yr, m.pct_2000kg_or_more[yr]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9, color=INK)
    bx.set_ylim(0, m.pct_2000kg_or_more.max() * 1.3); bx.set_xticks(range(2011, 2023, 2)); bx.set_xlim(2010.4, 2022.8)
    bx.set_title(L["r"], fontsize=10, color=MUTED, loc="left")
    finish(fig, HERE, "mass_automobiles", lang, L["title"], L["sub"], L["note"], bottom=0.17)
