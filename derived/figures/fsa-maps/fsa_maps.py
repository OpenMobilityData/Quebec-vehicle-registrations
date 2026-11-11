"""Maps by FSA, island of Montréal and Laval (postal codes in H), 2024:
  fsa_map_households   automobiles and light trucks per household (vehicles 2024 inferred type; households 2021 Census)
  fsa_map_age          median age of the vehicles registered (all types; nothing inferred)
Each with an enlargement of the FSAs around rue de Terrebonne. Writes derived/tables/fsa_vehicle_age.csv.
FSA polygons: DMTI Spatial, CanMap Postal Code Suite v2024.3 (under licence, not redistributed; drawn here with credit).
Run:  ~/.venvs/omd/bin/python derived/figures/fsa-maps/fsa_maps.py"""
import os
import sys
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
from matplotlib.patches import Patch
from shapely.geometry import LineString

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

TP = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party"))
g = gpd.read_file(TP / "canmap-v2024.3/CanMapPostalCodeSuitev2024.3/Shapefiles/ForwardSortationAreasRegion.shp")
g = g[g.FSA.str.startswith("H")][["FSA", "geometry"]].rename(columns={"FSA": "fsa"}).to_crs(32188)
v = pd.read_csv(paths.TABLES / "fsa_vehicles_census.csv"); v = v[v.year == 2024]
age = duckdb.connect().execute(f"""
    SELECT fsa, count(*) AS vehicles, median(year - model_year) AS median_age,
           round(100.0 * count(*) FILTER (WHERE year - model_year >= 10) / count(*), 1) AS pct_10_years_or_more
    FROM read_parquet('{paths.PARQUET_DIR}/vehicles_2024.parquet') WHERE fsa IS NOT NULL AND model_year BETWEEN 1900 AND 2025
    GROUP BY 1 ORDER BY 1""").df()
age.to_csv(paths.TABLES / "fsa_vehicle_age.csv", index=False)
c = g.geometry.representative_point()                       # leave out an H code far from the island (H0M)
g = g[(abs(c.x - c.x.median()) < 45000) & (abs(c.y - c.y.median()) < 45000)]
g = g.merge(v[["fsa", "au_per_household", "households"]], on="fsa", how="left").merge(age, on="fsa", how="left")
g["ok"] = g.households >= 1000
# rue de Terrebonne, west end to Girouard (City géobase points)
lane = gpd.GeoSeries([LineString([(-73.64080, 45.45974), (-73.63784, 45.46354), (-73.63524, 45.46674), (-73.63231, 45.46990),
                                  (-73.62936, 45.47334), (-73.62487, 45.47833)])], crs=4326).to_crs(32188)
