"""Electric, plug-in hybrid and hybrid vehicles registered, 2011-2024: Québec and the municipality of Montréal.
Published counts for 2017-2022 (the fuel column begins in 2017 and the 2023-2024 files carry none); inferred from
make, model and model year before 2017 (from the files of 2017-2019) and after 2022 (from those of 2020-2022).
Reads fuel_by_municipality.csv, fuel_inferred_before_2017.csv, holdout_summary.csv, holdout_backward.csv;
writes derived/tables/electrified_by_year.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/electric/electric.py"""
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

f = pd.read_csv(paths.TABLES / "fuel_by_municipality.csv", dtype={"muni_code": str})
bw = pd.read_csv(paths.TABLES / "fuel_inferred_before_2017.csv")
rows = []
for scope, d in (("Québec", f), ("Montréal", f[f.muni_code == "66023"])):
    for code in ("L", "W", "H"):
        s = d[d.fuel == code].groupby(["year", "basis"]).n.sum().reset_index()
        rows += [{"scope": scope, "year": r.year, "fuel": code, "vehicles": round(r.n), "basis": "published" if r.basis == "released" else "inferred"} for r in s.itertuples()]
        b = bw[(bw.scope == scope) & (bw.fuel == code)]
        rows += [{"scope": scope, "year": r.year, "fuel": code, "vehicles": round(r.n), "basis": "inferred"} for r in b.itertuples()]
t = pd.DataFrame(rows).sort_values(["scope", "fuel", "year"]); t.to_csv(paths.TABLES / "electrified_by_year.csv", index=False)
h = pd.read_csv(paths.TABLES / "holdout_summary.csv"); h = h[(h.target == "fuel") & (h.scope == "Québec")].rename(columns={"value": "fuel"})
hb = pd.read_csv(paths.TABLES / "holdout_backward.csv"); hb = hb[hb.scope == "Québec"]


def rng(d, v, lang):
    e = d[d.fuel == v].pct_error
    return f"{pct(e.min(), lang, 0)} {'to' if lang == 'en' else 'à'} {pct(e.max(), lang, 0)}"


NAMES = {"en": {"L": "Electric", "W": "Plug-in hybrid", "H": "Hybrid"}, "fr": {"L": "Électrique", "W": "Hybride branchable", "H": "Hybride"}}
COL = {"L": BLUE, "W": ORANGE, "H": AQUA}
T = {
    "en": dict(title="Electric and hybrid vehicles registered, 2011–2024", sub="Solid: published counts, 2017–2022. Dashed with hollow points: inferred from make, model and model year.",
               scopes={"Québec": "Québec", "Montréal": "Municipality of Montréal"},
               note=f"The fuel column begins in 2017, and the files of 2023–2024 carry none. Tested on published years for Québec, the inference forward (2023–2024) differs from the published count by {rng(h, 'L', 'en')} for electric, "
                    f"{rng(h, 'W', 'en')} for plug-in hybrid and {rng(h, 'H', 'en')} for hybrid, mostly low; backward (before 2017), tested up to three years back, by {rng(hb, 'L', 'en')}, {rng(hb, 'W', 'en')} and {rng(hb, 'H', 'en')}. "
                    "2011–2016 lie up to six years before the files used, beyond what the test covers. Each panel has its own scale, from zero."),
    "fr": dict(title="Véhicules électriques et hybrides immatriculés, 2011–2024", sub="Trait plein : nombres publiés, 2017–2022. Tirets et points creux : inférés de la marque, du modèle et de l’année du modèle.",
               scopes={"Québec": "Québec", "Montréal": "Municipalité de Montréal"},
               note=f"La colonne du carburant commence en 2017, et les fichiers de 2023–2024 n’en ont pas. Mise à l’essai sur les années publiées pour le Québec, l’inférence vers l’avant (2023–2024) s’écarte du nombre publié de {rng(h, 'L', 'fr')} pour l’électrique, "
                    f"de {rng(h, 'W', 'fr')} pour l’hybride branchable et de {rng(h, 'H', 'fr')} pour l’hybride, surtout à la baisse ; vers l’arrière (avant 2017), jusqu’à trois ans en arrière, de {rng(hb, 'L', 'fr')}, {rng(hb, 'W', 'fr')} et {rng(hb, 'H', 'fr')}. "
                    "Les années 2011–2016 précèdent de jusqu’à six ans les fichiers utilisés, au-delà de ce que l’essai couvre. Chaque panneau a sa propre échelle, à partir de zéro."),
}
for lang, L in T.items():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5.2))
    for ax, scope in zip(axes, ("Québec", "Montréal")):
        d = t[t.scope == scope]
        ax.axvspan(2016.5, 2022.5, color="#f3f5f6", lw=0, zorder=0)
        for code in ("L", "W", "H"):
            s = d[d.fuel == code].set_index("year").vehicles
            ax.plot(s.loc[2017:2022].index, s.loc[2017:2022].values, color=COL[code], lw=2, marker="o", ms=4.5)
            for seg in (s.loc[:2017], s.loc[2022:]):
                ax.plot(seg.index, seg.values, color=COL[code], lw=1.6, ls=(0, (3, 2)))
            hol = pd.concat([s.loc[:2016], s.loc[2023:]])
            ax.plot(hol.index, hol.values, ls="none", marker="o", ms=5.5, mfc=SURFACE, mec=COL[code], mew=1.6)
            ax.annotate(f"{NAMES[lang][code]}\n{num(s[2024], lang)}", (2024, s[2024]), xytext=(9, 0), textcoords="offset points", va="center", fontsize=9, color=INK)
        e = d[d.fuel == "L"].set_index("year").vehicles
        ax.text(2011, d.vehicles.max() * 1.1, f"{NAMES[lang]['L']}: {num(e[2011], lang)} (2011), {num(e[2017], lang)} (2017), {num(e[2022], lang)} (2022)", fontsize=8.5, color=INK, va="top")
        ax.set_ylim(0, d.vehicles.max() * 1.12); ax.set_xlim(2010.5, 2027.9); ax.set_xticks(range(2011, 2025, 2)); thousands(ax, lang)
        ax.set_title(L["scopes"][scope], fontsize=10.5, color=INK, loc="left")
    finish(fig, HERE, "electric", lang, L["title"], L["sub"], L["note"], bottom=0.2)
print(t[t.scope == "Québec"].pivot(index="year", columns="fuel", values="vehicles").to_string())
print(t[t.scope == "Montréal"].pivot(index="year", columns="fuel", values="vehicles").loc[[2011, 2016, 2017, 2022, 2023, 2024]].to_string())
