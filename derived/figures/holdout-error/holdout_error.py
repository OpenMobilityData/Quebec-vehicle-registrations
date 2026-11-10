"""How far the inferred count of automobiles and light trucks falls from the published count, for each
published year inferred from the years before it. Reads derived/tables/holdout_summary.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/holdout-error/holdout_error.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

h = pd.read_csv(paths.TABLES / "holdout_summary.csv")
h = h[(h.target == "vtype") & (h.value == "AU")]
T = {
    "en": dict(title="Inferring vehicle type from make, model and model year: error on published years",
               sub="Automobiles and light trucks: inferred count against the count the SAAQ published, in per cent",
               scopes={"Montréal": "Municipality of Montréal", "Québec": "Québec, all municipalities"},
               l1="inferred from the three years ending one year earlier (as 2023 from 2020–2022)",
               l2="inferred from the three years ending two years earlier (as 2024 from 2020–2022)",
               note="Each published year is reduced to the seven columns of the 2023–2024 files, inferred, and compared with the published "
                    "type. The test uses the open data's own make and model codes; it does not measure the effect of the unedited codes of 2023–2024."),
    "fr": dict(title="Inférer le type de véhicule de la marque, du modèle et de l’année : erreur sur les années publiées",
               sub="Automobiles et camions légers : nombre inféré par rapport au nombre publié par la SAAQ, en pourcentage",
               scopes={"Montréal": "Municipalité de Montréal", "Québec": "Québec, toutes les municipalités"},
               l1="inféré des trois années se terminant un an plus tôt (comme 2023 à partir de 2020–2022)",
               l2="inféré des trois années se terminant deux ans plus tôt (comme 2024 à partir de 2020–2022)",
               note="Chaque année publiée est réduite aux sept colonnes des fichiers de 2023–2024, inférée, puis comparée au type publié. "
                    "L’essai utilise les codes de marque et de modèle des données ouvertes ; il ne mesure pas l’effet des codes non révisés de 2023–2024."),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.9), sharey=True)
    for ax, scope in zip(axes, ("Montréal", "Québec")):
        d = h[h.scope == scope]
        ax.axhline(0, color=INK, lw=1)
        a, b = d[d.lead == 1], d[d.lead == 2]
        ax.plot(a.year, a.pct_error, ls="none", marker="o", ms=7, color=BLUE, label=L["l1"])
        ax.plot(b.year, b.pct_error, ls="none", marker="o", ms=7, mfc=SURFACE, mec=BLUE, mew=1.8, label=L["l2"])
        ax.set_title(L["scopes"][scope], fontsize=10, color=MUTED, loc="left")
        ax.set_xticks(range(2012, 2023, 2)); ax.set_ylim(-0.5, 0.5)
        ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: "0" if abs(v) < 1e-9 else pct(v, lang, 1)))
    fig.legend(*axes[0].get_legend_handles_labels(), loc="lower left", bbox_to_anchor=(0.06, 0.115), fontsize=9, ncol=1)
    finish(fig, HERE, "holdout_error", lang, L["title"], L["sub"], L["note"], bottom=0.3)
