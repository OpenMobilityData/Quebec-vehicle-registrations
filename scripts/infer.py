"""Stage 3: vehicle type and fuel for 2023-2024, inferred from make, model and
model year, with the error measured on years where the truth is published.

Method. The curated open data give, for each make, model and model year, how
many vehicles are of each type (TYP_VEH_CATEG_USA) and each fuel (TYP_CARBU,
from 2017). A vehicle of the 2023-2024 release is not assigned one value: it
contributes to each value in the proportions observed for its key in the
reference years (the three most recent published years). The key used is the
most specific one found in the reference:

  1  make, model, model year
  2  make, model, model years of the last three reference years
  3  make, model (all model years)
  4  make, model year
  5  make
  6  none: the vehicle stays unassigned and is reported as such

Measurement. For each published year T and each lead (1 or 2 years, the two
leads of 2023 and 2024 from 2022), year T is stripped to the columns of the
release, inferred from the years up to T minus the lead, and compared with
what the SAAQ published for T.

Outputs (derived/tables/):
  holdout_summary.csv     true and inferred counts, Québec and Montréal, by year and lead
  holdout_levels.csv      share of vehicles and probability given to the true value, by level
  holdout_municipal.csv   error on automobiles and light trucks by municipality size
  type_by_municipality.csv   2011-2024, released (2011-2022) and inferred (2023-2024)
  fuel_by_municipality.csv   2017-2024, the same
  type_by_fsa.csv, fuel_by_fsa.csv   2023-2024, inferred
  type_by_model_year.csv  Québec and Montréal, by model year (for the cohort tables)
  inference_levels.csv    share of the 2023-2024 vehicles at each level
  fuel_inferred_before_2017.csv, holdout_backward.csv   fuel for 2011-2016 inferred backward from 2017-2019, and that step tested
Run:  ~/.venvs/omd/bin/python scripts/infer.py
"""
import duckdb
import pandas as pd

import paths

TARGETS = {"vtype": 2011, "fuel": 2017}          # first year the column is published
LEVELS = {
    1: ("make, model, model year", ["make", "model", "model_year"], ""),
    2: ("make, model, recent model years", ["make", "model"], "AND model_year >= {last} - 2"),
    3: ("make, model", ["make", "model"], ""),
    4: ("make, model year", ["make", "model_year"], ""),
    5: ("make", ["make"], ""),
}
PARENT = paths.PARQUET_DIR.parent


def setup(con):
    con.execute(f"CREATE VIEW v AS SELECT * FROM read_parquet('{paths.PARQUET_DIR}/vehicles_*.parquet')")
    con.execute(f"CREATE VIEW vmap AS SELECT * FROM read_parquet('{PARENT}/vocabulary_map.parquet')")
    con.execute(f"CREATE VIEW mmap AS SELECT * FROM read_parquet('{PARENT}/municipality_match.parquet')")
    # one table of cells, both sources, in the curated vocabulary
    con.execute("""
        CREATE TABLE cells AS
        SELECT year, 'open' AS source, muni_code, CAST(NULL AS VARCHAR) AS fsa,
               upper(make_raw) AS make, upper(coalesce(model_raw,'')) AS model, model_year,
               vtype, fuel, count(*) AS n
        FROM v WHERE source='open' GROUP BY ALL
        UNION ALL
        SELECT a.year, 'access', m.muni_code, a.fsa, vm.make, vm.model, a.model_year,
               NULL, NULL, count(*)
        FROM v a
        LEFT JOIN vmap vm ON vm.make_raw = upper(coalesce(a.make_raw,'')) AND vm.model_raw = upper(coalesce(a.model_raw,''))
        LEFT JOIN mmap m ON m.muni_name IS NOT DISTINCT FROM a.muni_name AND m.region_code IS NOT DISTINCT FROM a.region_code
        WHERE a.source='access' GROUP BY ALL""")


