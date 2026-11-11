"""Stage 7: the 2011-2021 trend carried forward, set beside what the files show.

Nothing here is a forecast. A straight line is fitted to the published counts of automobiles and light trucks in the
municipality of Montréal for 2011-2021 (the last year before the published count fell) and carried forward (to 2050 in the table). Beside it:
the published count for 2022 and the inferred counts for 2023 and 2024. The same is done for the mean net mass
(2011-2022, the only years with mass).

Storage. A registered vehicle is somewhere when it is not moving. The table converts a number of vehicles into a
length of curb at 5.0, 5.5 and 6.0 m per vehicle: an assumption stated as a range, not a measurement, and it applies
only to the vehicles kept on the street (the files do not say which are).

Outputs (derived/tables/): trend_scenario.csv, storage_equivalents.csv, vehicles_per_1000_residents.csv
Run:  ~/.venvs/omd/bin/python scripts/scenarios.py
"""
import os
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

import paths

CSD = Path(os.environ.get("THIRD_PARTY", Path.home() / "Terrebonne-data/third-party")) / \
    "statcan-census-2021/98-401-X2021020_QC_CSD/98-401-X2021020_English_CSV_data.csv"


def main():
    t = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
    au = t[(t.muni_code == "66023") & (t.vtype == "AU")].set_index("year").n
    fit = au.loc[2011:2021]
    b, a = np.polyfit(fit.index, fit.values, 1)
    resid = fit.values - (a + b * fit.index.values)
    rows = []
    for y in range(2011, 2051):
        rows.append({"year": y, "trend_2011_2021": round(a + b * y), "count": round(au[y]) if y in au.index else None,
                     "basis": "published" if y <= 2022 else ("inferred" if y <= 2024 else ""),
                     "count_minus_trend": round(au[y] - (a + b * y)) if y in au.index else None})
    sc = pd.DataFrame(rows); sc.to_csv(paths.TABLES / "trend_scenario.csv", index=False)
    m = pd.read_csv(paths.TABLES / "mass_automobiles.csv"); m = m[m.scope == "Montréal"].set_index("year").mean_kg
    mb, ma = np.polyfit(m.index, m.values, 1)

    f = pd.read_csv(paths.TABLES / "fsa_vehicles_census.csv"); f = f[f.year == 2024].set_index("fsa")
    local = f.loc[["H4A", "H4B"], "automobiles_light_trucks_inferred"].sum()
    rate = b / fit.mean()                                     # yearly growth as a share of the 2011-2021 mean
    cases = [("Montréal, published increase 2011 to 2021", au[2021] - au[2011]),
             ("Montréal, 2024 (inferred) minus 2021", au[2024] - au[2021]),
             ("Montréal, trend 2011-2021 carried from 2024 to 2034 (10 years)", 10 * b),
             ("H4A and H4B, if the City's 2011-2021 yearly rate applied for 10 years", local * rate * 10),
             ("Per 1,000 vehicles", 1000)]
    st = pd.DataFrame([{"case": c, "vehicles": round(v), **{f"curb_km_at_{l}_m": round(v * l / 1000, 1) for l in (5.0, 5.5, 6.0)}} for c, v in cases])
    st.to_csv(paths.TABLES / "storage_equivalents.csv", index=False)

    pop = duckdb.connect().execute(f"""SELECT CHARACTERISTIC_ID AS id, TRY_CAST(C1_COUNT_TOTAL AS DOUBLE) AS v
        FROM read_csv('{CSD}', all_varchar=true, encoding='latin-1', header=true) WHERE ALT_GEO_CODE='2466023' AND CHARACTERISTIC_ID IN ('1','2')""").df().set_index("id").v
    pr = pd.DataFrame([{"year": y, "population_census": int(pop[i]), "automobiles_light_trucks": int(au[y]),
                        "per_1000_residents": round(1000 * au[y] / pop[i], 1)} for y, i in ((2016, "2"), (2021, "1"))])
    pr.to_csv(paths.TABLES / "vehicles_per_1000_residents.csv", index=False)

    pd.set_option("display.width", 220); pd.set_option("display.max_colwidth", 80)
    print(f"trend: {b:,.0f} vehicles a year ({100 * rate:.2f} % of the 2011-2021 mean); residual sd {resid.std(ddof=2):,.0f}")
    print(sc[sc.year.isin([2021, 2022, 2023, 2024, 2030, 2035])].to_string(index=False))
    print(f"mean mass trend: {mb:.1f} kg a year; 2022 {m[2022]:.0f}; trend 2030 {ma + mb * 2030:.0f}, 2035 {ma + mb * 2035:.0f}")
    print(st.to_string(index=False)); print(pr.to_string(index=False))


if __name__ == "__main__":
    main()
