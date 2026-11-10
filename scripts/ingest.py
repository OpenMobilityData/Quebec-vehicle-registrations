"""Stage 1: the 14 yearly files -> one Parquet file per year, one schema.

Sources
  2011-2022  SAAQ open data « Véhicules en circulation » (Données Québec, CC BY 4.0),
             files as revised by the SAAQ on December 18, 2023.
  2023-2024  files released by the SAAQ under the access-to-information Act
             (file 03.06.34729): seven columns only.

Nothing is inferred here. A column a source does not carry is NULL, and
`derived/tables/ingest_summary.csv` gives, per year, the share of rows filled
in each column. Raw files are read, never written.

Run:  ~/.venvs/omd/bin/python scripts/ingest.py [--force]
"""
import csv
import hashlib
import sys

import duckdb
import pandas as pd

import paths

SCHEMA = [
    "year", "source", "period_raw", "vclass", "vtype", "make_raw", "model_raw", "model_year",
    "net_mass_kg", "cylinders", "displacement_cc", "max_axles", "colour", "fuel",
    "region_code", "region_name", "mrc_code", "mrc_name", "muni_code", "muni_name", "fsa",
]
# Figures the ingestion must reproduce (rows of each file; legends of the
# SAAQAnalyzer charts of 2025).
EXPECTED = [
    ("rows 2022", "year=2022", 7058605),
    ("rows 2023", "year=2023", 7169989),
    ("rows 2024", "year=2024", 7189594),
    ("Montréal 2023, all vehicles", "year=2023 AND muni_name='Montréal'", 832054),
    ("Montréal 2024, all vehicles", "year=2024 AND muni_name='Montréal'", 831205),
    ("Montréal 2022, automobiles and light trucks (type AU)", "year=2022 AND muni_code='66023' AND vtype='AU'", 743494),
    ("Montréal 2022, class PAU", "year=2022 AND muni_code='66023' AND vclass='PAU'", 656363),
    ("Montréal 2022, class CAU", "year=2022 AND muni_code='66023' AND vclass='CAU'", 86702),
    ("Québec 2022, snowmobiles (type MN)", "year=2022 AND vtype='MN'", 237201),
    ("Québec 2022, mopeds (type CY)", "year=2022 AND vtype='CY'", 37511),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 24):
            h.update(chunk)
    return h.hexdigest()


def ingest_open(con, year):
    src = paths.open_csv(year)
    cols = con.execute(
        "SELECT column_name FROM (DESCRIBE SELECT * FROM read_csv(?, all_varchar=true, header=true))", [str(src)]
    ).fetchall()
    has_fuel = ("TYP_CARBU",) in cols
    fuel = "nullif(trim(TYP_CARBU),'')" if has_fuel else "CAST(NULL AS VARCHAR)"
    con.execute(f"""
        COPY (
          SELECT CAST(AN AS INTEGER) AS year, 'open' AS source, AN AS period_raw,
                 nullif(trim(CLAS),'') AS vclass, nullif(trim(TYP_VEH_CATEG_USA),'') AS vtype,
                 nullif(trim(MARQ_VEH),'') AS make_raw, nullif(trim(MODEL_VEH),'') AS model_raw,
                 TRY_CAST(ANNEE_MOD AS INTEGER) AS model_year,
                 TRY_CAST(MASSE_NETTE AS INTEGER) AS net_mass_kg,
                 nullif(trim(NB_CYL),'') AS cylinders,
                 TRY_CAST(CYL_VEH AS INTEGER) AS displacement_cc,
                 TRY_CAST(NB_ESIEU_MAX AS INTEGER) AS max_axles,
                 nullif(trim(COUL_ORIG),'') AS colour, {fuel} AS fuel,
                 TRY_CAST(regexp_extract(REG_ADM, '\\((\\d+)\\s*\\)', 1) AS INTEGER) AS region_code,
                 nullif(trim(regexp_replace(REG_ADM, '\\s*\\(.*$', '')),'') AS region_name,
                 nullif(regexp_extract(MRC, '\\(([^)]*?)\\s*\\)', 1),'') AS mrc_code,
                 nullif(trim(regexp_replace(MRC, '\\s*\\(.*$', '')),'') AS mrc_name,
                 nullif(trim(CG_FIXE),'') AS muni_code, CAST(NULL AS VARCHAR) AS muni_name,
                 CAST(NULL AS VARCHAR) AS fsa
          FROM read_csv(?, all_varchar=true, header=true)
        ) TO '{paths.parquet(year)}' (FORMAT parquet, COMPRESSION zstd)""", [str(src)])