def infer(con, target, year, ref_years, out, backward=False):
    """Expected counts of `target` for the cells of `year`, from the reference years. Result table `out`:
    year, muni_code, fsa, level, value, n (expected), plus rows with value NULL for unassigned vehicles."""
    last = max(ref_years)
    yrs = ",".join(map(str, ref_years))
    con.execute(f"CREATE OR REPLACE TEMP TABLE ref AS SELECT make, model, model_year, {target} AS value, sum(n) n "
                f"FROM cells WHERE source='open' AND year IN ({yrs}) AND {target} IS NOT NULL AND make IS NOT NULL GROUP BY ALL")
    con.execute(f"CREATE OR REPLACE TEMP TABLE tgt AS SELECT row_number() OVER () AS id, muni_code, fsa, make, model, "
                f"model_year, {target if year <= 2022 else 'NULL'} AS truth, n FROM cells WHERE year={year}")
    con.execute("CREATE OR REPLACE TEMP TABLE todo AS SELECT * FROM tgt")
    con.execute(f"CREATE OR REPLACE TABLE {out} (id BIGINT, muni_code VARCHAR, fsa VARCHAR, model_year INTEGER, truth VARCHAR, "
                "level INTEGER, value VARCHAR, n DOUBLE)")
    for lvl, (_, key, cond) in LEVELS.items():
        k = ", ".join(key)
        on = " AND ".join(f"t.{c} = r.{c}" for c in key)
        if backward and lvl == 2:          # going back in time: the model years that existed by the target year
            cond = f"AND model_year <= {year} + 1"
        con.execute(f"CREATE OR REPLACE TEMP TABLE r AS SELECT {k}, value, sum(n) n, "
                    f"sum(sum(n)) OVER (PARTITION BY {k}) tot FROM ref WHERE true {cond.format(last=last)} GROUP BY {k}, value")
        con.execute(f"INSERT INTO {out} SELECT t.id, t.muni_code, t.fsa, t.model_year, t.truth, {lvl}, r.value, t.n * r.n / r.tot "
                    f"FROM todo t JOIN r ON {on}")
        con.execute(f"CREATE OR REPLACE TEMP TABLE todo AS SELECT t.* FROM todo t WHERE NOT EXISTS "
                    f"(SELECT 1 FROM {out} o WHERE o.id = t.id AND o.level = {lvl})")
    con.execute(f"INSERT INTO {out} SELECT id, muni_code, fsa, model_year, truth, 6, NULL, n FROM todo")


