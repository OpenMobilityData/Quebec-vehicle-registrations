"""Automobiles and light trucks registered against holders of a passenger-vehicle licence, 2011-2022:
the island of Montréal (MRC 66) and Québec. Reads derived/tables/vehicles_per_licence.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/licences-vehicles/licences_vehicles.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

r = pd.read_csv(paths.TABLES / "vehicles_per_licence.csv")
isl = r[r.scope.str.startswith("Island")].set_index("year"); qc = r[r.scope == "Québec"].set_index("year")
T = {
    "en": dict(title="Automobiles and licence holders, 2011–2022", sub="Automobiles and light trucks registered (December 31) and holders of a passenger-vehicle licence (June 1)",
               l="Island of Montréal: counts", r="Automobiles and light trucks per 100 licence holders",
               a="Licence holders", b="Automobiles and light trucks", isl="Island of Montréal", qc="Québec",
               note="Licence holders: regular class 5 or probationary licence (the files give no class for probationary licences). The licence files give the MRC, not the municipality: "
                    "the island is the City of Montréal and the fifteen other municipalities. Vehicles include those owned by businesses. Both series end in 2022. "
                    "SAAQ, open data « Permis de conduire », 2011–2022."),
    "fr": dict(title="Automobiles et titulaires de permis, 2011–2022", sub="Automobiles et camions légers immatriculés (31 décembre) et titulaires d’un permis de véhicule de promenade (1er juin)",
               l="Île de Montréal : nombres", r="Automobiles et camions légers pour 100 titulaires de permis",
               a="Titulaires de permis", b="Automobiles et camions légers", isl="Île de Montréal", qc="Québec",
               note="Titulaires : permis régulier de classe 5 ou permis probatoire (les fichiers ne donnent pas la classe des permis probatoires). Les fichiers des permis donnent la MRC, non la municipalité : "
                    "l’île comprend la Ville de Montréal et les quinze autres municipalités. Les véhicules comprennent ceux des entreprises. Les deux séries s’arrêtent en 2022. "
                    "SAAQ, données ouvertes « Permis de conduire », 2011–2022."),
}
for lang, L in T.items():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(11, 5.0))
    for s, c, lab, dy in ((isl.car_licence_holders, ORANGE, L["a"], 10), (isl.automobiles_light_trucks, BLUE, L["b"], -16)):
        ax.plot(s.index, s.values, color=c, lw=2, marker="o", ms=4.5)
        ax.annotate(f"{lab}\n{num(s[2022], lang)}", (2022, s[2022]), xytext=(9, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        ax.annotate(num(s[2011], lang), (2011, s[2011]), xytext=(0, dy), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    ax.set_ylim(0, 1250000); ax.set_xlim(2010.5, 2026.3); ax.set_xticks(range(2011, 2023, 2)); thousands(ax, lang)
    ax.set_title(L["l"], fontsize=10, color=MUTED, loc="left")
    for s, c, lab in ((qc.automobiles_per_100_car_licence_holders, AQUA, L["qc"]), (isl.automobiles_per_100_car_licence_holders, VIOLET, L["isl"])):
        bx.plot(s.index, s.values, color=c, lw=2, marker="o", ms=4.5)
        bx.annotate(f"{lab}\n{num(s[2022], lang, 1)}", (2022, s[2022]), xytext=(9, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        bx.annotate(num(s[2011], lang, 1), (2011, s[2011]), xytext=(0, 9), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    bx.set_ylim(0, 115); bx.set_xlim(2010.5, 2025.6); bx.set_xticks(range(2011, 2023, 2))
    bx.set_title(L["r"], fontsize=10, color=MUTED, loc="left")
    finish(fig, HERE, "licences_vehicles", lang, L["title"], L["sub"], L["note"], bottom=0.2)
