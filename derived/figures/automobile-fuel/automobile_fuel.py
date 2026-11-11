"""Automobiles and light trucks (type AU) by fuel, 2011-2024: gasoline and diesel beside hybrid, plug-in hybrid
and electric. Left: counts from zero. Right: change in the number of vehicles since 2017, the first published year
with fuel (2017-2024). One figure for Québec, one for the municipality of Montréal. Reads derived/tables/automobile_fuel_by_year.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/automobile-fuel/automobile_fuel.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

t = pd.read_csv(paths.TABLES / "automobile_fuel_by_year.csv")
ORDER = ["E", "D", "H", "W", "L"]
COL = {"E": VIOLET, "D": YELLOW, "H": AQUA, "W": ORANGE, "L": BLUE}
NAMES = {"en": {"E": "Gasoline", "D": "Diesel", "H": "Hybrid", "W": "Plug-in hybrid", "L": "Electric"},
         "fr": {"E": "Essence", "D": "Diesel", "H": "Hybride", "W": "Hybride branchable", "L": "Électrique"}}
SC = {"Québec": ("quebec", {"en": "Québec", "fr": "Québec"}), "Montréal": ("montreal", {"en": "municipality of Montréal", "fr": "municipalité de Montréal"})}
T = {
    "en": dict(title="Automobiles and light trucks by fuel, {s}, 2011–2024", sub="Solid: published counts, 2017–2022. Dashed with hollow points: inferred from make, model and model year.",
               l="Vehicles registered", r="Change in the number of vehicles since 2017",
               note="Type AU only (automobiles and light trucks), businesses included. Before 2017 the type is published and the fuel inferred; for 2023–2024 both are inferred. On published years, all vehicle types together, "
                    "the forward inference is within 0.5 % for gasoline and runs 4 to 19 % low for electric; the backward one is within 6 %. Other fuels (propane, natural gas, not stated) are left out."),
    "fr": dict(title="Automobiles et camions légers selon le carburant, {s}, 2011–2024", sub="Trait plein : nombres publiés, 2017–2022. Tirets et points creux : inférés de la marque, du modèle et de l’année du modèle.",
               l="Véhicules immatriculés", r="Variation du nombre de véhicules depuis 2017",
               note="Type AU seulement (automobiles et camions légers), entreprises comprises. Avant 2017, le type est publié et le carburant inféré ; pour 2023–2024, les deux sont inférés. Sur les années publiées, tous types de véhicules confondus, "
                    "l’inférence vers l’avant est à 0,5 % près pour l’essence et inférieure de 4 à 19 % pour l’électrique ; vers l’arrière, elle est à 6 % près. Les autres carburants (propane, gaz naturel, non précisé) sont exclus."),
}


def draw(ax, s, c):
    ax.plot(s.loc[2017:2022].index, s.loc[2017:2022].values, color=c, lw=2, marker="o", ms=4)
    for seg in (s.loc[:2017], s.loc[2022:]):
        ax.plot(seg.index, seg.values, color=c, lw=1.6, ls=(0, (3, 2)))
    hol = pd.concat([s.loc[:2016], s.loc[2023:]])
    ax.plot(hol.index, hol.values, ls="none", marker="o", ms=5, mfc=SURFACE, mec=c, mew=1.5)


def spread(vals, gap):
    """Label positions kept at least `gap` apart, in the order of the values."""
    o = sorted(vals, key=vals.get); y = {}
    for i, k in enumerate(o):
        y[k] = vals[k] if i == 0 else max(vals[k], y[o[i - 1]] + gap)
    return y


for scope, (slug, sname) in SC.items():
    w = t[t.scope == scope].pivot(index="year", columns="fuel", values="vehicles")[ORDER]
    d = (w - w.loc[2017]).loc[2017:]
    for lang, L in T.items():
        fig, (ax, bx) = plt.subplots(1, 2, figsize=(11.5, 5.4))
        ax.axvspan(2016.5, 2022.5, color="#f3f5f6", lw=0, zorder=0); bx.axvspan(2016.5, 2022.5, color="#f3f5f6", lw=0, zorder=0)
        ya = spread({f: w[f][2024] for f in ORDER}, w.values.max() * 0.055); yb = spread({f: d[f][2024] for f in ORDER}, (d.values.max() - d.values.min()) * 0.065)
        for f in ORDER:
            draw(ax, w[f], COL[f]); draw(bx, d[f], COL[f])
            ax.annotate(f"{NAMES[lang][f]}  {num(w[f][2024], lang)}", (2024, w[f][2024]), xytext=(2024.5, ya[f]), textcoords="data", va="center", fontsize=8.5, color=INK,
                        arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6))
            v = d[f][2024]
            bx.annotate(f"{NAMES[lang][f]}  {'+' if v >= 0 else '−'}{num(abs(v), lang)}", (2024, v), xytext=(2024.5, yb[f]), textcoords="data", va="center", fontsize=8.5, color=INK,
                        arrowprops=dict(arrowstyle="-", color=AXIS, lw=0.6))
        bx.axhline(0, color=INK, lw=0.9)
        ax.set_ylim(0, w.values.max() * 1.1); ax.set_title(L["l"], fontsize=10, color=MUTED, loc="left")
        bx.set_title(L["r"], fontsize=10, color=MUTED, loc="left")
        ax.set_xlim(2010.5, 2030.5); ax.set_xticks(range(2011, 2025, 2)); thousands(ax, lang)
        bx.set_xlim(2016.7, 2028.2); bx.set_xticks(range(2017, 2025))
        bx.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v_, _: ("+" if v_ > 0 else ("−" if v_ < 0 else "")) + num(abs(v_), lang)))
        finish(fig, HERE, f"automobile_fuel_{slug}", lang, L["title"].format(s=sname[lang]), L["sub"], L["note"], bottom=0.18)
    print(scope, d.loc[[2021, 2022, 2024]].astype(int).to_string())
