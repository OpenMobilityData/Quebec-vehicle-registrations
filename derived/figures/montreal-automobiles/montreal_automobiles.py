"""Vehicles registered in the municipality of Montréal, 2011-2024: all vehicles (released for every
year) and automobiles and light trucks (type AU: released 2011-2022, inferred 2023-2024).
Reads derived/tables/type_by_municipality.csv and holdout_summary.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/montreal-automobiles/montreal_automobiles.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

t = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
m = t[t.muni_code == "66023"]
allv = m.groupby("year").n.sum()
au = m[m.vtype == "AU"].set_index("year").n
h = pd.read_csv(paths.TABLES / "holdout_summary.csv")
h = h[(h.scope == "Montréal") & (h.value == "AU") & (h.target == "vtype")]
lo, hi = h.pct_error.min(), h.pct_error.max()
unassigned = m[m.vtype.isna()].set_index("year").n

T = {
    "en": dict(title="Vehicles registered in the municipality of Montréal, 2011–2024",
               sub="Number of vehicles authorized to circulate, by year of the SAAQ's file",
               all="All vehicles", au="Automobiles and light trucks", inf="inferred (2023–2024)",
               left="Axis from zero", right="The same, enlarged (the axis does not start at zero)",
               note=f"Type is not in the 2023–2024 files: it is inferred from make, model and model year. Applied to each published year "
                    f"2012–2022 from the years before it, the method gives {pct(lo, 'en')} to {pct(hi, 'en')} against the published count "
                    f"({len(h)} tests). Vehicles left unassigned: {num(unassigned[2023], 'en')} (2023), {num(unassigned[2024], 'en')} (2024)."),
    "fr": dict(title="Véhicules immatriculés dans la municipalité de Montréal, 2011–2024",
               sub="Nombre de véhicules autorisés à circuler, selon l’année du fichier de la SAAQ",
               all="Tous les véhicules", au="Automobiles et camions légers", inf="inféré (2023–2024)",
               left="Axe à partir de zéro", right="Les mêmes, agrandis (l’axe ne part pas de zéro)",
               note=f"Le type ne figure pas dans les fichiers de 2023–2024 : il est inféré de la marque, du modèle et de l’année du modèle. Appliquée "
                    f"à chaque année publiée de 2012 à 2022 à partir des années précédentes, la méthode donne de {pct(lo, 'fr')} à {pct(hi, 'fr')} "
                    f"par rapport au nombre publié ({len(h)} essais). Véhicules non attribués : {num(unassigned[2023], 'fr')} (2023), {num(unassigned[2024], 'fr')} (2024)."),
}

for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    for ax, zoom in zip(axes, (False, True)):
        ax.plot(allv.index, allv.values, color=ORANGE, lw=2, marker="o", ms=4.5, label=L["all"])
        ax.plot(au.loc[:2022].index, au.loc[:2022].values, color=BLUE, lw=2, marker="o", ms=4.5, label=L["au"])
        ax.plot(au.loc[2022:].index, au.loc[2022:].values, color=BLUE, lw=1.6, ls=(0, (3, 2)))
        ax.plot(au.loc[2023:].index, au.loc[2023:].values, ls="none", marker="o", ms=6, mfc=SURFACE, mec=BLUE, mew=1.8,
                label=f"{L['au']}, {L['inf']}")
        ax.set_title(L["right"] if zoom else L["left"], fontsize=9.5, color=MUTED, loc="left")
        ax.set_xticks(range(2011, 2025, 2 if not zoom else 1))
        ax.tick_params(axis="x", labelsize=8.5 if zoom else 10)
        thousands(ax, lang)
        if zoom:
            ax.set_ylim(660000, 850000)
            for s, y, yr in ((allv, 12, 2024), (au, -16, 2024), (au, -16, 2022), (au, 10, 2011), (allv, 10, 2011)):
                ax.annotate(num(s[yr], lang), (yr, s[yr]), xytext=(0, y), textcoords="offset points", ha="center",
                            fontsize=8.5, color=INK)
            ax.set_xlim(2010.3, 2024.9)
        else:
            ax.set_ylim(0, 900000)
            ax.legend(loc="lower left", fontsize=9, handlelength=1.6)
    finish(fig, HERE, "montreal_automobiles", lang, L["title"], L["sub"], L["note"], bottom=0.19)
print(au.round(0).to_string()); print(allv.to_string())
