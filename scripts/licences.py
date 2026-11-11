"""Driver's licence holders, 2011-2022: SAAQ open data « Permis de conduire » (CC BY 4.0), one row per holder
as of June 1 of each year (the vehicle files are as of December 31). Twelve files in one format; nothing is inferred.

Geography: the MRC and the administrative region of residence. There is no municipality: the MRC « Montréal (66) »
is the whole island (the City and the fifteen other municipalities).

Outputs: one Parquet file per year beside the vehicle files (licences_<year>.parquet), and in derived/tables/:
  licence_holders_by_mrc.csv     holders by year and MRC: licence (regular or probationary), learner's permit only,
                                 class 5 (passenger vehicle), class 6 (motorcycle)
  licence_holders_by_age.csv     holders of a licence by year, age band and sex, Québec and the island of Montréal
  vehicles_per_licence.csv       automobiles and light trucks registered per 100 holders of a class 5 licence
Run:  ~/.venvs/omd/bin/python scripts/licences.py [--force]
"""
import os
import sys
from pathlib import Path

import duckdb
import pandas as pd

import paths

LIC_DIR = Path(os.environ.get("SAAQ_LICENCE_DIR", "/Volumes/Pegasus32 R8/SAAQ/Permis_Conduire"))
YEARS = range(2011, 2023)
pq = lambda y: paths.PARQUET_DIR / f"licences_{y}.parquet"


def ingest(con, y):
    src = LIC_DIR / f"Permis_Conduire_{y}.csv"
    con.execute(f"""
        COPY (SELECT CAST(AN AS INTEGER) AS year, AGE_1ER_JUIN AS age_band, SEXE AS sex,
                     nullif(regexp_extract(MRC, '\\(([^)]*?)\\s*\\)', 1), '') AS mrc_code,
                     nullif(trim(regexp_replace(MRC, '\\s*\\(.*$', '')), '') AS mrc_name,
                     TRY_CAST(regexp_extract(REG_ADM, '\\((\\d+)\\s*\\)', 1) AS INTEGER) AS region_code,
                     TYPE_PERMIS AS licence_type,
                     IND_PERMISAPPRENTI_123 = 'OUI' AS learner_123, IND_PERMISAPPRENTI_5 = 'OUI' AS learner_5,
                     IND_PERMISAPPRENTI_6A6R = 'OUI' AS learner_6, IND_PERMISCONDUIRE_1234 = 'OUI' AS class_1234,
                     IND_PERMISCONDUIRE_5 = 'OUI' AS class_5, IND_PERMISCONDUIRE_6ABCE = 'OUI' AS class_6,
                     IND_PERMISCONDUIRE_6D = 'OUI' AS class_6d, IND_PERMISCONDUIRE_8 = 'OUI' AS class_8,
                     IND_PROBATOIRE = 'OUI' AS probationary, EXPERIENCE_GLOBALE AS experience
              FROM read_csv('{src}', all_varchar=true, header=true, encoding='latin-1'))
        TO '{pq(y)}' (FORMAT parquet, COMPRESSION zstd)""")


def main():
    con = duckdb.connect()
    for y in YEARS:
        if "--force" in sys.argv or not pq(y).exists():
            ingest(con, y); print("written", pq(y).name, flush=True)
    con.execute(f"CREATE VIEW l AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/licences_*.parquet')")
    if "--explore" in sys.argv:
        for c in ("licence_type", "age_band", "sex", "experience"):
            print(c, con.execute(f"SELECT {c}, count(*) FROM l WHERE year=2022 GROUP BY 1 ORDER BY 1").fetchall())
        print(con.execute("SELECT year, count(*) n, count(*) FILTER (WHERE licence_type <> 'APPRENTI') lic, count(*) FILTER (WHERE class_5) c5, "
                          "count(*) FILTER (WHERE class_5 AND licence_type <> 'APPRENTI') c5lic, count(*) FILTER (WHERE mrc_code IS NULL) nomrc FROM l GROUP BY 1 ORDER BY 1").df().to_string(index=False))
        print(con.execute("SELECT mrc_code, any_value(mrc_name), count(*) FROM l WHERE year=2022 AND region_code IN (6, 13) GROUP BY 1").fetchall())
        return
    # A licence that allows driving a passenger vehicle: a regular licence of class 5, or a probationary licence. The files
    # give no class for probationary licences (« peu importe la classe »); they are counted here as passenger-vehicle licences.
    CAR = "(licence_type = 'PROBATOIRE' OR (licence_type <> 'APPRENTI' AND class_5))"
    m = con.execute(f"""
        SELECT year, mrc_code, any_value(mrc_name) AS mrc_name, count(*) FILTER (WHERE licence_type <> 'APPRENTI') AS licence_holders,
               count(*) FILTER (WHERE licence_type = 'APPRENTI') AS learners_only, count(*) FILTER (WHERE {CAR}) AS car_licence_holders,
               count(*) FILTER (WHERE class_6 AND licence_type <> 'APPRENTI') AS motorcycle_licence_holders
        FROM l GROUP BY 1, 2 ORDER BY 1, 2""").df()
    m.to_csv(paths.TABLES / "licence_holders_by_mrc.csv", index=False)
    a = con.execute(f"""
        SELECT year, 'Québec' AS scope, age_band, sex, count(*) AS car_licence_holders FROM l WHERE {CAR} GROUP BY ALL
        UNION ALL
        SELECT year, 'Island of Montréal (MRC 66)', age_band, sex, count(*) FROM l WHERE {CAR} AND mrc_code = '66' GROUP BY ALL
        ORDER BY ALL""").df()
    a.to_csv(paths.TABLES / "licence_holders_by_age.csv", index=False)
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet') WHERE source = 'open'")
    veh = con.execute("""
        SELECT year, 'Québec' AS scope, count(*) FILTER (WHERE vtype = 'AU') AS automobiles_light_trucks, count(*) AS vehicles_all_types FROM v GROUP BY 1
        UNION ALL
        SELECT year, 'Island of Montréal (MRC 66)', count(*) FILTER (WHERE vtype = 'AU'), count(*) FROM v WHERE mrc_code = '66' GROUP BY 1""").df()
    lic = pd.concat([m.groupby("year").car_licence_holders.sum().reset_index().assign(scope="Québec"),
                     m[m.mrc_code == "66"][["year", "car_licence_holders"]].assign(scope="Island of Montréal (MRC 66)")])
    r = veh.merge(lic, on=["year", "scope"]).sort_values(["scope", "year"])
    r["automobiles_per_100_car_licence_holders"] = (100 * r.automobiles_light_trucks / r.car_licence_holders).round(2)
    r.to_csv(paths.TABLES / "vehicles_per_licence.csv", index=False)
    pd.set_option("display.width", 200)
    print(r[r.year.isin([2011, 2016, 2019, 2021, 2022])].to_string(index=False))
    g = a[a.scope.str.startswith("Island")].groupby(["year", "age_band"]).car_licence_holders.sum().unstack()
    print(g.loc[[2011, 2016, 2022]].to_string())


if __name__ == "__main__":
    main()