def holdout(con):
    summ, lev, mun = [], [], []
    for target, first in TARGETS.items():
        for lead in (1, 2):
            for T in range(first + lead, 2023):
                ref_years = [y for y in range(T - lead - 2, T - lead + 1) if y >= first]
                infer(con, target, T, ref_years, "h")
                tag = dict(target=target, lead=lead, year=T, reference=f"{min(ref_years)}-{max(ref_years)}")
                for scope, cond in (("Québec", "true"), ("Montréal", "muni_code='66023'")):
                    true = con.execute(f"SELECT truth AS value, sum(n) FROM tgt WHERE {cond} GROUP BY 1").df()
                    true.columns = ["value", "true"]
                    pred = con.execute(f"SELECT value, sum(n) AS inferred FROM h WHERE {cond} AND level < 6 GROUP BY 1").df()
                    una = con.execute(f"SELECT coalesce(sum(n),0) FROM h WHERE {cond} AND level = 6").fetchone()[0]
                    j = true.merge(pred, on="value", how="outer").fillna({"true": 0, "inferred": 0})
                    j = j[j.value.notna() & (j["true"] > 0)].sort_values("true", ascending=False).head(8)
                    for r in j.itertuples():
                        summ.append({**tag, "scope": scope, "value": r.value, "true": int(r.true),
                                     "inferred": round(r.inferred), "unassigned_all_values": int(una),
                                     "pct_error": round(100 * (r.inferred - r.true) / r.true, 2)})
                d = con.execute("SELECT level, sum(n) vehicles, sum(n) FILTER (WHERE value IS NOT DISTINCT FROM truth) AS on_truth "
                                "FROM h WHERE truth IS NOT NULL GROUP BY 1 ORDER BY 1").df()
                tot = d.vehicles.sum()
                for r in d.itertuples():
                    lev.append({**tag, "level": r.level, "key": LEVELS.get(r.level, ("none",))[0],
                                "pct_vehicles": round(100 * r.vehicles / tot, 3),
                                "pct_probability_on_true_value": round(100 * (r.on_truth or 0) / r.vehicles, 2)})
                if target == "vtype":
                    m = con.execute("""
                        WITH t AS (SELECT muni_code, sum(n) FILTER (WHERE truth='AU') au, sum(n) tot FROM tgt
                                   WHERE muni_code IS NOT NULL GROUP BY 1),
                             p AS (SELECT muni_code, sum(n) FILTER (WHERE value='AU') au FROM h GROUP BY 1)
                        SELECT CASE WHEN t.tot < 1000 THEN '1 under 1,000' WHEN t.tot < 10000 THEN '2 1,000-9,999'
                                    WHEN t.tot < 100000 THEN '3 10,000-99,999' ELSE '4 100,000 and more' END AS size,
                               count(*) municipalities,
                               median(abs(p.au - t.au) / t.au) * 100 AS median_abs_pct,
                               quantile_cont(abs(p.au - t.au) / t.au, 0.9) * 100 AS p90_abs_pct,
                               max(abs(p.au - t.au) / t.au) * 100 AS max_abs_pct,
                               median((p.au - t.au) / t.au) * 100 AS median_signed_pct
                        FROM t JOIN p USING (muni_code) WHERE t.au > 0 GROUP BY 1 ORDER BY 1""").df()
                    for r in m.itertuples():
                        mun.append({**tag, "vehicles_registered": r.size[2:], "municipalities": r.municipalities,
                                    "median_abs_pct_error": round(r.median_abs_pct, 2),
                                    "p90_abs_pct_error": round(r.p90_abs_pct, 2), "max_abs_pct_error": round(r.max_abs_pct, 2),
                                    "median_signed_pct_error": round(r.median_signed_pct, 2)})
                print("holdout", target, "lead", lead, T, flush=True)
    pd.DataFrame(summ).to_csv(paths.TABLES / "holdout_summary.csv", index=False)
    pd.DataFrame(lev).to_csv(paths.TABLES / "holdout_levels.csv", index=False)
    pd.DataFrame(mun).to_csv(paths.TABLES / "holdout_municipal.csv", index=False)
    return pd.DataFrame(summ), pd.DataFrame(lev), pd.DataFrame(mun)


def final(con):
    lev = []
    for target, first in TARGETS.items():
        parts = [f"SELECT year, muni_code, {target} AS value, sum(n) AS n, 'released' AS basis FROM cells "
                 f"WHERE source='open' AND year >= {first} GROUP BY ALL"]
        fsa_parts = []
        for T in paths.ACCESS_YEARS:
            infer(con, target, T, [2020, 2021, 2022], f"inf_{target}_{T}")
            parts.append(f"SELECT {T}, muni_code, value, sum(n), 'inferred' FROM inf_{target}_{T} GROUP BY ALL")
            fsa_parts.append(f"SELECT {T} AS year, fsa, value, round(sum(n), 1) AS n FROM inf_{target}_{T} GROUP BY ALL")
            d = con.execute(f"SELECT level, sum(n) FROM inf_{target}_{T} GROUP BY 1 ORDER BY 1").fetchall()
            tot = sum(x[1] for x in d)
            lev += [{"target": target, "year": T, "level": l, "key": LEVELS.get(l, ("none (unassigned)",))[0],
                     "vehicles": round(n), "pct": round(100 * n / tot, 3)} for l, n in d]
        con.execute(f"COPY (SELECT year, muni_code, value AS {target}, round(n, 1) AS n, basis FROM ({' UNION ALL '.join(parts)}) "
                    f"ORDER BY year, muni_code, value) TO '{paths.TABLES}/{'type' if target == 'vtype' else 'fuel'}_by_municipality.csv' (HEADER)")
        con.execute(f"COPY (SELECT year, fsa, value AS {target}, n FROM ({' UNION ALL '.join(fsa_parts)}) "
                    f"ORDER BY year, fsa, value) TO '{paths.TABLES}/{'type' if target == 'vtype' else 'fuel'}_by_fsa.csv' (HEADER)")
    # type by model year, Québec and the municipality of Montréal (for the cohort tables)
    parts = ["SELECT year, 'Québec' AS scope, model_year, vtype, sum(n) AS n, 'released' AS basis FROM cells WHERE source='open' GROUP BY ALL",
             "SELECT year, 'Montréal', model_year, vtype, sum(n), 'released' FROM cells WHERE source='open' AND muni_code='66023' GROUP BY ALL"]
    for T in paths.ACCESS_YEARS:
        parts.append(f"SELECT {T}, 'Québec', model_year, value, sum(n), 'inferred' FROM inf_vtype_{T} GROUP BY ALL")
        parts.append(f"SELECT {T}, 'Montréal', model_year, value, sum(n), 'inferred' FROM inf_vtype_{T} WHERE muni_code='66023' GROUP BY ALL")
    con.execute(f"COPY (SELECT year, scope, model_year, vtype, round(n, 1) AS n, basis FROM ({' UNION ALL '.join(parts)}) "
                f"WHERE model_year BETWEEN 1950 AND 2026 ORDER BY ALL) TO '{paths.TABLES}/type_by_model_year.csv' (HEADER)")
    pd.DataFrame(lev).to_csv(paths.TABLES / "inference_levels.csv", index=False)
    return pd.DataFrame(lev)


