"""Stage 5: the yearly series behind the charts, and their check against the legends of the 2025
SAAQAnalyzer charts.

Outputs (derived/tables/):
  vehicles_by_municipality.csv     all vehicles, every municipality, 2011-2024 (nothing inferred)
  age_bands_by_municipality.csv    all vehicles by age band, every municipality, 2011-2024 (nothing inferred)
  type_by_year_quebec.csv          Québec by type, 2011-2024 (2023-2024 inferred)
  reproduction_checks.csv          legend values of the 2025 charts against this pipeline
Run:  ~/.venvs/omd/bin/python scripts/series.py
"""
import duckdb
import pandas as pd

import paths

BANDS = ["5 years or less", "6 to 10 years", "11 to 15 years", "16 years or more", "not stated"]


def main():
    con = duckdb.connect()
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')")
    con.execute(f"CREATE VIEW mmap AS SELECT * FROM read_parquet('{paths.PARQUET_DIR.parent}/municipality_match.parquet')")
    con.execute("""CREATE TABLE b AS
        SELECT a.year, coalesce(a.muni_code, m.muni_code) AS muni_code,
               CASE WHEN a.model_year IS NULL OR a.model_year < 1900 OR a.year - a.model_year < -1 THEN 'not stated'
                    WHEN a.year - a.model_year <= 5 THEN '5 years or less' WHEN a.year - a.model_year <= 10 THEN '6 to 10 years'
                    WHEN a.year - a.model_year <= 15 THEN '11 to 15 years' ELSE '16 years or more' END AS band, count(*) AS n
        FROM v a LEFT JOIN mmap m ON a.source = 'access' AND m.muni_name IS NOT DISTINCT FROM a.muni_name
                                   AND m.region_code IS NOT DISTINCT FROM a.region_code
        GROUP BY ALL""")
    names = pd.read_csv(paths.TABLES / "municipalities.csv", dtype=str)[["muni_code", "muni_name"]]
    ab = con.execute("SELECT * FROM b WHERE muni_code IS NOT NULL ORDER BY ALL").df().merge(names, on="muni_code", how="left")
    ab[["year", "muni_code", "muni_name", "band", "n"]].to_csv(paths.TABLES / "age_bands_by_municipality.csv", index=False)
    tot = ab.groupby(["year", "muni_code", "muni_name"], dropna=False).n.sum().reset_index()
    tot.to_csv(paths.TABLES / "vehicles_by_municipality.csv", index=False)

    t = pd.read_csv(paths.TABLES / "type_by_municipality.csv", dtype={"muni_code": str})
    q = t.groupby(["year", "vtype", "basis"], dropna=False).n.sum().round(0).reset_index()
    q.to_csv(paths.TABLES / "type_by_year_quebec.csv", index=False)

    def total(codes, year):
        return int(tot[tot.muni_code.isin(codes) & (tot.year == year)].n.sum())

    def band(code, year, b):
        return int(ab[(ab.muni_code == code) & (ab.year == year) & (ab.band == b)].n.sum())

    def typ(year, vt, code=None):
        d = t[(t.year == year) & (t.vtype == vt)]
        return int(round((d[d.muni_code == code] if code else d).n.sum()))

    enclaves = ["66062", "66047", "66058", "66032"]
    checks = [
        ("Hampstead, Montréal-Ouest, Côte-Saint-Luc and Westmount, all vehicles, 2024", 34252, total(enclaves, 2024)),
        ("Montréal-Ouest, 5 years or less, 2024", 1200, band("66047", 2024, BANDS[0])),
        ("Montréal-Ouest, 6 to 10 years, 2024", 820, band("66047", 2024, BANDS[1])),
        ("Montréal-Ouest, 11 to 15 years, 2024", 542, band("66047", 2024, BANDS[2])),
        ("Montréal-Ouest, 16 years or more, 2024", 310, band("66047", 2024, BANDS[3])),
        ("Montréal, 5 years or less, 2024", 282933, band("66023", 2024, BANDS[0])),
        ("Montréal, 16 years or more, 2024 (the app counted 58 vehicles with an invalid model year here)", 111556,
         band("66023", 2024, BANDS[3])),
        ("Montréal, all vehicles, 2024", 831205, total(["66023"], 2024)),
        ("Montréal, automobiles and light trucks, 2022", 743494, typ(2022, "AU", "66023")),
        ("Montréal, trucks and road tractors (type CA), 2022", 24352, typ(2022, "CA", "66023")),
        ("Québec, snowmobiles, 2022", 237201, typ(2022, "MN")),
        ("Québec, mopeds, 2022", 37511, typ(2022, "CY")),
    ]
    c = pd.DataFrame(checks, columns=["chart_legend", "app_2025", "pipeline"])
    c["difference"] = c.pipeline - c.app_2025
    c.to_csv(paths.TABLES / "reproduction_checks.csv", index=False)
    pd.set_option("display.width", 200); pd.set_option("display.max_colwidth", 90)
    print(c.to_string(index=False))
    e = tot[tot.muni_code.isin(enclaves)].pivot_table(index="year", columns="muni_name", values="n", aggfunc="sum")
    e["total"] = e.sum(axis=1); print(e.astype(int).to_string())
    print(q[q.vtype.isin(["MN", "CY"]) & (q.year >= 2019)].pivot_table(index="year", columns="vtype", values="n").to_string())


if __name__ == "__main__":
    main()