def _repair(s):
    """The 2023 file mixes Latin-1 with UTF-8 bytes read as Latin-1 (« MontrÃ©al »)."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def ingest_access(con, year):
    d = pd.read_csv(paths.access_csv(year), sep=";", dtype=str, encoding="latin-1", keep_default_na=False)
    assert d.shape[1] == 7, d.columns
    d.columns = ["period_raw", "make_raw", "model_raw", "model_year", "muni_name", "region_code", "fsa"]
    fix = {v: _repair(v) for v in d["muni_name"].unique()}
    d["muni_name"] = d["muni_name"].map(fix)
    for c in ("make_raw", "model_raw", "muni_name", "fsa"):
        d[c] = d[c].str.strip()
    con.register("acc", d)
    con.execute(f"""
        COPY (
          SELECT {year} AS year, 'access' AS source, period_raw,
                 CAST(NULL AS VARCHAR) AS vclass, CAST(NULL AS VARCHAR) AS vtype,
                 nullif(make_raw,'') AS make_raw, nullif(model_raw,'') AS model_raw,
                 TRY_CAST(model_year AS INTEGER) AS model_year,
                 CAST(NULL AS INTEGER) AS net_mass_kg, CAST(NULL AS VARCHAR) AS cylinders,
                 CAST(NULL AS INTEGER) AS displacement_cc, CAST(NULL AS INTEGER) AS max_axles,
                 CAST(NULL AS VARCHAR) AS colour, CAST(NULL AS VARCHAR) AS fuel,
                 TRY_CAST(region_code AS INTEGER) AS region_code, CAST(NULL AS VARCHAR) AS region_name,
                 CAST(NULL AS VARCHAR) AS mrc_code, CAST(NULL AS VARCHAR) AS mrc_name,
                 CAST(NULL AS VARCHAR) AS muni_code, nullif(muni_name,'') AS muni_name,
                 nullif(upper(fsa),'') AS fsa
          FROM acc
        ) TO '{paths.parquet(year)}' (FORMAT parquet, COMPRESSION zstd)""")
    con.unregister("acc")


def main():
    force = "--force" in sys.argv
    paths.PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    manifest = []
    for year in list(paths.OPEN_YEARS) + list(paths.ACCESS_YEARS):
        is_open = year in paths.OPEN_YEARS
        src = paths.open_csv(year) if is_open else paths.access_csv(year)
        if force or not paths.parquet(year).exists():
            (ingest_open if is_open else ingest_access)(con, year)
            print("written", paths.parquet(year).name, flush=True)
        manifest.append({
            "year": year, "source": "open" if is_open else "access", "file": src.name,
            "bytes": src.stat().st_size, "sha256": sha256(src),
            "origin": paths.OPEN_URL.format(year=year) if is_open
            else "SAAQ, access-to-information file 03.06.34729",
        })
        print("hashed", src.name, flush=True)
    with open(paths.TABLES / "raw_manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0]))
        w.writeheader()
        w.writerows(manifest)

    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')")
    fill = ", ".join(f"round(100.0*count({c})/count(*),2) AS pct_{c}" for c in SCHEMA[3:])
    summary = con.execute(
        f"SELECT year, source, count(*) AS n_rows, count(DISTINCT period_raw) AS period_values, {fill} "
        "FROM v GROUP BY ALL ORDER BY year").df()
    summary.to_csv(paths.TABLES / "ingest_summary.csv", index=False)
    print(summary[["year", "source", "n_rows", "pct_vtype", "pct_fuel", "pct_net_mass_kg", "pct_model_year",
                   "pct_muni_code", "pct_fsa"]].to_string(index=False))

    failed = 0
    rows = []
    for label, where, want in EXPECTED:
        got = con.execute(f"SELECT count(*) FROM v WHERE {where}").fetchone()[0]
        rows.append({"check": label, "expected": want, "found": got, "ok": got == want})
        failed += got != want
        print(("ok   " if got == want else "FAIL ") + f"{label}: {got:,} (expected {want:,})")
    pd.DataFrame(rows).to_csv(paths.TABLES / "ingest_checks.csv", index=False)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
