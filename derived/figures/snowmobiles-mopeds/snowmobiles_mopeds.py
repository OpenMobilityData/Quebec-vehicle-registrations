"""Snowmobiles and mopeds registered in Québec, 2011-2024 (published to 2022; 2023-2024 inferred).
Reads derived/tables/type_by_year_quebec.csv and holdout_summary.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/snowmobiles-mopeds/snowmobiles_mopeds.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

q = pd.read_csv(paths.TABLES / "type_by_year_quebec.csv")
h = pd.read_csv(paths.TABLES / "holdout_summary.csv"); h = h[(h.target == "vtype") & (h.scope == "Québec")]
err = {v: (h[h.value == v].pct_error.min(), h[h.value == v].pct_error.max()) for v in ("MN", "CY")}
T = {
    "en": dict(title="Snowmobiles and mopeds registered in Québec, 2011–2024", sub="Published counts to 2022; hollow points are inferred from make, model and model year",
               names={"MN": "Snowmobiles", "CY": "Mopeds"},
               note=f"On published years the inferred count differs from the published one by {pct(err['MN'][0], 'en')} to {pct(err['MN'][1], 'en')} for snowmobiles and "
                    f"{pct(err['CY'][0], 'en')} to {pct(err['CY'][1], 'en')} for mopeds. Each panel has its own scale, from zero."),
    "fr": dict(title="Motoneiges et cyclomoteurs immatriculés au Québec, 2011–2024", sub="Nombres publiés jusqu’en 2022 ; les points creux sont inférés de la marque, du modèle et de l’année du modèle",
               names={"MN": "Motoneiges", "CY": "Cyclomoteurs"},
               note=f"Sur les années publiées, le nombre inféré s’écarte du nombre publié de {pct(err['MN'][0], 'fr')} à {pct(err['MN'][1], 'fr')} pour les motoneiges et de "
                    f"{pct(err['CY'][0], 'fr')} à {pct(err['CY'][1], 'fr')} pour les cyclomoteurs. Chaque panneau a sa propre échelle, à partir de zéro."),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, vt, col in zip(axes, ("MN", "CY"), (BLUE, ORANGE)):
        s = q[q.vtype == vt].set_index("year").n
        released_inferred(ax, s, col)
        ax.set_ylim(0, s.max() * 1.18); ax.set_xticks(range(2011, 2025, 2)); thousands(ax, lang)
        ax.set_title(L["names"][vt], fontsize=10.5, color=INK, loc="left")
        for yr, dy in ((2011, 9), (2022, 9), (2024, -15)):
            ax.annotate(num(s[yr], lang), (yr, s[yr]), xytext=(0, dy), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
        lo = s.loc[:2022].idxmin()
        if lo not in (2011, 2022):
            ax.annotate(f"{num(s[lo], lang)} ({lo})", (lo, s[lo]), xytext=(0, -15), textcoords="offset points", ha="center", fontsize=8.5, color=INK)
    finish(fig, HERE, "snowmobiles_mopeds", lang, L["title"], L["sub"], L["note"], bottom=0.17)
