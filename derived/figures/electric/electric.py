"""Electric, plug-in hybrid and hybrid vehicles registered, 2017-2022: Québec and the municipality of Montréal.
Published counts only: the fuel column exists from 2017 and the 2023-2024 files carry none.
Reads derived/tables/fuel_by_municipality.csv; writes derived/tables/electrified_by_year.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/electric/electric.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

f = pd.read_csv(paths.TABLES / "fuel_by_municipality.csv", dtype={"muni_code": str})
f = f[f.basis == "released"]
rows = []
for scope, d in (("Québec", f), ("Montréal", f[f.muni_code == "66023"])):
    tot = d.groupby("year").n.sum()
    for code in ("L", "W", "H"):
        s = d[d.fuel == code].groupby("year").n.sum()
        rows += [{"scope": scope, "year": y, "fuel": code, "vehicles": int(s[y]), "pct_of_all_vehicles": round(100 * s[y] / tot[y], 2)} for y in s.index]
t = pd.DataFrame(rows); t.to_csv(paths.TABLES / "electrified_by_year.csv", index=False)
NAMES = {"en": {"L": "Electric", "W": "Plug-in hybrid", "H": "Hybrid"}, "fr": {"L": "Électrique", "W": "Hybride branchable", "H": "Hybride"}}
COL = {"L": BLUE, "W": ORANGE, "H": AQUA}
T = {
    "en": dict(title="Electric and hybrid vehicles registered, 2017–2022", sub="Published counts on December 31, all vehicle types; the fuel column begins in 2017",
               scopes={"Québec": "Québec", "Montréal": "Municipality of Montréal"},
               note="The files released for 2023 and 2024 carry no fuel. Inferring it from make, model and model year under-counts electric vehicles by 4 to 19 % on published years, so no count is shown after 2022. "
                    "Each panel has its own scale, from zero."),
    "fr": dict(title="Véhicules électriques et hybrides immatriculés, 2017–2022", sub="Nombres publiés au 31 décembre, tous les types de véhicules ; la colonne du carburant commence en 2017",
               scopes={"Québec": "Québec", "Montréal": "Municipalité de Montréal"},
               note="Les fichiers communiqués pour 2023 et 2024 ne donnent pas le carburant. L’inférer de la marque, du modèle et de l’année du modèle sous-compte les véhicules électriques de 4 à 19 % sur les années publiées ; aucun nombre n’est donc montré après 2022. "
                    "Chaque panneau a sa propre échelle, à partir de zéro."),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9))
    for ax, scope in zip(axes, ("Québec", "Montréal")):
        d = t[t.scope == scope]
        for code in ("L", "W", "H"):
            s = d[d.fuel == code].set_index("year").vehicles
            ax.plot(s.index, s.values, color=COL[code], lw=2, marker="o", ms=4.5)
            ax.annotate(f"{NAMES[lang][code]}\n{num(s[2022], lang)}", (2022, s[2022]), xytext=(9, {"L": 9, "H": -9, "W": 0}[code] if scope == "Québec" else 0), textcoords="offset points", va="center", fontsize=9, color=INK)
            if code == "H":
                ax.annotate(num(s[2017], lang), (2017, s[2017]), xytext=(0, 7), textcoords="offset points", ha="center", fontsize=8, color=INK)
        e17 = d[(d.fuel == "L") & (d.year == 2017)].vehicles.iloc[0]; w17 = d[(d.fuel == "W") & (d.year == 2017)].vehicles.iloc[0]
        ax.annotate(f"{NAMES[lang]['L']} {num(e17, lang)}\n{NAMES[lang]['W']} {num(w17, lang)}", (2017, max(e17, w17)), xytext=(-4, 10), textcoords="offset points", ha="left", fontsize=8, color=INK)
        ax.set_ylim(0, d.vehicles.max() * 1.15); ax.set_xlim(2016.6, 2024.4); ax.set_xticks(range(2017, 2023)); thousands(ax, lang)
        ax.set_title(L["scopes"][scope], fontsize=10.5, color=INK, loc="left")
    finish(fig, HERE, "electric", lang, L["title"], L["sub"], L["note"], bottom=0.17)
print(t.pivot_table(index=["scope", "year"], columns="fuel", values="vehicles").astype(int).to_string())
print(t[(t.year == 2022)].to_string(index=False))
