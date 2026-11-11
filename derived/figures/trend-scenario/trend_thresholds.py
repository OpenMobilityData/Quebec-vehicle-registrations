"""The Montréal series and the 2011-2021 line, set against two physical bounds computed from the City's street
network (scripts/street_space.py): every metre of curb used for parking, and every lane full nose to tail.
Reads derived/tables/trend_scenario.csv and street_space_bounds.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/trend-scenario/trend_thresholds.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

s = pd.read_csv(paths.TABLES / "trend_scenario.csv").set_index("year")
b = pd.read_csv(paths.TABLES / "street_space_bounds.csv").set_index("quantity").value
c = s["count"].dropna()
curb = (b["curb bound: vehicles at 6.0 m each"], b["curb bound: vehicles at 5.0 m each"])
jam = (b["standstill bound: vehicles at 8.0 m each"], b["standstill bound: vehicles at 6.0 m each"])
km_c, km_k, km_l = b["street centreline in the municipality of Montréal (km)"], b["curb, both sides (km)"], b["lanes, at least (km)"]
cross = next((y for y in s.index if s.trend_2011_2021[y] >= jam[0]), None)
T = {
    "en": dict(title="Montréal's automobiles against two physical bounds of its streets",
               sub="Automobiles and light trucks, municipality of Montréal; the bounds are hypothetical limits, not measurements",
               curb=f"Every metre of both curbs of every street used for parking:\n{num(curb[0], 'en')} to {num(curb[1], 'en')} vehicles (6 to 5 m each; {num(km_k, 'en')} km of curb)",
               jam=f"Every lane of every street full, nose to tail:\n{num(jam[0], 'en')} to {num(jam[1], 'en')} vehicles (8 to 6 m each; {num(km_l, 'en')} km of lanes at least)",
               trend="straight line through 2011–2021,\ncarried to 2050 (not a forecast)", pub="published", inf="inferred (2023–2024)",
               note=f"Bounds from the City's géobase of October 14, 2026: {num(km_c, 'en')} km of street in the municipality (autoroutes, bridges, tunnels, ramps and back lanes left out). Curb: no deduction for corners, driveways, hydrants, "
                    "bus stops or signs, so real street parking is lower. Lanes: one counted for a one-way street and two for a two-way street, since the file gives no lane count. Vehicles kept off the street are in neither bound, "
                    "the registered vehicles are never all on the road at once, and traffic stops flowing well before every lane is full."),
    "fr": dict(title="Les automobiles de Montréal et deux bornes physiques de ses rues",
               sub="Automobiles et camions légers, municipalité de Montréal ; les bornes sont des limites hypothétiques, non des mesures",
               curb=f"Chaque mètre des deux bordures de chaque rue servant au stationnement :\n{num(curb[0], 'fr')} à {num(curb[1], 'fr')} véhicules (6 à 5 m chacun ; {num(km_k, 'fr')} km de bordure)",
               jam=f"Chaque voie de chaque rue pleine, pare-chocs contre pare-chocs :\n{num(jam[0], 'fr')} à {num(jam[1], 'fr')} véhicules (8 à 6 m chacun ; au moins {num(km_l, 'fr')} km de voies)",
               trend="droite ajustée sur 2011–2021,\nprolongée jusqu’en 2050 (non une prévision)", pub="publié", inf="inféré (2023–2024)",
               note=f"Bornes tirées de la géobase de la Ville du 14 octobre 2026 : {num(km_c, 'fr')} km de rues dans la municipalité (autoroutes, ponts, tunnels, bretelles et ruelles exclus). Bordure : aucune déduction pour les coins, les entrées, "
                    "les bornes d’incendie, les arrêts d’autobus ou la signalisation, de sorte que le stationnement réel sur rue est moindre. Voies : une pour une rue à sens unique et deux pour une rue à double sens, le fichier ne donnant pas le nombre de voies. "
                    "Les véhicules gardés hors rue ne sont dans aucune des bornes, les véhicules immatriculés ne sont jamais tous sur la route en même temps, et la circulation cesse bien avant que chaque voie soit pleine."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10.5, 6.2))
    ax.axhspan(*curb, color="#fbe3d6", lw=0, zorder=0); ax.axhspan(*jam, color="#e4e0f7", lw=0, zorder=0)
    ax.text(2011.3, (curb[0] + curb[1]) / 2, L["curb"], fontsize=9, color=INK, va="center")
    ax.text(2011.3, jam[1] + 22000, L["jam"], fontsize=9, color=INK, va="bottom")
    ax.plot(s.index, s.trend_2011_2021, color=MUTED, lw=1.6, ls=(0, (4, 3)))
    ax.annotate(L["trend"], (2046, s.trend_2011_2021[2046]), xytext=(0, -30), textcoords="offset points", ha="center", va="top", fontsize=9, color=MUTED)
    released_inferred(ax, c, BLUE, label=L["pub"], inferred_label=L["inf"])
    ax.annotate(num(c[2024], lang), (2024, c[2024]), xytext=(6, -16), textcoords="offset points", fontsize=9, color=INK)
    ax.annotate(num(c[2011], lang), (2011, c[2011]), xytext=(2, -17), textcoords="offset points", ha="left", fontsize=9, color=INK)
    ax.set_ylim(0, 1750000); ax.set_xlim(2010.4, 2050.6); ax.set_xticks(range(2011, 2051, 3)); thousands(ax, lang)
    ax.legend(loc="lower right", fontsize=9)
    finish(fig, HERE, "trend_thresholds", lang, L["title"], L["sub"], L["note"], bottom=0.2)
print("line reaches the lower standstill bound in", cross, "; 2050 on the line:", int(s.trend_2011_2021[2050]))
