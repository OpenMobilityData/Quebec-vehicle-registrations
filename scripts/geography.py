"""Stage 4a: one municipality key across the two sources.

The open data (2011-2022) identify the municipality by its geographic code
(CG_FIXE); the 2023-2024 release gives its name and the administrative region.
The link is the Institut de la statistique du Québec's « Banque de données des
codes géographiques » (image of July 31, 2025, file d001; named here, not
redistributed): code, name, designation and region of every municipality.

A name is matched within its region. A name carried by two municipalities of
the same region is left ambiguous and counted, never assigned.

Outputs (derived/tables/): municipalities.csv, municipality_match.csv
Run:  ~/.venvs/omd/bin/python scripts/geography.py
"""
import os
from pathlib import Path

import duckdb
import pandas as pd

import paths

D001 = Path(os.environ.get(
    "ISQ_D001", Path.home() / "Terrebonne-data/third-party/isq-bdcg-2025-07-31/d001_min.txt"))


def read_d001():
    rows = []
    for line in D001.read_text(encoding="latin-1").splitlines():
        if not line.startswith("1"):
            continue
        # fixed width: record type (1), code (5), designation (2), name (58), ..., region code (2) at column 164
        rows.append({"muni_code": line[1:6], "designation": line[6:8].strip(),
                     "muni_name": line[8:66].strip(), "region_code": line[164:166]})
    return pd.DataFrame(rows)


def main():
    m = read_d001()
    mtl = m[m.muni_code == "66023"].iloc[0]
    assert mtl.muni_name == "Montréal" and mtl.region_code == "06", mtl.to_dict()
    m["region_code"] = pd.to_numeric(m.region_code, errors="coerce").astype("Int64")
    m.to_csv(paths.TABLES / "municipalities.csv", index=False)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')")
    acc = con.execute("SELECT muni_name, region_code, sum((year=2023)::INT) n_2023, sum((year=2024)::INT) n_2024 "
                      "FROM v WHERE source='access' GROUP BY ALL").df()
    opn = con.execute("SELECT muni_code, count(*) n_2022 FROM v WHERE year=2022 GROUP BY ALL").df()
    k = m.groupby(["muni_name", "region_code"]).muni_code.agg(["count", "first"]).reset_index()
    j = acc.merge(k, on=["muni_name", "region_code"], how="left")
    j["status"] = "matched"
    j.loc[j["count"].isna(), "status"] = "no such name in the region"
    j.loc[j["count"] > 1, "status"] = "ambiguous"
    j.loc[j.muni_name.isna() | (j.muni_name == ""), "status"] = "no municipality given"
    j["muni_code"] = j["first"].where(j.status == "matched")
    j = j.merge(opn, on="muni_code", how="left")
    j[["muni_name", "region_code", "muni_code", "status", "n_2022", "n_2023", "n_2024"]].sort_values(
        "n_2024", ascending=False).to_csv(paths.TABLES / "municipality_match.csv", index=False)
    j[["muni_name", "region_code", "muni_code"]].to_parquet(paths.PARQUET_DIR.parent / "municipality_match.parquet")
    s = j.groupby("status")[["n_2023", "n_2024"]].sum()
    print((100 * s / s.sum()).round(3).join(j.groupby("status").size().rename("names")))
    print(j[j.status != "matched"].sort_values("n_2024", ascending=False).head(15)[
        ["muni_name", "region_code", "status", "n_2023", "n_2024"]].to_string(index=False))
    big = j[j.status == "matched"].sort_values("n_2024", ascending=False).head(8)
    print(big[["muni_name", "muni_code", "n_2022", "n_2023", "n_2024"]].to_string(index=False))
    print("codes in the 2022 open data absent from the matched release:",
          int(opn[~opn.muni_code.isin(j.muni_code.dropna())].n_2022.sum()), "vehicles")


if __name__ == "__main__":
    main()