def backward(con):
    """Fuel before 2017, when the column did not exist: inferred from the reference years 2017-2019, and the same
    backward step tested on 2017-2019 from the three later years available."""
    rows = []
    for T, ref in ((2017, [2018, 2019, 2020]), (2017, [2019, 2020, 2021]), (2017, [2020, 2021, 2022]),
                   (2018, [2019, 2020, 2021]), (2018, [2020, 2021, 2022]), (2019, [2020, 2021, 2022])):
        infer(con, "fuel", T, ref, "hb", backward=True)
        for scope, cond in (("Québec", "true"), ("Montréal", "muni_code='66023'")):
            true = dict(con.execute(f"SELECT truth, sum(n) FROM tgt WHERE {cond} GROUP BY 1").fetchall())
            pred = dict(con.execute(f"SELECT value, sum(n) FROM hb WHERE {cond} AND level < 6 GROUP BY 1").fetchall())
            for v in ("E", "D", "H", "L", "W"):
                rows.append({"year": T, "reference": f"{ref[0]}-{ref[-1]}", "years_back": ref[0] - T, "scope": scope, "fuel": v,
                             "true": int(true.get(v, 0)), "inferred": round(pred.get(v, 0)),
                             "pct_error": round(100 * (pred.get(v, 0) - true[v]) / true[v], 2)})
    hb = pd.DataFrame(rows); hb.to_csv(paths.TABLES / "holdout_backward.csv", index=False)
    parts = []
    for T in range(2011, 2017):
        infer(con, "fuel", T, [2017, 2018, 2019], f"bw_{T}", backward=True)
        parts.append(f"SELECT {T} AS year, 'Québec' AS scope, value AS fuel, sum(n) AS n FROM bw_{T} GROUP BY ALL")
        parts.append(f"SELECT {T}, 'Montréal', value, sum(n) FROM bw_{T} WHERE muni_code='66023' GROUP BY ALL")
    con.execute(f"COPY (SELECT year, scope, fuel, round(n, 1) AS n, 'inferred' AS basis FROM ({' UNION ALL '.join(parts)}) ORDER BY ALL) "
                f"TO '{paths.TABLES}/fuel_inferred_before_2017.csv' (HEADER)")
    return hb


def main():
    con = duckdb.connect()
    con.execute("SET threads=16")
    setup(con)
    s, l, m = holdout(con)
    pd.set_option("display.width", 220)
    print(s[(s.year == 2022) & s.value.isin(["AU", "E", "L", "H", "W", "D"])].to_string(index=False))
    print(m[m.year == 2022].to_string(index=False))
    print(l[l.year == 2022].to_string(index=False))
    print(final(con).to_string(index=False))
    hb = backward(con)
    print(hb[hb.fuel.isin(["L", "W", "H"]) & (hb.scope == "Québec")].to_string(index=False))
    print(pd.read_csv(paths.TABLES / "fuel_inferred_before_2017.csv").query("scope == 'Québec' and fuel in ['L', 'W', 'H']").pivot(index="year", columns="fuel", values="n").round(0).to_string())


if __name__ == "__main__":
    main()
