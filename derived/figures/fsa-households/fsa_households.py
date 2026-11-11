"""Automobiles and light trucks per household by FSA on the island of Montréal (postal codes in H),
2024, against the share of commuters who drive (2021 Census). Reads derived/tables/fsa_vehicles_census.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/fsa-households/fsa_households.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

v = pd.read_csv(paths.TABLES / "fsa_vehicles_census.csv")
d = v[(v.year == 2024) & v.fsa.str.startswith("H", na=False) & (v.households >= 1000)].copy()
MAIN, NEAR = ["H4A", "H4B"], ["H3X", "H4V"]
med = d.au_per_household.median()
T = {
    "en": dict(title="Automobiles and light trucks per household, by FSA: island of Montréal and Laval, 2024",
               sub=f"Each dot is one FSA beginning with H ({len(d)} with 1,000 households or more); rue de Terrebonne runs through H4A and H4B",
               x="Commuters who drive a car, truck or van to work, 2021 Census (%)", y="Automobiles and light trucks per household",
               med=f"median of these FSAs: {num(med, 'en', 2)}",
               note="Vehicles: 2024 file, type inferred from make, model and model year; all owners, businesses included, so an FSA with fleets or "
                    "dealers stands high. Households and commuting: 2021 Census profile by FSA. "
                    "The two quantities are three years apart. {above} Statistics Canada, 2021 Census, "
                    "catalogue 98-401-X2021013."),
    "fr": dict(title="Automobiles et camions légers par ménage, selon la RTA : île de Montréal et Laval, 2024",
               sub=f"Chaque point est une RTA commençant par H ({len(d)} comptant 1 000 ménages ou plus) ; la rue de Terrebonne traverse H4A et H4B",
               x="Navetteurs qui conduisent une automobile, un camion ou une fourgonnette, Recensement de 2021 (%)", y="Automobiles et camions légers par ménage",
               med=f"médiane de ces RTA : {num(med, 'fr', 2)}",
               note="Véhicules : fichier de 2024, type inféré de la marque, du modèle et de l’année du modèle ; tous les propriétaires, entreprises comprises : "
                    "une RTA où logent des parcs ou des concessionnaires ressort donc haut. Ménages et navettage : profil du Recensement de 2021 par RTA. "
                    "Trois ans séparent les deux grandeurs. {above} Statistique Canada, Recensement de 2021, "
                    "no 98-401-X2021013 au catalogue."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10, 6))
    o = d[~d.fsa.isin(MAIN + NEAR)]
    ax.scatter(o.pct_commute_car_driver, o.au_per_household, s=26, color="#aab2b8", lw=0, zorder=2)
    n = d[d.fsa.isin(NEAR)]
    ax.scatter(n.pct_commute_car_driver, n.au_per_household, s=44, color=MUTED, edgecolor=SURFACE, lw=1.2, zorder=3)
    m = d[d.fsa.isin(MAIN)]
    ax.scatter(m.pct_commute_car_driver, m.au_per_household, s=80, color=BLUE, edgecolor=SURFACE, lw=1.5, zorder=4)
    OFF = {"H4A": (-10, 10, "right"), "H4B": (10, -14, "left"), "H3X": (9, 4, "left"), "H4V": (9, -10, "left")}
    for r in d[d.fsa.isin(MAIN + NEAR)].itertuples():
        dx, dy, ha = OFF[r.fsa]
        ax.annotate(f"{r.fsa}  {num(r.au_per_household, lang, 2)}", (r.pct_commute_car_driver, r.au_per_household), xytext=(dx, dy),
                    textcoords="offset points", ha=ha, fontsize=9.5, color=INK, fontweight="bold" if r.fsa in MAIN else "normal")
    ax.axhline(med, color=MUTED, lw=1, ls=(0, (2, 2)), zorder=1)
    ax.text(d.pct_commute_car_driver.min(), med + 0.03, L["med"], fontsize=8.5, color=MUTED, va="bottom")
    ax.set_ylim(0, min(3.2, d.au_per_household.max() * 1.05)); ax.set_xlabel(L["x"]); ax.set_ylabel(L["y"])
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v_, _: num(v_, lang, 1)))
    ax.grid(axis="x", color=GRID, lw=0.8)
    hi = d[d.au_per_household > 3.2].sort_values("au_per_household")
    above = "" if hi.empty else ("Above the scale: " if lang == "en" else "Au-dessus de l’échelle : ") + ", ".join(f"{r.fsa} {num(r.au_per_household, lang, 2)}" for r in hi.itertuples()) + "."
    finish(fig, HERE, "fsa_households", lang, L["title"], L["sub"], L["note"].replace("{above}", above), bottom=0.2)
print(d.sort_values("au_per_household").head(6)[["fsa", "au_per_household", "pct_commute_car_driver"]].to_string(index=False))
print(d.sort_values("au_per_household").tail(8)[["fsa", "au_per_household", "households", "automobiles_light_trucks_inferred"]].to_string(index=False))
print("rank of H4A, H4B from the lowest:", (d.au_per_household.rank().loc[d.fsa.isin(MAIN)]).tolist(), "of", len(d))
