"""Automobiles and light trucks in the municipality of Montréal: the 2011-2021 trend carried to 2035, beside the
published count for 2022 and the inferred counts for 2023-2024. Reads derived/tables/trend_scenario.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/trend-scenario/trend_scenario.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

s = pd.read_csv(paths.TABLES / "trend_scenario.csv").set_index("year")
c = s["count"].dropna()
per_year = round((s.trend_2011_2021[2035] - s.trend_2011_2021[2011]) / 24)
T = {
    "en": dict(title="Montréal: the 2011–2021 trend carried forward, and what the files show",
               sub="Automobiles and light trucks, municipality of Montréal. The axis does not start at zero.",
               trend=f"straight line through 2011–2021\n({num(per_year, 'en')} more a year), carried to 2035",
               pub="published", inf="inferred (2023–2024)", gap=lambda y: f"{y}: {num(abs(s.count_minus_trend[y]), 'en')} below the line",
               note="The line is not a forecast: it shows where the counts of 2011–2021 were heading. 2022 is the published count; 2023 and 2024 are inferred from make, model and model year "
                    "(within 0.13 % on published years)."),
    "fr": dict(title="Montréal : la tendance de 2011–2021 prolongée, et ce que montrent les fichiers",
               sub="Automobiles et camions légers, municipalité de Montréal. L’axe ne part pas de zéro.",
               trend=f"droite ajustée sur 2011–2021\n({num(per_year, 'fr')} de plus par an), prolongée jusqu’en 2035",
               pub="publié", inf="inféré (2023–2024)", gap=lambda y: f"{y} : {num(abs(s.count_minus_trend[y]), 'fr')} sous la droite",
               note="La droite n’est pas une prévision : elle montre où menaient les nombres de 2011–2021. 2022 est le nombre publié ; 2023 et 2024 sont inférés de la marque, du modèle et de l’année du modèle "
                    "(à 0,13 % près sur les années publiées)."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10, 5.6))
    ax.plot(s.index, s.trend_2011_2021, color=MUTED, lw=1.6, ls=(0, (4, 3)))
    ax.annotate(L["trend"], (2031, s.trend_2011_2021[2031]), xytext=(-6, 12), textcoords="offset points", ha="right", fontsize=9, color=MUTED)
    released_inferred(ax, c, BLUE, label=L["pub"], inferred_label=L["inf"])
    for y, dy in ((2022, -34), (2024, -18)):
        ax.annotate(L["gap"](y), (y, c[y]), xytext=(14, dy), textcoords="offset points", fontsize=9, color=INK,
                    arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.8))
    for y in (2011, 2021):
        ax.annotate(num(c[y], lang), (y, c[y]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.annotate(num(s.trend_2011_2021[2035], lang), (2035, s.trend_2011_2021[2035]), xytext=(-2, -24), textcoords="offset points", ha="right", fontsize=8.5, color=MUTED)
    ax.set_ylim(650000, 880000); ax.set_xlim(2010.4, 2035.6); ax.set_xticks(range(2011, 2036, 3)); thousands(ax, lang)
    ax.legend(loc="lower right", fontsize=9)
    finish(fig, HERE, "trend_scenario", lang, L["title"], L["sub"], L["note"], bottom=0.16)
