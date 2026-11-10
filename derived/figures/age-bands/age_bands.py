"""Vehicles registered in the municipality of Montréal by age (year of the file minus model year),
2011-2024. Age needs only the model year, which both sources carry, so nothing here is inferred.
Writes derived/tables/age_bands_montreal.csv.
Run:  ~/.venvs/omd/bin/python derived/figures/age-bands/age_bands.py"""
import sys
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
from fig_lib import *  # noqa: E402,F403

con = duckdb.connect()
d = con.execute(f"""
    SELECT year, CASE WHEN model_year IS NULL OR model_year < 1900 OR year - model_year < -1 THEN 'not stated'
                      WHEN year - model_year <= 5 THEN '5 years or less' WHEN year - model_year <= 10 THEN '6 to 10 years'
                      WHEN year - model_year <= 15 THEN '11 to 15 years' ELSE '16 years or more' END AS band, count(*) n
    FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')
    WHERE muni_code = '66023' OR (source = 'access' AND muni_name = 'Montréal' AND region_code = 6)
    GROUP BY ALL ORDER BY 1, 2""").df()
w = d.pivot(index="year", columns="band", values="n").fillna(0).astype(int)
BANDS = ["5 years or less", "6 to 10 years", "11 to 15 years", "16 years or more"]
w[BANDS + [c for c in w.columns if c not in BANDS]].to_csv(paths.TABLES / "age_bands_montreal.csv")
# the SAAQAnalyzer legend of 2025 for 2024
# (its 16-and-over band, 111,556, counted 58 vehicles whose model year is 0 or two digits; here they are « not stated »)
assert [int(w.loc[2024, b]) for b in BANDS[:3]] == [282933, 240376, 196337], w.loc[2024].to_dict()
assert int(w.loc[2024, BANDS[3]]) + int(w.loc[2024, "not stated"]) - 3 == 111556, w.loc[2024].to_dict()
FR = dict(zip(BANDS, ["5 ans ou moins", "6 à 10 ans", "11 à 15 ans", "16 ans ou plus"]))
COL = dict(zip(BANDS, [BLUE, ORANGE, AQUA, VIOLET]))
T = {
    "en": dict(title="Vehicles registered in the municipality of Montréal by age, 2011–2024",
               sub="All vehicle types; age = year of the SAAQ's file minus model year (the newest band includes next year's models)",
               mark="2023–2024: files released\nunder the access Act",
               note=f"Nothing is inferred: both sources carry the model year. Vehicles with no usable model year: {num(w['not stated'].min(), 'en')} to "
                    f"{num(w['not stated'].max(), 'en')} a year, not shown."),
    "fr": dict(title="Véhicules immatriculés dans la municipalité de Montréal selon l’âge, 2011–2024",
               sub="Tous les types de véhicules ; âge = année du fichier de la SAAQ moins l’année du modèle (la tranche la plus récente comprend les modèles de l’année suivante)",
               mark="2023–2024 : fichiers communiqués\nen vertu de la Loi sur l’accès",
               note=f"Rien n’est inféré : les deux sources donnent l’année du modèle. Véhicules sans année de modèle utilisable : de {num(w['not stated'].min(), 'fr')} à "
                    f"{num(w['not stated'].max(), 'fr')} par an, non représentés."),
}
for lang, L in T.items():
    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.axvspan(2022.5, 2024.5, color="#eef1f4", lw=0, zorder=0)
    ax.text(2023.5, 372000, L["mark"], fontsize=8, color=MUTED, ha="center", va="top")
    for b in BANDS:
        ax.plot(w.index, w[b], color=COL[b], lw=2, marker="o", ms=4.5)
        lab = b if lang == "en" else FR[b]
        ax.annotate(f"{lab}\n{num(w.loc[2024, b], lang)}", (2024, w.loc[2024, b]), xytext=(9, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK)
        ax.annotate(num(w.loc[2011, b], lang), (2011, w.loc[2011, b]), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=8.5, color=INK)
    ax.set_ylim(0, 380000); ax.set_xlim(2010.5, 2026.2); ax.set_xticks(range(2011, 2025))
    thousands(ax, lang)
    finish(fig, HERE, "age_bands", lang, L["title"], L["sub"], L["note"], bottom=0.14)
print(w.loc[[2011, 2022, 2023, 2024]].to_string())
