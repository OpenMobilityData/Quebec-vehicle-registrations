"""The Montréal series and the 2011-2021 line, set against two physical bounds computed by scripts/street_space.py:
every legal metre of curb used for parking, and every travel lane full nose to tail. One panel per bound.
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
park = (b["parking bound: vehicles at 6.0 m each"], b["parking bound: vehicles at 5.0 m each"])
drive = (b["driving bound: vehicles at 8.0 m each"], b["driving bound: vehicles at 6.0 m each"])
legal, curb, ban, lanes, tag = b["legal curb (km)"], b["curb, both sides (km)"], b[[k for k in b.index if k.startswith("share of that curb")][0]], \
    b["travel lanes in the municipality of Montréal (km)"], b[[k for k in b.index if k.startswith("share of those lane")][0]]
T = {
    "en": dict(title="Montréal's automobiles against two hypothetical bounds of its streets",
               sub="Automobiles and light trucks, municipality of Montréal; the bands are limits under stated assumptions, not measurements",
               p=("If every legal metre of curb were used for parking", f"{num(park[0], 'en')} to {num(park[1], 'en')} vehicles\n(6 to 5 m each; {num(legal, 'en')} km of legal curb)"),
               d=("If every travel lane were full, nose to tail", f"{num(drive[0], 'en')} to {num(drive[1], 'en')} vehicles\n(8 to 6 m each; {num(lanes, 'en')} km of lanes)"),
               trend="line through 2011–2021,\ncarried to 2050 (not a forecast)", pub="published", inf="inferred (2023–2024)",
               note=f"Parking: City géobase (October 14, 2026), {num(curb, 'en')} km of curb without autoroutes, bridges, tunnels, ramps and back lanes; less 5 m at each end of each block face, and less the stretches where the City's sign inventory "
                    f"(October 23, 2026) forbids stopping or parking at all times ({num(ban, 'en', 1)} % in the boroughs where the inventory is complete, applied to the others). Driveways, hydrants, bus stops and hourly or permit restrictions are not deducted. "
                    f"Driving: OpenStreetMap (Geofabrik, November 11, 2026), autoroutes included, lane counts from the map for {num(tag, 'en', 0)} % of lane-kilometres. Vehicles kept off the street are in neither bound; the registered vehicles are never all "
                    "on the road at once; vehicles from elsewhere are not counted; traffic stops flowing well before every lane is full. © OpenStreetMap contributors."),
    "fr": dict(title="Les automobiles de Montréal et deux bornes hypothétiques de ses rues",
               sub="Automobiles et camions légers, municipalité de Montréal ; les bandes sont des limites sous hypothèses énoncées, non des mesures",
               p=("Si chaque mètre de bordure permis servait au stationnement", f"{num(park[0], 'fr')} à {num(park[1], 'fr')} véhicules\n(6 à 5 m chacun ; {num(legal, 'fr')} km de bordure permise)"),
               d=("Si chaque voie de circulation était pleine, pare-chocs contre pare-chocs", f"{num(drive[0], 'fr')} à {num(drive[1], 'fr')} véhicules\n(8 à 6 m chacun ; {num(lanes, 'fr')} km de voies)"),
               trend="droite ajustée sur 2011–2021,\nprolongée jusqu’en 2050 (non une prévision)", pub="publié", inf="inféré (2023–2024)",
               note=f"Stationnement : géobase de la Ville (14 octobre 2026), {num(curb, 'fr')} km de bordure sans les autoroutes, ponts, tunnels, bretelles et ruelles ; moins 5 m à chaque bout de chaque côté d’îlot, et moins les tronçons où l’inventaire de signalisation de la Ville "
                    f"(23 octobre 2026) interdit l’arrêt ou le stationnement en tout temps ({num(ban, 'fr', 1)} % dans les arrondissements où l’inventaire est complet, appliqué aux autres). Entrées, bornes d’incendie, arrêts d’autobus et restrictions horaires ou par permis non déduits. "
                    f"Circulation : OpenStreetMap (Geofabrik, 11 novembre 2026), autoroutes comprises, nombre de voies tiré de la carte pour {num(tag, 'fr', 0)} % des kilomètres de voie. Les véhicules gardés hors rue ne sont dans aucune borne ; les véhicules immatriculés ne sont jamais tous "
                    "sur la route en même temps ; ceux d’ailleurs ne sont pas comptés ; la circulation cesse bien avant que chaque voie soit pleine. © les contributeurs d’OpenStreetMap."),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 6.0), sharey=True)
    for ax, band, col, lab in zip(axes, (park, drive), ("#fbe3d6", "#e4e0f7"), (L["p"], L["d"])):
        ax.axhspan(*band, color=col, lw=0, zorder=0)
        ax.text(2011.5, band[1] + 30000, lab[1], fontsize=9, color=INK, va="bottom")
        ax.plot(s.index, s.trend_2011_2021, color=MUTED, lw=1.6, ls=(0, (4, 3)))
        released_inferred(ax, c, BLUE, label=L["pub"], inferred_label=L["inf"])
        ax.annotate(num(c[2024], lang), (2024, c[2024]), xytext=(4, -16), textcoords="offset points", fontsize=9, color=INK)
        ax.set_title(lab[0], fontsize=10.5, color=INK, loc="left")
        ax.set_ylim(0, 1750000); ax.set_xlim(2010.4, 2050.6); ax.set_xticks(range(2011, 2051, 6)); thousands(ax, lang)
    axes[0].annotate(L["trend"], (2043, s.trend_2011_2021[2043]), xytext=(0, -24), textcoords="offset points", ha="center", va="top", fontsize=9, color=MUTED)
    axes[1].legend(loc="lower right", fontsize=9)
    finish(fig, HERE, "trend_thresholds", lang, L["title"], L["sub"], L["note"], bottom=0.22)