RAMP = ["#e3eefb", "#b5d2f5", "#7fb0ec", "#2a78d6", "#0d366b"]       # one hue, light to dark
ZOOM = ["H4A", "H4B", "H4V", "H3X", "H4W", "H4X", "H3W", "H3S", "H3T", "H3V", "H3Y", "H3Z", "H4C", "H4E", "H4G", "H4H"]
MAPS = {
    "fsa_map_households": dict(col="au_per_household", bins=[0.6, 0.9, 1.2, 1.5], dec=2, mask=True,
        en=("Automobiles and light trucks per household, by FSA, 2024", "Island of Montréal and Laval (postal codes beginning with H)",
            ["under 0.6", "0.6 to 0.9", "0.9 to 1.2", "1.2 to 1.5", "1.5 or more"], "fewer than 1,000 households", "rue de Terrebonne bike lane",
            "Vehicles: 2024 file, type inferred from make, model and model year; all owners, businesses included. Households: 2021 Census, dissemination areas shared among FSAs by postal codes. "
            "FSA boundaries: DMTI Spatial, CanMap Postal Code Suite v2024.3. Statistics Canada, catalogue 98-401-X2021006."),
        fr=("Automobiles et camions légers par ménage, selon la RTA, 2024", "Île de Montréal et Laval (codes postaux commençant par H)",
            ["moins de 0,6", "0,6 à 0,9", "0,9 à 1,2", "1,2 à 1,5", "1,5 ou plus"], "moins de 1 000 ménages", "piste cyclable de la rue de Terrebonne",
            "Véhicules : fichier de 2024, type inféré de la marque, du modèle et de l’année du modèle ; tous les propriétaires, entreprises comprises. Ménages : Recensement de 2021, aires de diffusion réparties entre les RTA selon les codes postaux. "
            "Limites des RTA : DMTI Spatial, CanMap Postal Code Suite v2024.3. Statistique Canada, no 98-401-X2021006 au catalogue.")),
    "fsa_map_age": dict(col="median_age", bins=[6, 7, 8, 9], dec=0, mask=False,
        en=("Median age of registered vehicles, by FSA, 2024", "Island of Montréal and Laval (postal codes beginning with H); all vehicle types; age = 2024 minus model year",
            ["5 years or less", "6 years", "7 years", "8 years", "9 years or more"], "fewer than 1,000 vehicles", "rue de Terrebonne bike lane",
            "Nothing is inferred: the 2024 file carries the model year and the FSA. All owners, businesses included. FSA boundaries: DMTI Spatial, CanMap Postal Code Suite v2024.3."),
        fr=("Âge médian des véhicules immatriculés, selon la RTA, 2024", "Île de Montréal et Laval (codes postaux commençant par H) ; tous les types de véhicules ; âge = 2024 moins l’année du modèle",
            ["5 ans ou moins", "6 ans", "7 ans", "8 ans", "9 ans ou plus"], "moins de 1 000 véhicules", "piste cyclable de la rue de Terrebonne",
            "Rien n’est inféré : le fichier de 2024 donne l’année du modèle et la RTA. Tous les propriétaires, entreprises comprises. Limites des RTA : DMTI Spatial, CanMap Postal Code Suite v2024.3.")),
}
for stem, M in MAPS.items():
    d = g.copy()
    d["shown"] = d.ok if M["mask"] else (d.vehicles >= 1000)
    d["cls"] = pd.cut(d[M["col"]], [-1e9] + [b - 1e-9 for b in M["bins"]] + [1e9], labels=False)
    for lang in ("en", "fr"):
        title, sub, labels, small, lane_lab, note = M[lang]
        fig = plt.figure(figsize=(11, 6.6))
        ax = fig.add_axes([0.0, 0.09, 0.60, 0.78]); zx = fig.add_axes([0.61, 0.27, 0.38, 0.58])
        for a, part, lw in ((ax, d, 0.35), (zx, d[d.fsa.isin(ZOOM)], 0.8)):
            sh = part[part.shown & part.cls.notna()]
            sh.plot(ax=a, color=[RAMP[int(c)] for c in sh.cls], edgecolor=SURFACE, linewidth=lw)
            part[~(part.shown & part.cls.notna())].plot(ax=a, color="#eceeef", edgecolor="#c9cdd2", linewidth=lw, hatch="////")
            lane.plot(ax=a, color=ORANGE, linewidth=2.2 if a is zx else 1.4, zorder=5)
            a.set_axis_off(); a.set_aspect("equal")
        zb = d[d.fsa.isin(["H4A", "H4B", "H4V", "H3X", "H4W", "H4X"])].total_bounds
        pad = 600
        zx.set_xlim(zb[0] - pad, zb[2] + pad); zx.set_ylim(zb[1] - pad, zb[3] + pad)
        ax.add_patch(plt.Rectangle((zb[0] - pad, zb[1] - pad), zb[2] - zb[0] + 2 * pad, zb[3] - zb[1] + 2 * pad, fill=False, ec=INK, lw=1, zorder=6))
        for sp in zx.spines.values(): sp.set_visible(True)
        zx.set_axis_on(); zx.set_xticks([]); zx.set_yticks([]); zx.grid(False); zx.set_xlabel(""); zx.set_ylabel("")
        for sp in zx.spines.values(): sp.set_visible(True); sp.set_color(INK); sp.set_linewidth(1)
        for r in d[d.fsa.isin(ZOOM)].itertuples():
            p0 = r.geometry.representative_point()
            if zb[0] - pad < p0.x < zb[2] + pad and zb[1] - pad < p0.y < zb[3] + pad:
                val = "" if not (r.shown and pd.notna(r.cls)) else "\n" + num(getattr(r, M["col"]), lang, M["dec"])
                dark = r.shown and pd.notna(r.cls) and r.cls >= 3
                zx.text(p0.x, p0.y, r.fsa + val, ha="center", va="center", fontsize=8.5, color=SURFACE if dark else INK,
                        fontweight="bold" if r.fsa in ("H4A", "H4B") else "normal", zorder=7)
        hs = [Patch(fc=c, ec=SURFACE, label=l) for c, l in zip(RAMP, labels)] + [Patch(fc="#eceeef", ec="#c9cdd2", hatch="////", label=small),
              plt.Line2D([0], [0], color=ORANGE, lw=2.2, label=lane_lab)]
        fig.legend(handles=hs, loc="lower left", bbox_to_anchor=(0.605, 0.085), fontsize=8.5, ncol=2, handlelength=1.4, columnspacing=1.2)
        fig.text(0.012, 0.975, title, fontsize=13, fontweight="bold", va="top")
        fig.text(0.012, 0.915, sub, fontsize=10, color=MUTED, va="top")
        fig.text(0.012, 0.012, note + "\n" + SRC[lang], fontsize=7.5, color=MUTED, va="bottom", wrap=True)
        for ext in ("png", "svg"):
            fig.savefig(HERE / f"{stem}_{lang}.{ext}", dpi=200)
        plt.close(fig)
print(g[g.fsa.isin(["H4A", "H4B", "H4V", "H3X"])][["fsa", "au_per_household", "median_age", "pct_10_years_or_more", "vehicles"]].to_string(index=False))
print(g.median_age.describe().round(1).to_dict(), "FSAs:", len(g))
